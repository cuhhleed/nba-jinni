from mangum import Mangum
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from nbajinni_shared.session import get_session_factory
from nbajinni_shared.logging import configure_logging, get_logger


load_dotenv()

configure_logging()
logger = get_logger("backend_api")

AsyncSessionLocal = get_session_factory()

app = FastAPI()


origins = [
    os.getenv("FRONTEND_ORIGIN")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except Exception as e:
        logger.error("get_session_failed", error=str(e))
        raise


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))  # Verify DB connection
    return {"status": "healthy"}

handler = Mangum(app, lifespan="off")
