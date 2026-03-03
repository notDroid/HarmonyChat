import uuid
from cent import AsyncClient, PublishRequest
from .chat import ChatQueries
from harmony.app.schemas import CentrifugoSubscribeRequest, CentrifugoSubscribeResponse, CentrifugoError

import structlog

logger = structlog.get_logger(__name__)

class PubSubService:
    """
    Service responsible for publishing messages to the message broker (Cent) for real-time events 
    and authorizing incoming subscriptions from cent.
    """
    def __init__(
        self,
        client: AsyncClient,
        chat_queries: ChatQueries
    ):
        self.client = client
        self.chat_queries = chat_queries

    async def publish_message(self, channel: str, message: dict):
        request = PublishRequest(channel=channel, data=message)
        await self.client.publish(request)
        logger.info("published_message", channel=channel)

    @staticmethod 
    def parse_request(req: CentrifugoSubscribeRequest):
        namespace, chat_id_str = req.channel.split(":", 1)
        chat_id = uuid.UUID(chat_id_str)
        user_id = uuid.UUID(req.user_id)
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
            logger.info("subscription_authorized", chat_id=chat_id, user_id=user_id)
            return CentrifugoSubscribeResponse(result={}) # Allow subscription
        else:
            logger.warning("subscription_denied_not_a_member", chat_id=chat_id, user_id=user_id)
            return CentrifugoSubscribeResponse(
                error=CentrifugoError(code=1001, message="Not a member of this chat")
            )