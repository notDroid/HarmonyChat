import uuid
from ulid import ULID
from datetime import datetime, timezone
from fastapi import HTTPException, status
import structlog

from harmony.app.schemas import ChatMessage
from harmony.app.repositories import ChatHistoryRepository

from ..chat import ChatQueries
from harmony.app.streams import RedisPubSubManager

logger = structlog.get_logger(__name__)

class MessageCommands:
    def __init__(
        self, 
        chat_history_repository: ChatHistoryRepository,
        chat_queries: ChatQueries,
        event_publisher: RedisPubSubManager
    ):
        self.chat_history_repo = chat_history_repository
        self.chat_queries = chat_queries
        self.event_publisher = event_publisher

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

        # 3. Persist to DynamoDB
        try:
            await self.chat_history_repo.create_message(msg)
            
            # 4. Publish to Redis Pub/Sub
            await self.event_publisher.publish(str(chat_id), msg.model_dump(mode="json"))
            
            logger.info("message_sent", chat_id=str(chat_id), user_id=str(user_id), message_id=ulid_str)
            return msg
            
        except Exception as e:
            logger.exception("message_send_failed", chat_id=str(chat_id), user_id=str(user_id))
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to send message.")
        
    async def background_delete_chat_history(self, chat_id: uuid.UUID):
        """
        Deletes all messages for a chat. Should be called in the background after a chat is deleted to prevent API latency.
        Note: This is a best-effort operation. If it fails, it will be retried on the next message send or chat access for that chat.
        """
        try:
            await self.chat_history_repo.delete_chat_history(chat_id)
            logger.info("chat_history_deleted", chat_id=str(chat_id))
        except Exception as e:
            logger.exception("chat_history_delete_failed", chat_id=str(chat_id))