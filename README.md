# Harmony Chat
A fullstack discord/slack based chat app built with FastAPI (backend) and Next.js (frontend) for learning and demonstration purposes.

### Setup
Dependencies:

1. Conda
2. Taskfile
3. Docker and Docker Compose


Create and activate the conda environment:
```bash
conda env create -f environment.yaml
conda activate harmony
python -m pip install -e backend
```

### Run and Test Locally
To run the application locally using Docker Compose, use the following commands:
```bash
task build
task run-local
```

In another terminal, run tests:
```bash
task test
```

### TODO List
- [ ] Implement authentication and authorization
- [ ] Implement pub/sub model for real-time chat updates
- [ ] Implement request/response model for scrolling through chat history
- [ ] Implement caching layer for user-chat membership data to optimize presence checks
- [ ] Deploy app to AWS with terraform and set up CI/CD pipeline

# Implementation Documentation

## Database
We use DynamoDB as our primary database for storing chat history data and user/chat metadata.

### Reasoning
1. Dynamodb is suitable to store real time chat data due to its low latency and high scalability for small message record data model which doesn't require relational operations or complex transactions.
2. User/Chat metadata is relational but can be easily modeled in a denormalized way in DynamoDB with proper partition keys, secondary indexes, and careful use of transactions which makes the implementation simpler.
    - Although using a relational database is likely a better choice in a real production system.
    - We also use Redis as a caching layer for metadata to optimize presence checks which are very frequent and latency sensitive, we rely on cache invalidation to get fast eventual consistency.

### Schema Design
Because of these 2 different models we reason about the data access by whether we are accessing user/chat metadata or chat history data and use the appropriate access patterns for each:
1. For user/chat metadata, we use 3 tables: Users, Chats, and UserChats. The Users table stores user information, the Chats table stores chat information, and the UserChats table models the many-to-many relationship between users and chats.
2. For chat history data, we use a single ChatMessages table with a partition key of chat_id and a sort key of ulid. 
    - The ULID allows us to efficiently query for messages in a chat because it encodes a timestamp and ensures lexicographical ordering.

infra/config/tables.json:
```json
{
    "ChatHistory": {
        "TableName": "ChatHistory",
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "chat_id", "KeyType": "HASH"},
            {"AttributeName": "ulid", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "chat_id", "AttributeType": "S"},
            {"AttributeName": "ulid", "AttributeType": "S"}
        ]
    },

    "UserData": {
        "TableName": "UserData",
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "email", "AttributeType": "S"} 
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "EmailIndex",
                "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"}
            }
        ]
    },

    "ChatData": {
        "TableName": "ChatData",
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [{"AttributeName": "chat_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "chat_id", "AttributeType": "S"}]
    },
    
    "UserChat": {
        "TableName": "UserChat",
        "BillingMode": "PAY_PER_REQUEST",
        "KeySchema": [
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "chat_id", "KeyType": "RANGE"}
        ],
        "AttributeDefinitions": [
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "chat_id", "AttributeType": "S"}
        ],
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "ChatIdIndex",
                "KeySchema": [
                    {"AttributeName": "chat_id", "KeyType": "HASH"},
                    {"AttributeName": "user_id", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ]
    }
}
```

### Metadata Access Patterns
We rely on transaction condition checks in order to maintain consistency of metadata state while tolerating eventual consistency on the read path and relying on caching. 

**Writes:**
1. **Condition Checks:** 
    - When creating/updating/removing chats/users we use conditional updates to ensure that the relevant chat and user records exist and are not marked as deleted before allowing the update to go through.
2. **Transactions:** 
    - When adding or removing users from a chat we use conditional updates to ensure that the chat exists and the user is not marked as deleted (for adding) or is a member of the chat (for removing) before allowing the update to go through.

**Reads: (Caching Layer)**
- We frequently check user status, chat status, and user-chat membership before allowing chat operations to ensure proper access control. 
- Because this is an extremely repetive check we use redis to cache user-chat membership data and rely on cache invalidation on updates to ensure we minimize latency for these checks while maintaining nearly immediate consistency (although technically a user can still read/write to a chat a bit after they are removed due to lag).

### Chat History Access Patterns
For chat history data we rely on DynamoDB's low latency for reads and writes and use a simple data model with a single table and efficient querying by chat_id and timestamp (ulid) for reads and conditional writes for ensuring data integrity on the write path.

**No Caching Layer:**
- We do not use a caching layer for chat history data because our read/write ratio is about equal and we want to ensure that users see new messages in a chat immediately without needing to worry about cache invalidation.

**Chat Deletion:**
- Chat deletetion is a metadata change that triggers an asynchronous task to delete the chat history data for that chat.
- To do this keep a background worker that listens for chat deletion events and deletes the relevant chat history data and user-chat membership records in batches.

**Eventual Consistency:**
- We do not use transactional condition checks with the metadata tables (like checking a chat exists before writing to it) and instead rely on the fact that metadata is eventually consistent. 
    - This means that in some edge cases we might write chat history data for a chat that has been deleted or for a user that has been removed from the chat, but we handle this gracefully on the read path by checking the metadata state before returning chat history data to the user.
    - This also means there may be memory leaks in the ChatHistory table from deleted chats/users, this could be handled with a periodic cleanup job that deletes chat history data for chats that have been deleted and users that have been removed from all their chats but we have not implemented this for simplicity.

## API Design
The API is made with FastAPI and designed as a RESTful API with the following endpoints:
1. `api/v1/users`: For user registration and management.
    - Includes endpoints for creating users, retrieving user information, and updating user metadata.
2. `api/v1/chats`: For chat creation and management.
    - Includes endpoints for creating chats, retrieving chat information, adding/removing users from chats, and deleting chats and reading/writing chat history.

We use 3 layers of abstraction for our API design:

1. **The API Layer:** which defines the RESTful endpoints and handles request validation and response formatting.
2. **The Service Layer:** which contains the business logic for handling user and chat operations, including interactions with the database and cache.
3. **The Repository Layer:** which abstracts away the details of interacting with DynamoDB and Redis, providing a clean interface for the service layer to perform database operations.

### Authentication and Authorization

### Pub/Sub Model

## Frontend
The frontend is built with Next.js and provides a user interface for interacting with the chat application. It includes features such as user registration, chat creation, and real-time chat updates. The frontend communicates with the backend API to perform these operations and uses WebSockets for real-time updates.

It heavily relies on server-side rendering for fast initial load times while delegating client-side rendering for dynamic interactions and real-time updates. The frontend is designed to be responsive and user-friendly, providing a seamless chat experience across different devices.

We organize our frontend code into features where each feature has 3 parts:
1. `ui/` The UI components for that feature
2. `components/` The client-side logic and state management for that feature
3. `view/` The server side rendering logic for that feature which also serves as the entry point for the feature's route.

styles for the app are organized into a global css file (`app/globals.css`).

We have 2 main features in our frontend:
1. Authentication (user registration and login)
2. Chat (creating chats, viewing chat list, viewing chat history, sending messages)

### Chat Feature
The chat feature includes the UI components for displaying chat messages, the input box for sending messages, and the logic for fetching and updating chat data in real-time. The view handles server-side rendering of the chat page and ensures that the initial chat history is loaded when a user navigates to a chat.

The logic for handling real-time updates is implemented using WebSockets, allowing users to see new messages in a chat without needing to refresh the page. The chat feature also includes functionality for scrolling through chat history, which is implemented using a request/response model to fetch older messages as the user scrolls up.