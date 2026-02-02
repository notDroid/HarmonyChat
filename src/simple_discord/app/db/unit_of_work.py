# simple_discord/app/db/unit_of_work.py
from typing import List, Any
from botocore.exceptions import ClientError

class UnitOfWork:
    def __init__(self, client):
        self.client = client
        self.operations: List[dict] = []

    def add_operation(self, operation: dict):
        self.operations.append(operation)

    async def commit(self):
        if not self.operations:
            return

        if len(self.operations) > 100:
            raise ValueError("Transaction exceeds DynamoDB limit of 100 operations")

        try:
            await self.client.transact_write_items(TransactItems=self.operations)
            self.operations.clear()
        except ClientError as e:
            raise e

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.operations.clear()

class UnitOfWorkFactory:
    def __init__(self, client):
        self.client = client

    def __call__(self):
        return UnitOfWork(self.client)