import boto3
from fastapi import FastAPI
from pydantic import BaseModel
from boto3.dynamodb.conditions import Key
from contextlib import asynccontextmanager

# --- 1. CONFIGURATION ---
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='us-east-1',
    aws_access_key_id='fake',
    aws_secret_access_key='fake'
)
TABLE_NAME = "ChatHistory"

# --- 2. LIFESPAN (Startup/Shutdown Logic) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup: Create Table ---
    try:
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'chat_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'chat_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )
        print(f"Table '{TABLE_NAME}' created.")
    except Exception as e:
        print(f"Table skipped (likely exists): {e}")
    
    yield  # The application runs here
    
    # --- Shutdown: Clean up if needed ---
    print("Shutting down...")

# --- 3. APP INITIALIZATION ---
app = FastAPI(lifespan=lifespan)

# --- 4. DATA MODEL ---
class Message(BaseModel):
    chat_id: str
    timestamp: int
    user_id: str
    content: str

# --- 5. ENDPOINTS ---
@app.post("/messages")
def send_message(msg: Message):
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item=msg.model_dump()) 
    return {"status": "Message saved"}

@app.get("/messages/{chat_id}")
def get_chat_history(chat_id: str):
    table = dynamodb.Table(TABLE_NAME)
    response = table.query(
        KeyConditionExpression=Key('chat_id').eq(chat_id)
    )
    return response.get('Items', [])