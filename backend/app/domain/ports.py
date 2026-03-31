"""Abstract repository interface (port) for run storage."""

from __future__ import annotations

import abc

from app.domain.models import RunRecord


class RunRepository(abc.ABC):
    @abc.abstractmethod
    async def upsert(self, record: RunRecord) -> RunRecord:
        """Insert or update a run record. Returns the persisted record."""

    @abc.abstractmethod
    async def get_by_run_id(self, run_id: str) -> RunRecord | None:
        """Fetch a single run by its composite ID."""

    @abc.abstractmethod
    async def get_by_steam_id_hash(
        self, steam_id_hash: str, *, limit: int = 50, offset: int = 0
    ) -> list[RunRecord]:
        """Fetch all runs for a hashed Steam ID, newest first."""

    @abc.abstractmethod
    async def count_by_steam_id_hash(self, steam_id_hash: str) -> int:
        """Count total runs for a hashed Steam ID."""

    @abc.abstractmethod
    async def list_all(
        self, *, limit: int = 50, offset: int = 0
    ) -> list[RunRecord]:
        """Fetch all runs, newest first."""

    @abc.abstractmethod
    async def count_all(self) -> int:
        """Count total runs in the database."""
