from fastapi import APIRouter, Depends
from harmony.app.schemas import CentrifugoSubscribeRequest
from harmony.app.schemas.centrifugo import CentrifugoConnectRequest
from harmony.app.services import PubSubService

from .dependencies import get_pubsub_service, get_user_from_cookie

router = APIRouter()

@router.post("/subscribe")
async def subscribe_proxy(
    req: CentrifugoSubscribeRequest,
    pubsub_service: PubSubService = Depends(get_pubsub_service),
):
    return await pubsub_service.authorize_subscription(req)

@router.post("/connect")
async def connect_proxy(
    req: CentrifugoConnectRequest,
    user_id: str | None = Depends(get_user_from_cookie),
    pubsub_service: PubSubService = Depends(get_pubsub_service),
):
    return await pubsub_service.authorize_connection(user_id)