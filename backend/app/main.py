from mangum import Mangum
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import os
from dotenv import load_dotenv

from nbajinni_shared.logging import configure_logging, get_logger
from .dependencies import get_db
from .routers import players, teams, games, standings

load_dotenv()

configure_logging()
logger = get_logger("backend_api")

app = FastAPI()
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(games.router)
app.include_router(standings.router)

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

@app.get("/")
async def root():
    return {
        "name": "NBAJinni API",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))  # Verify DB connection
    return {"status": "healthy"}



handler = Mangum(app, lifespan="off")
