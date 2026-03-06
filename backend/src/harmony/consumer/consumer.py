import json
import asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from harmony.app.core.settings import KafkaConsumerConfig
import structlog

from .router import EventRouter

logger = structlog.get_logger(__name__)

class CDCConsumer:
    def __init__(self, config: KafkaConsumerConfig, router: EventRouter):
        self.cfg = config
        self.router = router
        self.consumer = AIOKafkaConsumer(
            *self.cfg.topics,
            bootstrap_servers=self.cfg.bootstrap_servers,
            group_id=self.cfg.group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",

            max_poll_records=self.cfg.max_poll_records,
            fetch_max_bytes=self.cfg.fetch_max_bytes,
            session_timeout_ms=self.cfg.session_timeout_ms
        )

    async def start(self, stop_event: asyncio.Event):
        await self.consumer.start()
        logger.info("cdc_consumer_started", topics=self.cfg.topics)
        
        try:
            while not stop_event.is_set():
                msg_batch = await self.consumer.getmany(timeout_ms=1000)
                
                for tp, messages in msg_batch.items():
                    for msg in messages:
                        if stop_event.is_set():
                            break

                        success = await self.process_message(msg)
                        
                        if success:
                            await self.consumer.commit({tp: msg.offset + 1})
                        else:
                            # TODO: Implement a proper DLQ mechanism. For now, we log and skip the message to prevent blocking.
                            logger.critical("fatal_processing_error", offset=msg.offset)
                            raise Exception(f"Failed to process message {msg.offset}. Crashing consumer to prevent data loss.")
                            
        finally:
            await self.consumer.stop()
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
                    logger.exception("fatal_processing_error", offset=msg.offset)
                    return False

        except json.JSONDecodeError:
            logger.error("poison_pill_invalid_json", offset=msg.offset)
            # TODO: Send to a Dead Letter Queue for manual inspection
            return True 
        except Exception as e:
            logger.exception("unexpected_consumer_error", offset=msg.offset)
            return False