import uuid
from fastapi import HTTPException, status
import structlog

from harmony.app.repositories import ChatHistoryRepository
from harmony.app.schemas import ChatMessage, ChatMessageResponse

from ..chat import ChatQueries
from ..user import UserQueries

logger = structlog.get_logger(__name__)

class MessageQueries:
    def __init__(
        self, 
        chat_history_repository: ChatHistoryRepository,
        chat_queries: ChatQueries,
        user_queries: UserQueries,
    ):
        self.chat_history_repo = chat_history_repository
        self.chat_queries = chat_queries
        self.user_queries = user_queries

    async def get_chat_history(self, user_id: uuid.UUID, chat_id: uuid.UUID, limit: int = 50, cursor: str | None = None) -> tuple[list[ChatMessageResponse], str | None]:
        # 1. Authorize
        is_member = await self.chat_queries.check_user_in_chat(user_id=user_id, chat_id=chat_id)
        if not is_member:
            logger.warning("history_access_denied", chat_id=chat_id, user_id=user_id)
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You must be a member of the chat to view history.")

        # 2. Fetch from DynamoDB
        try:
            messages, next_cursor = await self.chat_history_repo.get_chat_history(str(chat_id), limit, cursor)
            logger.debug("chat_history_retrieved", chat_id=str(chat_id), message_count=len(messages))
        except Exception as e:
            logger.exception("chat_history_fetch_failed", chat_id=str(chat_id))
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve chat history.")
        
        # 3. Get user metadata
        user_ids = list(set(m.user_id for m in messages))
        users_dict = await self.user_queries.get_users_dict(user_ids)
        
        # 4. Hydrate messages with user metadata
        hydrated_messages = []
        for msg in messages:
            user = users_dict.get(msg.user_id)
            hydrated_messages.append(
                ChatMessageResponse(
                    **msg.model_dump(),
                    author_metadata=user.meta if user else None
                )
            )
            
        return hydrated_messages, next_cursor