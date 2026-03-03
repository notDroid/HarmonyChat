import uuid
import asyncio
from ulid import ULID
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException, status
import structlog

from harmony.app.core.interfaces import TaskQueue
from harmony.app.schemas import ChatMessage, ChatMessageResponse
from harmony.app.repositories import ChatHistoryRepository

from ..chat import ChatQueries
from ..user import UserQueries
from ..pubsub import PubSubService

logger = structlog.get_logger(__name__)

class MessageCommands:
    def __init__(
        self, 
        chat_history_repository: ChatHistoryRepository,
        chat_queries: ChatQueries,
        user_queries: UserQueries,
        event_publisher: PubSubService,
        task_queue: Optional[TaskQueue] = None
    ):
        self.chat_history_repo = chat_history_repository
        self.chat_queries = chat_queries
        self.user_queries = user_queries
        self.event_publisher = event_publisher
        self.task_queue = task_queue

    async def send_message(self, chat_id: uuid.UUID, user_id: uuid.UUID, content: str, client_uuid: str | None = None) -> ChatMessage:
        # 1. Authorize
        is_member = await self.chat_queries.check_user_in_chat(user_id=user_id, chat_id=chat_id)
        if not is_member:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "User is not a member of this chat.")

        # 2. Construct Message Data
        ulid_val = ULID()
        ulid_str = str(ulid_val)
        timestamp = datetime.fromtimestamp(ulid_val.timestamp, timezone.utc).isoformat()

        msg = ChatMessage(
            chat_id=str(chat_id),
            ulid=ulid_str,
            timestamp=timestamp,
            user_id=str(user_id),
            content=content,
            client_uuid=client_uuid
        )

        try:
            # 3. Persist to DynamoDB and fetch sender metadata concurrently
            task1 = self.chat_history_repo.create_message(msg)
            task2 = self.user_queries.get_user_by_id(user_id)
            results = await asyncio.gather(task1, task2)

            # 4. Fill in author metadata to publish message with complete info
            sender = results[1]
            msg_resp = ChatMessageResponse(
                **msg.model_dump(),
                author_metadata=sender.meta
            )
            
            # 5. Publish to Redis Pub/Sub
            self.task_queue.add_task(
                self.event_publisher.publish_message, 
                str(chat_id), 
                msg_resp.model_dump(mode="json")
            )
            
            logger.info("message_sent", chat_id=str(chat_id), user_id=str(user_id), message_id=ulid_str)
            return msg_resp
            
        except Exception as e:
            logger.exception("message_send_failed", chat_id=str(chat_id), user_id=str(user_id))
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to send message.")