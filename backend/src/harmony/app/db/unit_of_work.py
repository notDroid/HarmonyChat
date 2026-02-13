# simple_discord/app/db/unit_of_work.py
from typing import List, Any
from botocore.exceptions import ClientError
from harmony.app.core import active_writer_var

class UnitOfWork:
    def __init__(self, client):
        self.client = client
        self.operations: List[dict] = []
        self._token = None

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
        tx_writer = TransactionWriter(self)
        self._token = active_writer_var.set(tx_writer)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            active_writer_var.reset(self._token)
        self.operations.clear()

class UnitOfWorkFactory:
    def __init__(self, client):
        self.client = client

    def __call__(self):
        return UnitOfWork(self.client)
    
class TransactionWriter:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def put_item(self, TableName: str, Item: dict, **kwargs):
        op = {
            "Put": {
                "TableName": TableName,
                "Item": Item
                **kwargs
            }
        }            
        self.uow.add_operation(op)

    async def put_batch(self, TableName: str, Items: List[dict], **kwargs):
        for item in Items:
            self.uow.add_operation({
                "Put": {
                    "TableName": TableName,
                    "Item": item,
                    **kwargs
                }
            })

    async def delete_item(self, TableName: str, Key: dict, **kwargs):
        self.uow.add_operation({
            "Delete": {
                "TableName": TableName,
                "Key": Key,
                **kwargs
            }
        })

    async def delete_batch(self, TableName: str, Keys: List[dict], **kwargs):
        for key in Keys:
            self.uow.add_operation({
                "Delete": {
                    "TableName": TableName,
                    "Key": key,
                    **kwargs
                }
            })

    async def require_condition(self, TableName: str, Key: dict, ConditionExpression: str, **kwargs):
        self.uow.add_operation({
            "ConditionCheck": {
                "TableName": TableName,
                "Key": Key,
                "ConditionExpression": ConditionExpression,
                **kwargs
            }
        })