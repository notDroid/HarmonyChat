import logging
from logging.handlers import QueueHandler, QueueListener
import queue
import sys
import structlog
from structlog.types import Processor

class ThreadSafeQueueHandler(QueueHandler):
    """
    A custom QueueHandler that doesn't prematurely format the log record.
    This preserves the structlog dictionary for the StreamHandler's formatter.
    """
    def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
        return record

def setup_logging(is_local_dev: bool = True):
    """
    Configures structlog and standard logging.
    If is_local_dev is True, outputs pretty, colorized logs.
    If False, outputs strict JSON for log aggregators.
    """
    # -------------------------- Structlog Configuration ------------------------- #

    # 1. Define the processors that run on every log message
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,       # Pulls in our Correlation IDs
        structlog.stdlib.add_logger_name,              # Adds the module name (e.g., harmony.services.chat)
        structlog.stdlib.add_log_level,                # Adds INFO, ERROR, etc.
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),   # Adds a standardized timestamp
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,          # Formats exception tracebacks
    ]

    # 2. Choose the output format based on environment
    if is_local_dev:
        # PRETTY LOGS: Great for your terminal
        formatter = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON LOGS: Great for Datadog, AWS CloudWatch, etc.
        formatter = structlog.processors.JSONRenderer()

    # 3. Configure structlog to use the standard library for actual output
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # ---------------------------- Async Logging Setup --------------------------- #
    # 1. Create the standard stream handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(structlog.stdlib.ProcessorFormatter(processor=formatter))
    
    # 2. Create a thread-safe queue and a non-blocking QueueHandler
    log_queue = queue.Queue(-1) # Infinite queue
    queue_handler = ThreadSafeQueueHandler(log_queue)
    
    # 3. Create a listener that writes from the queue to the stream in a background thread
    listener = QueueListener(log_queue, stream_handler, respect_handler_level=True)
    listener.start()

    # 4. Attach ONLY the non-blocking queue handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(logging.INFO)

    # ------------------------------ Hijack Uvicorn ------------------------------ #
    for _log in ["uvicorn", "uvicorn.error"]:
        logger_instance = logging.getLogger(_log)
        logger_instance.handlers.clear()
        logger_instance.propagate = True

    # MUTE uvicorn.access completely because our custom middleware handles request logging
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False

    return listener