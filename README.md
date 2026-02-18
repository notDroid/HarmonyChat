# Harmony Chat
A fullstack discord/slack based chat app built with FastAPI (backend) and Next.js (frontend) using DynamoDB and Postgres for data storage, Redis for caching and pub/sub, and Kafka for event streaming. The app is deployed locally with Docker Compose and can be easily set up and run with Taskfile.

### Setup
Dependencies:

1. Conda
2. Taskfile
3. Docker


Setup the project by running the following command:
```bash
task setup
```

### Run and Test Locally
To run the application locally using Docker Compose, use the following commands:
```bash
task build
task run:dev
```

In another terminal, run tests:
```bash
task test:stress
```

For the full list of explorable tasks, run:
```bash
task
```

### TODO List
- [ ] Implement authentication and authorization
- [ ] Implement pub/sub model for real-time chat updates
- [ ] Implement request/response model for scrolling through chat history
- [ ] Implement caching layer for user-chat membership data to optimize presence checks
- [ ] Deploy app to AWS with terraform and set up CI/CD pipeline

# Implementation Documentation

## Design Decisions

### Databases
1. Dynamodb is suitable to store real time chat data due to its low latency and high scalability for small message record data model which doesn't require relational operations or complex transactions.
2. Postgres is suitable to store user and chat metadata which requires relational operations and complex transactions.

### Caching
We use Redis as a caching layer to store user-chat membership data to optimize presence checks. This allows us to quickly determine if a user is part of a chat without having to query the database, improving performance for real-time chat updates. We rely on cache invalidation strategies to ensure data consistency between Redis and our databases.

### Streaming
We use WebSockets for real-time communication between the client and server. We use a redis pub/sub model to broadcast messages. Fastapi servers can subscribe to relevant chat servers and then broadcast recieved messages to connected clients. This allows for efficient real-time updates without the need for clients to continuously poll the server for new messages.

### Log Source of Truth
We use Kafka as the source of truth for chat history. All messages are published to a Kafka topic, and we have a consumer that listens to this topic and writes messages to DynamoDB for persistence and publish it to redis for streaming. This allows us to decouple the real-time messaging from the database writes, improving performance and scalability.

### Asynchronous Event Processing
We model events in the chat system like deleting a chat or removing a user from a chat as asynchronous events. When such an event occurs we write it atomically to an outbox table in postgres and use the debezium integration to stream these events to Kafka. We have consumers that listen to these topics and perform the necessary database updates and cache invalidations. This allows us to handle these operations asynchronously, improving performance and responsiveness of the system.

### Containers
We use a single docker image for the fastapi server but we deploy it for 3 different purposes: the rest endpoint server, the websocket server, and the event processor. We use a single container for the next js frontend. We deploy redis with 2 containers, one for pub/sub and one for caching. The other services we either use externally or we use their official docker images (postgres, dynamodb, and kafka).
