import asyncio
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer

serializer = TypeSerializer()
deserializer = TypeDeserializer()

def to_dynamo_json(python_dict: dict) -> dict:
    return {k: serializer.serialize(v) for k, v in python_dict.items()}

def from_dynamo_json(dynamo_dict: dict) -> dict:
    return {k: deserializer.deserialize(v) for k, v in dynamo_dict.items()}

async def process_batch(client, table_name, batch, max_retries: int = 0):
    response = await client.batch_write_item(
        RequestItems={
            table_name: batch
        }
    )

    unprocessed = response.get('UnprocessedItems', {})

    retries = 0
    while unprocessed and (max_retries == 0 or retries < max_retries):
        await asyncio.sleep(0.5 * (2 ** retries)) # Exponential backoff: 0.5s, 1s, 2s...
        response = await client.batch_write_item(RequestItems=unprocessed)
        unprocessed = response.get('UnprocessedItems', {})
        retries += 1

    if unprocessed:
        raise Exception(f"Failed to process batch after {retries} retries: {unprocessed}")

async def batch_request(client, table_name, write_requests, chunk_size: int = 25, max_retries: int = 0):
    batches = [write_requests[i:i + chunk_size] for i in range(0, len(write_requests), chunk_size)]

    tasks = []
    for batch in batches:
        tasks.append(process_batch(client, table_name, batch, max_retries=max_retries))
    
    await asyncio.gather(*tasks)


async def paginate_in_batches(client, query_kwargs: dict, batch_size: int = 25):
    paginator = client.get_paginator('query')
    batch = []
    
    async for page in paginator.paginate(**query_kwargs):
        for item in page.get("Items", []):
            batch.append(item)
            
            # Yield the chunk when it reaches the desired size
            if len(batch) == batch_size:
                yield batch
                batch = [] # Reset
                
    # Yield any remaining items
    if batch:
        yield batch