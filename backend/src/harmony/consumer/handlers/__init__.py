from ..router import EventRouter
from .chat import router as chat_router
from .user import router as user_router

main_router = EventRouter()
main_router.include_router(chat_router)
main_router.include_router(user_router)