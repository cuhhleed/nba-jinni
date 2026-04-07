import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_session_factory(database_url=None):
    if database_url == "test":
        url = os.getenv("TEST_DATABASE_URL")
    elif database_url:
        url = database_url
    else:
        url = DATABASE_URL
    
    engine = create_async_engine(url, echo=False)
    return sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

AsyncSessionLocal = get_session_factory()
