from dataclasses import dataclass
from harmony.app.services import ChatEventHandler, UserEventHandler, MessageEventHandler

@dataclass
class ConsumerContext:
    chat_handler: ChatEventHandler
    user_handler: UserEventHandler
    msg_handler: MessageEventHandler