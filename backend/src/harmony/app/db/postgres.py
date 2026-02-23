from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from harmony.app.core import settings
from harmony.app.models import Base

@asynccontextmanager
async def postgres_connector():
    """
    Context manager that yields a SQLAlchemy session factory.
    Handles engine creation and disposal.
    """
    if not settings.ENABLE_POSTGRES:
        yield None
        return

    # 1. Create Engine
    engine = create_async_engine(
        settings.POSTGRES_URL, 
        echo=(settings.APP_ENV == "development"),
        future=True
    )

    # 2. Create Tables (Dev Only)
    # In production, use Alembic. 
    if settings.APP_ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # 3. Create Factory
    session_factory = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False
    )

    try:
        yield session_factory
    finally:
        # 4. Cleanup
        await engine.dispose()