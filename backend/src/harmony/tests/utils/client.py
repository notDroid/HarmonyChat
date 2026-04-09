import uuid
import time
from httpx import AsyncClient, Response, HTTPStatusError
from typing import List, Optional, Any, Callable, Coroutine
from harmony.app.schemas import ChatMessage, ChatHistoryResponse
from .data_gen import generate_user_data, generate_chat_metadata

class AppClient:
    """
    Wraps raw HTTP calls.
    Updated to support JWT auth and /me endpoints.
    Now supports recording call latencies via an optional SafeMetrics instance.
    """
    def __init__(self, client: AsyncClient, api_prefix: str = "/api/v1"):
        self.client = client
        self.prefix = api_prefix
        self.metrics: Optional[Any] = None  # SafeMetrics

    async def _record_call(self, name: str, func: Callable[..., Coroutine[Any, Any, Response]], *args, **kwargs) -> Response:
        """Helper to measure latency and record it in metrics if available."""
        start = time.monotonic()
        error = False
        try:
            res = await func(*args, **kwargs)
            res.raise_for_status()
            return res
        except Exception:
            error = True
            raise
        finally:
            if self.metrics:
                latency = time.monotonic() - start
                # We use category="call" to distinguish from high-level actions
                await self.metrics.record(name, latency, error=error, category="call")

    async def login(self, email: str, password: str) -> str:
        """
        Exchanges credentials for a JWT access token.
        """
        form_data = {
            "username": email, 
            "password": password
        }
        res = await self._record_call("POST /auth/token", self.client.post, f"{self.prefix}/auth/token", data=form_data)
        return {token["token_type"]:token["token"] for token in res.json()}

    def _headers(self, token: Optional[str]) -> dict:
        return {"Authorization": f"Bearer {token}"} if token else {}

    async def create_user(self, username: str, email: str, password: str) -> uuid.UUID:
        payload = {"username": username, "email": email, "password": password}
        res = await self._record_call("POST /users", self.client.post, f"{self.prefix}/users/", json=payload)
        return uuid.UUID(res.json()["user_id"])
    
    async def delete_user_me(self, token: str):
        await self._record_call(
            "DELETE /users/me",
            self.client.delete,
            f"{self.prefix}/users/me",
            headers=self._headers(token)
        )

    async def create_chat(self, user_ids: List[uuid.UUID], token: str) -> uuid.UUID:
        payload = {
            "user_id_list": [str(uid) for uid in user_ids],
            **generate_chat_metadata()
        }
        res = await self._record_call(
            "POST /chats", 
            self.client.post,
            f"{self.prefix}/chats/", 
            json=payload,
            headers=self._headers(token)
        )
        return uuid.UUID(res.json()["chat_id"])

    async def send_message(self, chat_id: uuid.UUID, content: str, token: str) -> ChatMessage:
        payload = {"content": content}
        res = await self._record_call(
            "POST /chats/{id}", 
            self.client.post,
            f"{self.prefix}/chats/{chat_id}", 
            json=payload,
            headers=self._headers(token)
        )
        return ChatMessage.model_validate(res.json())

    async def get_chat_history(self, chat_id: uuid.UUID, token: str) -> ChatHistoryResponse:
        res = await self._record_call(
            "GET /chats/{id}", 
            self.client.get,
            f"{self.prefix}/chats/{chat_id}", 
            headers=self._headers(token)
        )
        return ChatHistoryResponse(**res.json())

    async def get_my_chats(self, token: str) -> List[uuid.UUID]:
        res = await self._record_call(
            "GET /users/me/chats",
            self.client.get,
            f"{self.prefix}/users/me/chats",
            headers=self._headers(token)
        )
        return [uuid.UUID(chat["chat_id"]) for chat in res.json()["chats"]]
    
    async def delete_chat(self, chat_id: uuid.UUID, token: str):
        await self._record_call(
            "DELETE /chats/{id}", 
            self.client.delete,
            f"{self.prefix}/chats/{chat_id}", 
            headers=self._headers(token)
        )

class SimulationActor:
    """
    Represents a specific user in the test environment.
    Now holds state (token) to authenticate its own requests.
    """
    def __init__(self, user_id: uuid.UUID, username: str, email: str, password: str, client: AppClient):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password = password
        self.client = client
        self.tokens: dict[str, str] = {}

    async def login(self):
        self.tokens = await self.client.login(self.email, self.password)

    async def create_chat_with(self, other_actors: List['SimulationActor']) -> uuid.UUID:
        ids = [a.user_id for a in other_actors]
        chat_id = await self.client.create_chat(ids, token=self.tokens["access_token"])
        return chat_id

    async def send_message(self, chat_id: uuid.UUID, content: str):
        return await self.client.send_message(chat_id, content, token=self.tokens["access_token"])

    async def get_history(self, chat_id: uuid.UUID):
        resp = await self.client.get_chat_history(chat_id, token=self.tokens["access_token"])
        return resp.messages

    async def get_my_chats(self):
        return await self.client.get_my_chats(token=self.tokens["access_token"])
    
    async def delete_chat(self, chat_id: uuid.UUID):
        await self.client.delete_chat(chat_id, token=self.tokens["access_token"])

    async def delete_self(self):
        await self.client.delete_user_me(token=self.tokens["access_token"])

async def spawn_actor(client: AppClient) -> SimulationActor:
    data = generate_user_data()
    uid = await client.create_user(**data)
    actor = SimulationActor(
        user_id=uid, 
        username=data['username'], 
        email=data['email'],
        password=data['password'],
        client=client
    )
    await actor.login()
    return actor
