import uuid
from harmony.app.repositories import ChatHistoryRepository
import structlog

logger = structlog.get_logger(__name__)


class MessageEventHandler:
    def __init__(
            self,
            chat_history_repository: ChatHistoryRepository,
    ):
        self.chat_history_repo = chat_history_repository

    async def on_chat_deleted(self, chat_id: uuid.UUID):
        try:
            await self.chat_history_repo.delete_chat_history(chat_id)
            logger.info("chat_history_deleted", chat_id=str(chat_id))
        except Exception as e:
            logger.exception("chat_history_delete_failed", chat_id=str(chat_id))
            raise e