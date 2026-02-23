from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from harmony.app.services import StreamService

from .dependencies import get_stream_service

router = APIRouter()

@router.websocket("/{chat_id}")
async def chat_websocket(
    websocket: WebSocket, 
    chat_id: str,
    stream_service: StreamService = Depends(get_stream_service),
):
    stream_service.handle_chat_connection(websocket=websocket, chat_id=chat_id)