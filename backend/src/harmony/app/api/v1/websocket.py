# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
# from harmony.app.services import WebSocketManager, RedisPubSubManager
# from starlette.requests import Request

# router = APIRouter()

# def get_managers(request: Request):
#     return request.app.state.ws_manager, request.app.state.redis_manager

# @router.websocket("/{chat_id}")
# async def chat_websocket(
#     websocket: WebSocket, 
#     chat_id: str,
#     managers: tuple[WebSocketManager, RedisPubSubManager] = Depends(get_managers)
# ):
#     ws_manager, redis_manager = managers
    
#     # 1. Accept Connection (Layer 2)
#     await ws_manager.connect(chat_id, websocket)
    
#     # 2. Ensure we are subscribed to Redis for this chat (Layer 1)
#     await redis_manager.subscribe_to_chat(chat_id)
    
#     try:
#         while True:
#             # We just keep the connection open.
#             # If you want to support "Client -> Server" messages via WS, handle them here.
#             # For now, we just wait for disconnect.
#             await websocket.receive_text() 
#     except WebSocketDisconnect:
#         # 3. Cleanup Layer 2
#         ws_manager.disconnect(chat_id, websocket)
        
#         # 4. Cleanup Layer 1 (If no one else is listening locally)
#         await redis_manager.unsubscribe_from_chat(chat_id)