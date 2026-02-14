from httpx import AsyncClient, Response
from typing import List, Optional
from harmony.app.schemas import ChatMessage, ChatHistoryResponse
from .data_gen import generate_user_data

class AppClient:
    """
    Wraps raw HTTP calls.
    Updated to support JWT auth and /me endpoints.
    """
    def __init__(self, client: AsyncClient, api_prefix: str = "/api/v1"):
        self.client = client
        self.prefix = api_prefix

    async def login(self, email: str, password: str) -> str:
        """
        Exchanges credentials for a JWT access token.
        """
        form_data = {
            "username": email, 
            "password": password
        }
        res = await self.client.post(f"{self.prefix}/auth/token", data=form_data)
        res.raise_for_status()
        return res.json()["access_token"]

    def _headers(self, token: Optional[str]) -> dict:
        return {"Authorization": f"Bearer {token}"} if token else {}

    async def create_user(self, username: str, email: str, password: str) -> str:
        payload = {"username": username, "email": email, "password": password}
        res = await self.client.post(f"{self.prefix}/users/", json=payload)
        res.raise_for_status()
        return res.json()["user_id"]
    
    async def delete_user_me(self, token: str):
        res = await self.client.delete(
            f"{self.prefix}/users/me",
            headers=self._headers(token)
        )
        res.raise_for_status()

    async def create_chat(self, user_ids: List[str], token: str) -> str:
        payload = {"user_id_list": user_ids}
        res = await self.client.post(
            f"{self.prefix}/chats/", 
            json=payload,
            headers=self._headers(token)
        )
        res.raise_for_status()
        return res.json()["chat_id"]

    async def send_message(self, chat_id: str, content: str, token: str) -> ChatMessage:
        payload = {"content": content}
        res = await self.client.post(
            f"{self.prefix}/chats/{chat_id}", 
            json=payload,
            headers=self._headers(token)
        )
        res.raise_for_status()
        return ChatMessage.model_validate(res.json())

    async def get_chat_history(self, chat_id: str, token: str) -> ChatHistoryResponse:
        res = await self.client.get(
            f"{self.prefix}/chats/{chat_id}", 
            headers=self._headers(token)
        )
        res.raise_for_status()
        return ChatHistoryResponse(**res.json())

    async def get_my_chats(self, token: str) -> List[str]:
        res = await self.client.get(
            f"{self.prefix}/users/me/chats",
            headers=self._headers(token)
        )
        res.raise_for_status()
        return res.json()["chat_id_list"]
    
    async def delete_chat(self, chat_id: str, token: str):
        res = await self.client.delete(
            f"{self.prefix}/chats/{chat_id}", 
            headers=self._headers(token)
        )
        res.raise_for_status()

class SimulationActor:
    """
    Represents a specific user in the test environment.
    Now holds state (token) to authenticate its own requests.
    """
    def __init__(self, user_id: str, username: str, email: str, password: str, client: AppClient):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password = password
        self.client = client
        self.token: Optional[str] = None

    async def login(self):
        self.token = await self.client.login(self.email, self.password)

    async def create_chat_with(self, other_actors: List['SimulationActor']) -> str:
        ids = [a.user_id for a in other_actors]
        chat_id = await self.client.create_chat(ids, token=self.token)
        return chat_id

    async def send_message(self, chat_id: str, content: str):
        return await self.client.send_message(chat_id, content, token=self.token)

    async def get_history(self, chat_id: str):
        resp = await self.client.get_chat_history(chat_id, token=self.token)
        return resp.messages

    async def get_my_chats(self):
        return await self.client.get_my_chats(token=self.token)
    
    async def delete_chat(self, chat_id: str):
        await self.client.delete_chat(chat_id, token=self.token)

    async def delete_self(self):
        await self.client.delete_user_me(token=self.token)

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
