import boto3
from fastapi import FastAPI
from pydantic import BaseModel
from boto3.dynamodb.conditions import Key
from contextlib import asynccontextmanager
from ulid import ULID

# --- 1. CONFIGURATION ---
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='fake',
    aws_secret_access_key='fake'
)


# --- 2. LIFESPAN (Startup/Shutdown Logic) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: Create Table ---
    try:
        dynamodb.create_table(
            TableName="ChatHistory",
            KeySchema=[
                {'AttributeName': 'chat_id', 'KeyType': 'HASH'},
                {'AttributeName': 'ulid', 'KeyType': 'RANGE'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'chat_id', 'AttributeType': 'S'},
                {'AttributeName': 'ulid', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )
        print(f"Table ChatHistory created.")
        dynamodb.create_table(
            TableName="UserData",
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )
        print(f"Table UserData created.")
        dynamodb.create_table(
            TableName="UserChat",
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'chat_id', 'KeyType': 'RANGE'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'chat_id', 'AttributeType': 'S'},
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )
        print(f"Table UserChat created.")
    except Exception as e:
        print(f"Table skipped (likely exists): {e}")
    
    yield  # The application runs here
    
    # --- Shutdown: Clean up if needed ---
    print("Shutting down...")

# --- 3. APP INITIALIZATION ---
app = FastAPI(lifespan=lifespan)

# --- 4. DATA MODEL ---
class SendMessageRequest(BaseModel):
    chat_id: str
    user_id: str
    content: str

class UserContext(BaseModel):
    username: str

class CreateUserRequest(BaseModel):
    context: UserContext

def verify_chat(chat_id: str) -> list[str]:
    table = dynamodb.Table("UserChat")
    response = table.query(
        KeyConditionExpression=Key('chat_id').eq(chat_id),
        AttributesToGet=['user_id']
    )
    return len(response.get('Items', [])) > 0

@app.post("/messages")
def send_message(msg: SendMessageRequest):
    table = dynamodb.Table("ChatHistory")

    item = {
        "chat_id": msg.chat_id,
        "user_id": msg.user_id,
        "content": msg.content,
    }
    ulid_val = ULID()
    item["ulid"] = str(ulid_val)
    item["timestamp"] = str(ulid_val.timestamp)

    try:
        table.put_item(Item=item, ConditionExpression="attribute_not_exists(SK)")
        return {"status": "Message saved"}
    except Exception as e:
        return {"status": "Failed to save message", "error": str(e)}

@app.get("/messages")
def get_chat_history(chat_id: str):
    table = dynamodb.Table("ChatHistory")
    response = table.query(
        KeyConditionExpression=Key('chat_id').eq(chat_id)
    )
    return response.get('Items', [])

@app.post("/users/")
def create_user(msg: CreateUserRequest):
    table = dynamodb.Table("UserData")
    user_id = str(ULID())
    item = {
        "user_id": user_id,
        "context": msg.context.model_dump()
    }
    try:
        table.put_item(Item=item, ConditionExpression="attribute_not_exists(PK)")
        return {"status": "User created", "user_id": user_id}
    except Exception as e:
        return {"status": "Failed to create user", "error": str(e)}
    

@app.get("/users")
def get_users():
    table = dynamodb.Table("UserData")
    all_items = []

    scan_kwargs = {'ProjectionExpression': 'user_id'}
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
            
        response = table.scan(**scan_kwargs)
        
        # Add the current page of results to our list
        all_items.extend(response.get('Items', []))
        
        # Check if there are more pages
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None

    return all_items