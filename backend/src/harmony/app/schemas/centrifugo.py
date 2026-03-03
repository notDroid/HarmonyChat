from pydantic import BaseModel
from typing import Optional, Dict, Any


class CentrifugoSubscribeRequest(BaseModel):
    client: str
    transport: str
    protocol: str
    user_id: str
    channel: str

class CentrifugoError(BaseModel):
    code: int
    message: str

class CentrifugoSubscribeResponse(BaseModel):
    result: Optional[Dict[str, Any]] = None
    error: Optional[CentrifugoError] = None