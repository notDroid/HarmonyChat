import asyncio
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

serializer = TypeSerializer()
deserializer = TypeDeserializer()

def to_dynamo_json(python_dict: dict) -> dict:
    return {k: serializer.serialize(v) for k, v in python_dict.items()}

def from_dynamo_json(dynamo_dict: dict) -> dict:
    return {k: deserializer.deserialize(v) for k, v in dynamo_dict.items()}

async def process_batch(client, table_name, batch):
    response = await client.batch_write_item(
        RequestItems={
            table_name: batch
        }
    )

    unprocessed = response.get('UnprocessedItems', {})
    while unprocessed:
        await asyncio.sleep(0.5)
        response = await client.batch_write_item(RequestItems=unprocessed)
        unprocessed = response.get('UnprocessedItems', {})

async def batch_request(client, table_name, write_requests):
    chunk_size = 25
    batches = [write_requests[i:i + chunk_size] for i in range(0, len(write_requests), chunk_size)]

    tasks = []
    for batch in batches:
        tasks.append(process_batch(client, table_name, batch))
    
    await asyncio.gather(*tasks)