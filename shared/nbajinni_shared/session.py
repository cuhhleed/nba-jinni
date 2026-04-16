import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

_in_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

if not _in_lambda:
    from dotenv import load_dotenv
    load_dotenv()  # Searches upward from CWD for .env

def _build_database_url():
    if _in_lambda:
        user = os.environ["DB_USER"]
        password = os.environ["DB_PASSWORD"]
        endpoint = os.environ["DB_HOST"]  # host:port format from RDS
        name = os.environ["DB_NAME"]
        return f"postgresql+asyncpg://{user}:{password}@{endpoint}/{name}"
    return os.getenv("DATABASE_URL")

DATABASE_URL = _build_database_url()

def get_session_factory(database_url=None):
    if database_url == "test":
        url = os.getenv("TEST_DATABASE_URL")
    elif database_url == "dev":
        url = DATABASE_URL
    elif database_url:
        url = database_url
    else:
        url = DATABASE_URL

    engine = create_async_engine(url, echo=False, pool_size=1)
    return sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
