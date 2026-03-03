from contextlib import asynccontextmanager
from harmony.app.core import get_settings, CentrifugoConfig

from cent import AsyncClient

async def init_stream(app, stack):
    """
    Initializes the cent client.
    """
    settings = get_settings()
    if not settings.features.centrifugo:
        return

    cent_client = await stack.enter_async_context(stream_connector(settings.cent))
    app.state.cent_client = cent_client

@asynccontextmanager
async def stream_connector(cfg: CentrifugoConfig = None):
    """
    Context manager that yields cent client
    """

    client = AsyncClient(
        api_url=cfg.url, 
        api_key=cfg.api_key,
        timeout=cfg.timeout
    )
    
    try:
        yield client
    finally:
        await client.close()