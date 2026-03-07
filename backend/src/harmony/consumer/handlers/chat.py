import uuid
import asyncio
from ..router import EventRouter
from ..context import ConsumerContext

router = EventRouter()

@router.register("Chat", "USERS_ADDED")
async def handle_users_added(aggregate_id: str, payload: dict, ctx: ConsumerContext):
    chat_id = uuid.UUID(aggregate_id)
    user_ids = [uuid.UUID(uid) for uid in payload.get("user_id_list", [])]
    await ctx.chat_handler.on_users_added_to_chat(chat_id, user_ids)

@router.register("Chat", "USER_LEFT")
async def handle_user_left(aggregate_id: str, payload: dict, ctx: ConsumerContext):
    await ctx.chat_handler.on_user_left_chat(uuid.UUID(aggregate_id), uuid.UUID(payload.get("user_id")))

@router.register("Chat", "CHAT_DELETED")
async def handle_chat_deleted(aggregate_id: str, payload: dict, ctx: ConsumerContext):
    chat_id = uuid.UUID(aggregate_id)
    await asyncio.gather(
        ctx.chat_handler.on_chat_deleted(chat_id),
        ctx.msg_handler.on_chat_deleted(chat_id)
    )