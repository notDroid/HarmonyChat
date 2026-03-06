import asyncio
from .router import EventRouter

def setup_router(chat_handler, user_handler, msg_handler) -> EventRouter:
    router = EventRouter()

    # -------------------------------- CHAT EVENTS ------------------------------- #
    @router.register("Chat", "USERS_ADDED")
    async def handle_users_added(aggregate_id: str, payload: dict):
        import uuid
        chat_id = uuid.UUID(aggregate_id)
        user_ids = [uuid.UUID(uid) for uid in payload.get("user_id_list", [])]
        await chat_handler.on_users_added_to_chat(chat_id, user_ids)

    @router.register("Chat", "USER_LEFT")
    async def handle_user_left(aggregate_id: str, payload: dict):
        import uuid
        await chat_handler.on_user_left_chat(uuid.UUID(aggregate_id), uuid.UUID(payload.get("user_id")))

    @router.register("Chat", "CHAT_DELETED")
    async def handle_chat_deleted(aggregate_id: str, payload: dict):
        import uuid
        chat_id = uuid.UUID(aggregate_id)
        asyncio.gather(
            chat_handler.on_chat_deleted(chat_id),
            msg_handler.on_chat_deleted(chat_id)
        )

    # -------------------------------- USER EVENTS ------------------------------- #
    @router.register("User", "TOMBSTONED")
    async def handle_user_deleted(aggregate_id: str, payload: dict):
        import uuid
        await user_handler.on_delete_user(uuid.UUID(aggregate_id))

    return router