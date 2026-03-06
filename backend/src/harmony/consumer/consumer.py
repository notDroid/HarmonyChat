import json
import asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
import structlog

from .router import EventRouter

logger = structlog.get_logger(__name__)

class CDCConsumer:
    def __init__(self, kafka_bootstrap_servers: str, topics: list[str], router: EventRouter):
        self.topics = topics
        self.bootstrap_servers = kafka_bootstrap_servers
        self.router = router

    async def start(self, stop_event: asyncio.Event):
        consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id="harmony-cdc-consumer",
            enable_auto_commit=False,
            auto_offset_reset="earliest"
        )
        
        await consumer.start()
        logger.info("cdc_consumer_started", topics=self.topics)
        
        try:
            while not stop_event.is_set():
                msg_batch = await consumer.getmany(timeout_ms=1000)
                
                for tp, messages in msg_batch.items():
                    for msg in messages:
                        if stop_event.is_set():
                            break

                        success = await self.process_message(msg)
                        
                        if success:
                            await consumer.commit({tp: msg.offset + 1})
                        else:
                            # TODO: Implement a proper DLQ mechanism. For now, we log and skip the message to prevent blocking.
                            logger.critical("fatal_processing_error", offset=msg.offset)
                            raise Exception(f"Failed to process message {msg.offset}. Crashing consumer to prevent data loss.")
                            
        finally:
            await consumer.stop()
            logger.info("cdc_consumer_stopped")

    async def process_message(self, msg) -> bool:
        try:
            payload = json.loads(msg.value.decode("utf-8")) if msg.value else {}
            
            headers = {k: v.decode('utf-8') if v else None for k, v in (msg.headers or [])}
            event_type = headers.get("eventType")
            aggregate_id = msg.key.decode("utf-8") if msg.key else None

            if not event_type or not aggregate_id:
                logger.warning("skipping_invalid_message", topic=msg.topic, offset=msg.offset)
                return True

            # Bind context variables so all logs in this trace have the ID
            with structlog.contextvars.bound_contextvars(
                topic=msg.topic, event=event_type, aggregate_id=aggregate_id
            ):
                logger.info("processing_cdc_event")
                
                try:
                    await self.router.route_event(msg.topic, event_type, aggregate_id, payload)
                    return True
                except Exception as e:
                    logger.exception("fatal_processing_error", error=str(e))
                    return False

        except json.JSONDecodeError:
            logger.error("poison_pill_invalid_json", offset=msg.offset)
            # TODO: Send to a Dead Letter Queue for manual inspection
            return True 
        except Exception as e:
            logger.exception("unexpected_consumer_error", offset=msg.offset)
            return False