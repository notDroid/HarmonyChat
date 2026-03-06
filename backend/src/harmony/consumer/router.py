import structlog
from typing import Callable, Awaitable, Dict, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
import logging

logger = structlog.get_logger(__name__)

EventHandler = Callable[[str, dict], Awaitable[None]]

class EventRouter:
    def __init__(self):
        self._routes: Dict[Tuple[str, str], EventHandler] = {}

    def register(self, aggregate_type: str, event_type: str):
        def decorator(func: EventHandler):
            self._routes[(aggregate_type, event_type)] = func
            return func
        return decorator

    async def _route(self, aggregate_type: str, event_type: str, aggregate_id: str, payload: dict):
        handler = self._routes.get((aggregate_type, event_type))
        if not handler:
            logger.debug("no_handler_registered_for_event", aggregate=aggregate_type, event=event_type)
            return

        await handler(aggregate_id, payload)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
    async def route_event(self, aggregate_type: str, event_type: str, aggregate_id: str, payload: dict):
        await self._route(aggregate_type, event_type, aggregate_id, payload)