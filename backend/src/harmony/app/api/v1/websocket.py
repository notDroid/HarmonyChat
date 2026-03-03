from fastapi import APIRouter, Depends
from harmony.app.schemas import CentrifugoSubscribeRequest
from harmony.app.services import PubSubService

from .dependencies import get_pubsub_service

router = APIRouter()

@router.post("/subscribe")
async def subscribe_proxy(
    req: CentrifugoSubscribeRequest,
    pubsub_service: PubSubService = Depends(get_pubsub_service),
):
    return await pubsub_service.authorize_subscription(req)