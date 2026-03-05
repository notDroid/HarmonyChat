import json
import asyncio
from aiokafka import AIOKafkaConsumer
import structlog

from harmony.app.services import ChatEventHandler, UserEventHandler, MessageEventHandler

logger = structlog.get_logger(__name__)

class CDCConsumer:
    def __init__(self, kafka_bootstrap_servers: str, chat_handler: ChatEventHandler, user_handler: UserEventHandler, message_handler: MessageEventHandler):
        # The topics are dictated by your Debezium outbox routing (aggregate_type)
        self.topics = ["Chat", "User"] 
        self.bootstrap_servers = kafka_bootstrap_servers
        
        self.chat_handler = chat_handler
        self.user_handler = user_handler
        self.message_handler = message_handler

    async def start(self):
        consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id="harmony-cdc-consumer",
            enable_auto_commit=True,
            auto_offset_reset="earliest"
        )
        
        await consumer.start()
        logger.info("cdc_consumer_started", topics=self.topics)
        
        try:
            async for msg in consumer:
                await self.process_message(msg)
        finally:
            await consumer.stop()

    async def process_message(self, msg):
        try:
            # Debezium Outbox Event Router unwraps the payload. 
            # The msg.value is the JSON from your OutboxEvent payload column.
            payload = json.loads(msg.value.decode("utf-8")) if msg.value else {}
            
            # Debezium can pass metadata in Kafka headers. Let's extract the event_type.
            headers = {k: v.decode('utf-8') if v else None for k, v in (msg.headers or [])}
            event_type = headers.get("eventType")
            aggregate_id = msg.key.decode("utf-8") if msg.key else None

            logger.info("cdc_event_received", topic=msg.topic, event_type=event_type, aggregate_id=aggregate_id)

            # Route to appropriate event handler based on Topic (Aggregate Type) and Event Type
            if msg.topic == "Chat":
                await self.handle_chat_event(event_type, aggregate_id, payload)
            elif msg.topic == "User":
                await self.handle_user_event(event_type, aggregate_id, payload)

        except Exception as e:
            logger.exception("failed_to_process_cdc_message", topic=msg.topic, offset=msg.offset)

    async def handle_chat_event(self, event_type: str, chat_id: str, payload: dict):
        import uuid
        chat_uuid = uuid.UUID(chat_id)
        
        if event_type == "USERS_ADDED":
            user_id_list = [uuid.UUID(uid) for uid in payload.get("user_id_list", [])]
            await self.chat_handler.on_users_added_to_chat(chat_uuid, user_id_list)
            
        elif event_type == "USER_LEFT":
            user_uuid = uuid.UUID(payload.get("user_id"))
            await self.chat_handler.on_user_left_chat(chat_uuid, user_uuid)
            
        elif event_type == "CHAT_DELETED":
            await self.chat_handler.on_chat_deleted(chat_uuid)
            await self.message_handler.on_chat_deleted(chat_uuid)

    async def handle_user_event(self, event_type: str, user_id: str, payload: dict):
        import uuid
        user_uuid = uuid.UUID(user_id)
        
        if event_type == "TOMBSTONED":
            await self.user_handler.on_delete_user(user_uuid)