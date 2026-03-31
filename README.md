# Harmony Chat

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white)](https://kafka.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![DynamoDB](https://img.shields.io/badge/Amazon%20DynamoDB-4053D6?style=for-the-badge&logo=Amazon%20DynamoDB&logoColor=white)](https://aws.amazon.com/dynamodb/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Centrifugo](https://img.shields.io/badge/Centrifugo-2563EB?style=for-the-badge&logo=centrifugo&logoColor=white)](https://centrifugal.dev/)

Harmony Chat is a fullstack chat application created for learning purposes as an exploration of distributed systems, event-driven architecture, and modern DevOps practices. 

We intentionally keep the application level simple to practice the more complex underlying architecture patterns necessary for high scalability, state consistency, and real-time data streaming.

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy, Pytest
- **Frontend:** TypeScript, Next.js, React Query, Tailwind CSS, Orval
- **Infrastructure:** AutoMQ Kafka, PostgreSQL, DynamoDB, Redis, Centrifugo, Conduit, Redpanda Connect

## Frontend Screenshots
<p align="center">
  <img src="https://github.com/user-attachments/assets/238529c1-dc3d-4c7b-a0fc-0773d54d578a" width="45%" alt="Frontend Chat Screen Dark Mode">
  <img src="https://github.com/user-attachments/assets/c14729b9-d942-4710-b18e-17fd992c1247" width="45%" alt="Frontend Chat Screen Light Mode">
</p>

---

## Architecture & Implementation Details

The system is designed around separating relational state (users, chat metadata) from high-volume, append-only data (chat messages), bound together by a fault-tolerant event-driven backbone. 

Here is the logic behind our core architectural decisions:

### 1. Databases & Storage Strategy
* **PostgreSQL (State Source of Truth):** Ideal for storing user profiles, chat metadata, and user-chat relational mappings. These domains require complex transactions and row-based locking, making Postgres the strict source of truth for the application state. We rely on Change Data Capture (CDC) to keep the rest of the system eventually consistent with this state.
* **DynamoDB (Message Storage):** Chosen to store real-time chat data. Its low latency and high scalability are perfectly suited for a small message record data model that doesn't require relational joins. It serves as the long-term storage for messages and is eventually consistent with the Kafka topics that source them.

### 2. Log Source of Truth (Kafka)
Kafka acts as the source of truth for chat history. When a user sends a message, it is sent to kafka and considered committed after being persisted within kafka.
* A **Kafka Connect** sink with a DynamoDB integration listens to this topic, strips transient author metadata from the payload, and persists the data to DynamoDB.
* Simultaneously, **Centrifugo** consumes the same topic to instantly broadcast messages to active WebSocket listeners.
* **The Architectural Advantage:** Kafka acts as a buffer that decouples Centrifugo, DynamoDB, and the FastAPI backend. 
  * For instance if DynamoDB experiences throttling or downtime, the system maintains short-term consistency: Centrifugo will continue delivering messages to active users in real-time, while DynamoDB safely catches up later once it recovers.

### 3. Change Data Capture (CDC) & The Outbox Pattern
Application state changes (e.g., adding users to a chat, deleting a chat) produce side effects that must propagate through the entire system. 
* We utilize the **Transactional Outbox Pattern** in PostgreSQL to atomically write state changes alongside outbox events within the same transaction.
* **Debezium** reads the Postgres Write-Ahead Log (WAL) and streams these outbox events into Kafka.
* A custom Python CDC Consumer worker (`harmony.consumer`) processes these events with strict idempotency guarantees to update secondary storage (postgres and dynamodb) and invalidate Redis caches.
* **The Architectural Advantage:** 
  * Because Kafka guarantees at-least-once delivery and our consumer event handlers are strictly idempotent, this pattern guarantees the distributed system will eventually achieve consistency with the relational source of truth, avoiding the need for distributed transactions.

### 4. Streaming & WebSockets (Centrifugo)
We use **Centrifugo** to manage persistent WebSocket connections, providing a simple and highly scalable pub/sub model for frontend clients. 
* It securely authenticates connections and channel subscriptions by proxying requests back to the FastAPI backend, which completely decouples the WebSocket connection pool from the Python API instances. 
* Under the hood, it uses a Redis engine to cache user presence and recent messages, and utilizes Redis pub/sub as the broker for real-time message data.

### 5. Caching Layer (Redis)
We use the Cache-Aside pattern with Redis to increase response speed and decrease database load for metadata lookups. 

* We frequently need to verify user-chat membership for authorization and hydrate chat messages with user metadata. By caching this data, we dramatically increase response speeds and reduce the load on PostgreSQL. 
* Cache invalidation is integrated into the CDC event consumer to prevent stale reads when the relational state changes.

### 6. Backend-For-Frontend (BFF) Auth Proxy
Authentication utilizes rotating JWT access and refresh tokens. 
* The Next.js server acts as a proxy (`api/proxy/{api_path}`), securely attaching HTTP-only cookies to outgoing requests bound for the internal FastAPI backend.
* We transparently handle access token management without disrupting the client experience by using middleware (`proxy.ts`) to resolve expired credentials and (`api/refresh`) for resolving HTTP 401s.
* The backend uses a opaque string refresh tokens stored in postgres and rotates them on refresh with a very short grace period before invalidation to handle multiple refresh requests in close proximity.
* The frontend heavily utilizes React Query for optimistic UI updates, complete with automatic rollback capabilities upon network failure.

---

## Local Development & Setup

### Dependencies
We use devbox to manage all development dependencies. Use `devbox shell` to download and enter the devbox environment.
We use task to manage all development commands, which are defined in the `Taskfile.yaml` at the root of the repository

### Initial Setup
Download pyton and node dependencies for both the frontend and backend by running (uv sync and npm install):
```bash
task setup
```

### Run the Application with Docker Compose
```bash
task run:dev
```

### Run the Application with Kind
```bash
task kind:setup
```

### Explore Available Tasks
To see a full list of available development tasks (like running tests, generating fake data, compiling environments, or syncing OpenAPI schemas):
```bash
task
```

---

## Roadmap & TODOs

- [x] Implement repo wrappers to interact with DynamoDB tables
- [x] Implement simple poll-based FastAPI backend
- [x] Implement simple frontend with Next.js
- [x] Implement backend endpoints for chat and user management
- [x] Implement authentication with access token JWTs
- [x] Use the Backend-For-Frontend pattern proxying API requests to securely set HTTP-only cookies
- [x] Implement pub/sub model for real-time chat updates
- [x] Use React Query in the frontend for optimistic server-side hydration and client-side fallback
- [x] Implement ULID cursor-based pagination for chat history
- [x] Migrate to Postgres storage for metadata, relying on transactions and row-based locking
- [x] Implement refresh tokens with rotation and automatic resolution of expired access tokens
- [x] Implement Redis caching layer for metadata and membership authorization
- [x] Migrate WebSocket handling to Centrifugo + Redis
- [x] Implement Kafka-based event sourcing for chat messages with Kafka Connect DynamoDB sink
- [x] Implement CDC (Change Data Capture) with Postgres Outbox + Debezium + Kafka
- [x] Build k8s set up with helm and deploy locally using kind.
- [x] Switch from Apache Kafka to AutoMQ, from Debezium to Conduit, from Kafka Connect to Redpanda Connect
- [x] Deploy simplified application to AWS via Terraform
- [x] Setup GitHub Actions CI
- [ ] Setup argoCD
- [ ] Upgrade k8s setup with API Gateway and Autoscaling
- [ ] Launch production deployment
