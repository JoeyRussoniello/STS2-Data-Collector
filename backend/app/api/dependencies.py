"""FastAPI dependency injection — wires adapters into domain services."""

from __future__ import annotations

from typing import AsyncGenerator

from app.adapters.postgres.database import async_session
from app.adapters.postgres.repository import PostgresRunRepository
from app.config import settings
from app.domain.services import RunService


async def get_run_service() -> AsyncGenerator[RunService, None]:
    async with async_session() as session:
        repo = PostgresRunRepository(session)
        yield RunService(repo, settings.steam_id_salt)
