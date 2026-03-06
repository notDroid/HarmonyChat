from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError
import structlog

from harmony.app.core.exceptions import ConflictError, InternalServerError, HarmonyError
from sqlalchemy.ext.asyncio import AsyncSession

class Command:
    def __init__(self, session: AsyncSession, logger: structlog.BoundLogger):
        self.session = session
        self.logger = logger

    @asynccontextmanager
    async def transaction_handler(self, action_name: str, **log_context):
        """
        A context manager to handle commits, rollbacks, and exception translation.
        With an action_name and kwargs to maintain logs.
        """
        try:
            yield
            await self.session.commit()
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(f"{action_name}_integrity_error", detail=str(e.orig), **log_context)
            raise ConflictError("Operation failed: One or more provided records do not exist or violate system constraints.")
        except HarmonyError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            self.logger.exception(f"{action_name}_failed", **log_context)
            raise InternalServerError(f"An unexpected error occurred while trying to {action_name.replace('_', ' ')}.")