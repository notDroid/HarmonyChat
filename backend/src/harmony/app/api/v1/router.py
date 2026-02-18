from fastapi import APIRouter
from .chat import router as chat_router
from .user import router as user_router
from .auth import router as auth_router
from .websocket import router as ws_router

router = APIRouter()

router.include_router(chat_router, prefix="/chats", tags=["chat"])
router.include_router(user_router, prefix="/users", tags=["user"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(ws_router, prefix="/ws", tags=["streaming"])