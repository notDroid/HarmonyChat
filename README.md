# Harmony Chat
This is a fullstack project implementing a simple chat app for learning system design and devops.

Developed With:
  1. Frameworks: FastAPI (backend), Next.js (frontend)

Architecture Components:
  1. Centrifugo+Redis (user facing pub/sub)
  2. Kafka (log source of truth for messages + app state CDC)
  3. DynamoDB (message storage)
  4. Postgres (app state source of truth)

Utilized/Learned:
  - FastAPI, Next.js (heavy on react-query and SSR),
  - Centrifugo, Redis, Kafka, DynamoDB, Postgres,
  - Docker, Docker compose,
  - (Kubernetes, Terraform, ECS/EKS, github actions (CI/CD))

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
To run the application locally:
```bash
task run:dev
```

In another terminal, run tests:
```bash
task test:stress # Run stress tests
task data:generate # Continuously generate data
```

For the full list of explorable tasks, run:
```bash
task
```

### TODO List
- [x] Implement repo wrappers to interact with dynamodb tables
- [x] Implement simple poll based fastapi backend
- [x] Implement simple frontend with next.js
- [x] Implement backend endpoints for chat and user management
- [x] Implement authentication with access token JWTs
- [x] Use the backend for frontend pattern by proxying api requests through the frontend and setting the authorization header
- [x] Implement pub/sub model for real-time chat updates in fastapi with redis pub/sub broker
- [x] Use react query in the frontend and do optimistic server side hydration with client side fallback
- [x] Implement pagination model for scrolling through chat history
- [x] Migrate to postgres storage for user and chat metadata and rely on transactions + row based locking for state consistency
- [x] Upgrade frontend UI
- [x] Implement refresh tokens with rotation and automatic resolution of expired access tokens and 401 errors
- [x] Implement redis caching layer for metadata.
- [x] Migrate websocket handling to centrifugo+redis.
- [x] Implement kafka-based event sourcing for chat messages with integrated centrifugo consumer and kafka connect integration for dynamodb with transform
- [x] Implement CDC with postgres+debzium -> kafka and handle events caused by state changes with eventual consistency.
- [ ] Deploy app to AWS with terraform and set up CI/CD pipeline

## Implementation Documentation

### Databases
1. Dynamodb is suitable to store real time chat data due to its low latency and high scalability for small message record data model which doesn't require relational operations or complex transactions. Dynamodb serves as storage for messages and is eventually consistent with the kafka which sources the messages.
2. Postgres is suitable to store user and chat metadata which requires relational operations and complex transactions. Postgres is the source of truth for the app state and we use CDC into kafka to handle metadata events to keep the app eventually consistent with the actual state.

### Caching
We use Redis as a caching layer to store user-chat membership and user/chat metadata. We frequently need to check user-chat membership and need to fill in user metadata when requesting chat messages which are often highly repetitive requests making them a good fit for caching to increase the speed of response and reduce the load on postgres. Some CDC events trigger cache invalidation to ensure data consistency between Redis and the app state.

### Streaming
We use Centrifugo to manage websocket connections with clients. It provides a simple pub/sub model for frontend websocket users. It authenticates connections and subscriptions by proxying requests to the fastapi servers. It uses a redis as an engine to cache user presence, recent messages, and uses redis pub/sub as a broker for message data.

### Log Source of Truth
We use Kafka as the source of truth for chat history. All messages are published to a Kafka topic where it can then be committed. Then a kafka connect consumer with an integration for dynamodb listens to this topic, strips the author metadata from it, and catches up dynamodb with it. Centrifugo has a built in kafka consumer that caches and broadcasts messages to listeners. Kafka presents the advantage of acting like a buffer for dynamodb while decoupling centrifugo and dynamodb from the fastapi backend and each other. For instance if dynamodb is overloaded we can still have short term consistency because centrifugo is unlikely to be overloaded.

### Change Data Capture
App state changes like deleting a chat have side effects that need to be caught up with in the overall system. When such an event occurs we write it atomically to an outbox table in postgres and use the debezium integration to stream these events to Kafka. We have consumers that listen to these topics and perform the necessary database updates and cache invalidations. This gaurantees the system is eventually consistency with the state specified in postgres as events will be consumed at least once and event handlers are idempotent.
