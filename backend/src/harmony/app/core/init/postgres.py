from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from harmony.app.core import get_settings, PostgresConfig
from harmony.app.models import Base

async def init_postgres(app, stack):
    """
    Initializes the Postgres connection and session factory, storing it in app.state.
    """
    settings = get_settings()
    if not settings.features.postgres:
        return

    session_factory = await stack.enter_async_context(postgres_connector(settings.app_env == "development", settings.postgres))
    app.state.session_factory = session_factory

@asynccontextmanager
async def postgres_connector(dev_mode: bool, cfg: PostgresConfig):
    """
    Context manager that yields a SQLAlchemy session factory.
    Handles engine creation and disposal.
    """
    # 1. Create Engine
    engine = create_async_engine(
        cfg.url,
        echo=dev_mode,
        future=True
    )

    # 2. Create Tables (Dev Only)
    # In production, use Alembic. 
    if dev_mode:
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