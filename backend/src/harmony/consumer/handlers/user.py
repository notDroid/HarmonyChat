import uuid

from ..router import EventRouter
from ..context import ConsumerContext
from harmony.app.core import get_consumer_settings

router = EventRouter()
topic = get_consumer_settings().topics.user

@router.register("User", "TOMBSTONED")
async def handle_user_deleted(aggregate_id: str, payload: dict, ctx: ConsumerContext):
    await ctx.user_handler.on_delete_user(uuid.UUID(aggregate_id))