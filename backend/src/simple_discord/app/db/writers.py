from typing import Protocol, List, Any
from .utils import batch_request

class Delegator:
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)

    def __getattr__(self, name):
        return getattr(self._obj, name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            setattr(self._obj, name, value)

    def __dir__(self):
        return sorted(set(dir(type(self))))

class DirectWriter(Delegator):
    def __init__(self, client):
        super().__init__(client)
        self.client = client

    async def put_batch(self, TableName: str, Items: List[dict]):
        await batch_request(self.client, TableName, [{"PutRequest": {"Item": item}} for item in Items])

    async def delete_batch(self, TableName: str, Keys: List[dict]):
        await batch_request(self.client, TableName, [{"DeleteRequest": {"Key": key}} for key in Keys])