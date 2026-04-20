from nbajinni_shared.logging import configure_logging, get_logger
from nbajinni_shared.session import get_session_factory
configure_logging()
logger = get_logger("backend_api")

AsyncSessionLocal = get_session_factory()


async def get_db():
    
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        logger.error("get_session_failed", error=str(e))
        raise