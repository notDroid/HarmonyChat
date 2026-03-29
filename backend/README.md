# Harmony Chat - Backend API & CDC Consumer

## 🛠 Tech Stack

- **Framework**: FastAPI (Python 3.12+)
- **Package Manager**: `uv`
- **Databases**: PostgreSQL (AsyncPG + SQLAlchemy 2.0), DynamoDB (`aioboto3`), Redis (Caching & PubSub)
- **Message Broker**: Kafka (Event Sourcing & CDC via Debezium)
- **Data Validation**: Pydantic v2
- **Logging**: Structlog (Structured JSON logging)

---

## 🏗 Architecture Overview

The backend is split into two primary components running as separate processes:

1. **The API (`harmony.api`)**: A standard FastAPI REST API. It handles incoming HTTP requests, WebSocket proxy authorizations (Centrifugo), database reads/writes, and caching.
2. **The CDC Consumer (`harmony.consumer`)**: A background Kafka consumer that listens to Change Data Capture (CDC) events emitted by PostgreSQL (via Debezium/Outbox). It updates secondary data stores (like DynamoDB), invalidates Redis caches, and handles distributed side effects asynchronously to ensure eventual consistency.

### Key Patterns Used

* **CQRS (Command Query Responsibility Segregation)**: Business logic in `app/services/` is explicitly divided into `command.py` (state-mutating writes) and `query.py` (read-only operations).
* **Transactional Outbox**: When a command updates PostgreSQL, it simultaneously writes an event to the `outbox_events` table within the *same transaction*. This guarantees that local state changes and outbound Kafka events are perfectly synced.
* **Cache-Aside**: Redis is used extensively for metadata and membership authorization. Cache invalidation is triggered asynchronously via the CDC Consumer.

---

## 📂 Directory Structure

```text
backend/
├── Dockerfile                  # Multi-stage Dockerfile using `uv`
├── pyproject.toml              # Python dependencies and project metadata
├── specs/                      # Scripts to extract OpenAPI schema (for frontend SDK generation)
└── src/harmony/
    ├── api/                    # 1. REST API Layer (FastAPI Routers & Dependencies)
    │   ├── v1/                 # Endpoints (Auth, Chat, User, WebSocket)
    │   ├── dependencies.py     # FastAPI Dependency Injection definitions
    │   ├── main.py             # FastAPI App instance and middlewares
    │   └── lifespan.py         # Startup/Shutdown logic (DB connections)
    │
    ├── app/                    # 2. Core Business Logic & Data Access Layer
    │   ├── core/               # Settings, Exceptions, Security (JWT/Hashes), Logging
    │   ├── db/                 # DynamoDB helpers and serializers
    │   ├── init/               # Async context managers for connecting to external services
    │   ├── models/             # SQLAlchemy ORM Models (Postgres source-of-truth)
    │   ├── schemas/            # Pydantic Models (DTOs for requests/responses)
    │   ├── repositories/       # Data Access Layer (Postgres & DynamoDB interactions)
    │   └── services/           # Business Logic Layer (CQRS Commands, Queries, & Event Handlers)
    │
    ├── consumer/               # 3. Change Data Capture (CDC) Kafka Worker
    │   ├── handlers/           # Event handlers mapped to Kafka topics
    │   ├── consumer.py         # Main AIOKafkaConsumer loop
    │   └── main.py             # Entrypoint for the consumer process
    │
    └── tests/                  # 4. Testing & Tooling
        ├── integration/        # API Integration tests
        ├── stress/             # High-concurrency system stress tests
        ├── tools/              # Dummy data generators (`data:generate`)
        └── utils/              # Test state, mock clients, and metrics
```