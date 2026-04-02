"""Abstract repository interfaces (ports) for run and stats storage."""

from __future__ import annotations

import abc

from app.domain.models import RunRecord
from app.domain.runs import ProcessedRun


class RunRepository(abc.ABC):
    @abc.abstractmethod
    async def upsert(self, record: RunRecord, processed_run: ProcessedRun) -> RunRecord:
        """Insert or update a run record. Returns the persisted record."""

    @abc.abstractmethod
    async def get_processed_by_run_id(self, run_id: str) -> ProcessedRun | None:
        """Fetch normalized records for one run, or None if missing."""

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
    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[RunRecord]:
        """Fetch all runs, newest first."""

    @abc.abstractmethod
    async def count_all(self) -> int:
        """Count total runs in the database."""


class StatsRepository(abc.ABC):
    """Port for aggregate statistics queries against normalized tables."""

    @abc.abstractmethod
    async def get_overview(
        self,
        *,
        steam_id_hash: str | None = None,
    ) -> dict:
        """Dashboard summary: counts, rates, averages, character breakdown."""

    @abc.abstractmethod
    async def get_characters(
        self,
        *,
        steam_id_hash: str | None = None,
        ascension: int | None = None,
        game_mode: str | None = None,
    ) -> list[dict]:
        """Per-character performance metrics."""

    @abc.abstractmethod
    async def get_cards(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
        min_appearances: int = 5,
    ) -> list[dict]:
        """Per-card acquisition and win-rate metrics."""

    @abc.abstractmethod
    async def get_relics(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
        min_appearances: int = 5,
    ) -> list[dict]:
        """Per-relic acquisition and win-rate metrics."""

    @abc.abstractmethod
    async def get_run_outcomes(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> dict:
        """Run outcome distribution: wins, losses, killed_by breakdowns."""

    @abc.abstractmethod
    async def get_encounters(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> list[dict]:
        """Per-encounter kill stats from killed_by_encounter."""

    @abc.abstractmethod
    async def get_deck_growth(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> list[dict]:
        """Deck size progression by floor."""
