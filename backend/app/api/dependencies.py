"""FastAPI dependency injection — wires adapters into domain services."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Security
from fastapi.security import APIKeyHeader

from app.adapters.postgres.database import async_session
from app.adapters.postgres.repository import PostgresRunRepository
from app.adapters.postgres.stats_repository import PostgresStatsRepository
from app.config import settings
from app.domain.services import RunService
from app.domain.stats import StatsService

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """Validate the API key. Raises 401 if missing or invalid."""
    import hmac

    from fastapi import HTTPException

    if api_key is None or not hmac.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


async def get_run_service() -> AsyncGenerator[RunService, None]:
    async with async_session() as session:
        repo = PostgresRunRepository(session)
        yield RunService(repo, settings.steam_id_salt)


async def get_stats_service() -> AsyncGenerator[StatsService, None]:
    async with async_session() as session:
        repo = PostgresStatsRepository(session)
        yield StatsService(repo, settings.steam_id_salt)
