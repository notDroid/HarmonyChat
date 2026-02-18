from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from harmony.app.services import WebSocketManager, RedisPubSubManager

router = APIRouter()

# Dependency to get managers from app state (tight coupling for simplicity)
def get_managers(websocket: WebSocket):
    return websocket.app.state.ws_manager, websocket.app.state.redis_manager

@router.websocket("/{chat_id}")
async def chat_websocket(
    websocket: WebSocket, 
    chat_id: str,
    managers: tuple[WebSocketManager, RedisPubSubManager] = Depends(get_managers)
):
    ws_manager, redis_manager = managers
    
    # 1. Accept Connection (Layer 2)
    await ws_manager.connect(chat_id, websocket)
    
    # 2. Subscribe to Redis Channel (Layer 1)
    await redis_manager.subscribe_to_chat(chat_id)
    
    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
        # 3. Disconnect (Layer 2)
        ws_manager.disconnect(chat_id, websocket)
        
        # 4. Unsubscribe from Redis (Layer 1)
        await redis_manager.unsubscribe_from_chat(chat_id)