import json
import asyncio
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from harmony.app.core.settings import KafkaConsumerConfig
import structlog

from .router import EventRouter
from .context import ConsumerContext

logger = structlog.get_logger(__name__)

class CDCConsumer:
    def __init__(self, config: KafkaConsumerConfig, router: EventRouter, context: ConsumerContext):
        self.cfg = config
        self.router = router
        self.context = context
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
                msg_batch = await self.consumer.getmany(timeout_ms=self.cfg.poll_timeout_ms)
                
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
        except KafkaError as ke:
            logger.exception("kafka_consumer_error")
        except Exception as e:
            logger.exception("unexpected_consumer_error")
        finally:
            # await self.consumer.stop() # doesn't seem to be working reliably
            logger.info("cdc_consumer_stopped")

    async def process_message(self, msg) -> bool:
        try:
            body = json.loads(msg.value.decode("utf-8")) if msg.value else {}
            
            event_type = body.get("event_type")
            aggregate_id = body.get("aggregate_id")
            event_id = body.get("event_id")
            payload = body.get("payload", {})

            topic = msg.topic
            offset = msg.offset

            if not event_type or not aggregate_id or not event_id:
                logger.warning("skipping_invalid_message", topic=topic, offset=offset)
                return True

            # Bind context variables so all logs in this trace have the ID
            with structlog.contextvars.bound_contextvars(
                topic=topic, event=event_type, aggregate_id=aggregate_id, event_id=event_id, offset=offset
            ):
                logger.info("processing_cdc_event")
                
                try:
                    await self.router.route_event(topic, event_type, aggregate_id, payload, self.context)
                    logger.info("cdc_event_processed_successfully")
                    return True
                except Exception as e:
                    logger.exception("fatal_processing_error")
                    return False

        except json.JSONDecodeError:
            logger.error("poison_pill_invalid_json", offset=offset)
            # TODO: Send to a Dead Letter Queue for manual inspection
            return True 
        except Exception as e:
            logger.exception("unexpected_consumer_error", offset=offset)
            return False