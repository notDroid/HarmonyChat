from contextlib import asynccontextmanager
from aiokafka import AIOKafkaProducer
from harmony.app.core import KafkaConfig
import structlog

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def kafka_connector(cfg: KafkaConfig):
    """
    Context manager that yields a connected AIOKafkaProducer.
    Handles startup, idempotency setup, and graceful teardown.
    """
    producer = AIOKafkaProducer(
        bootstrap_servers=cfg.bootstrap_servers,
        acks="all",
        enable_idempotence=True,
        retry_backoff_ms=cfg.retry_backoff_ms,
    )

    try:
        await producer.start()
        logger.info("kafka_producer_started", bootstrap_servers=cfg.bootstrap_servers)
        yield producer
    except Exception as e:
        logger.exception("kafka_producer_failed_to_start")
        raise e
    finally:
        await producer.stop()
        logger.info("kafka_producer_stopped")