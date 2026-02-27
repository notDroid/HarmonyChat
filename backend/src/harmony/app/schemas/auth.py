from pydantic import BaseModel

class Token(BaseModel):
    token: str
    token_type: str # one of "access_token" or "refresh_token" depending on context
    expiration: int # in seconds until token expires