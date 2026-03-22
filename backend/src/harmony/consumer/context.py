from dataclasses import dataclass
from harmony.app.services import ChatEventHandler, UserEventHandler, MessageEventHandler
from harmony.app.core import get_consumer_settings, ConsumerSettings

@dataclass
class ConsumerContext:
    chat_handler: ChatEventHandler
    user_handler: UserEventHandler
    msg_handler: MessageEventHandler
    settings: ConsumerSettings