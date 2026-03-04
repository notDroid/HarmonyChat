import uuid
from .chat import ChatQueries
from harmony.app.schemas import (
    CentrifugoSubscribeRequest, CentrifugoSubscribeResponse, 
    CentrifugoConnectResponse, CentrifugoConnectResult,
    CentrifugoError
)

import structlog

logger = structlog.get_logger(__name__)

class PubSubService:
    """
    Service responsible for publishing messages to the message broker (Cent) for real-time events 
    and authorizing incoming subscriptions from cent.
    """
    def __init__(
        self,
        chat_queries: ChatQueries,
    ):
        self.chat_queries = chat_queries

    @staticmethod 
    def parse_request(req: CentrifugoSubscribeRequest):
        namespace, chat_id_str = req.channel.split(":", 1)
        chat_id = uuid.UUID(chat_id_str)
        user_id = uuid.UUID(req.user) if req.user else ""
        return namespace, chat_id, user_id
    
    async def authorize_subscription(self, req: CentrifugoSubscribeRequest) -> CentrifugoSubscribeResponse:
        try:
            _, chat_id, user_id = self.parse_request(req)
        except ValueError:
            logger.warning("invalid_channel_format", channel=req.channel)
            return CentrifugoSubscribeResponse(
                error=CentrifugoError(code=1000, message="Invalid channel format")
            )

        is_member = await self.chat_queries.check_user_in_chat(user_id=user_id, chat_id=chat_id)
        
        if is_member:
            logger.info("subscription_authorized", chat_id=str(chat_id), user_id=str(user_id))
            return CentrifugoSubscribeResponse(result={}) # Allow subscription
        else:
            logger.warning("subscription_denied_not_a_member", chat_id=str(chat_id), user_id=str(user_id))
            return CentrifugoSubscribeResponse(
                error=CentrifugoError(code=1001, message="Not a member of this chat")
            )
        
    async def authorize_connection(self, user_id: str | None) -> CentrifugoConnectResponse:
        if not user_id:
            logger.warning("ws_connection_denied_unauthenticated")
            return CentrifugoConnectResponse(
                error=CentrifugoError(code=1001, message="Authentication required")
            )
            
        logger.info("ws_connection_authorized", user_id=user_id)
        return CentrifugoConnectResponse(
            result=CentrifugoConnectResult(user=str(user_id))
        )