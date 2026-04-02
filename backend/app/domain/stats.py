"""Stats business logic depends only on domain ports, never on adapters."""

# NOTE: Lots of signature duplication between StatsService and StatsRepository.
# This design decision may be re-evaluated if it becomes a burden

from __future__ import annotations

import logging

from app.domain.models import hash_steam_id
from app.domain.ports import StatsRepository

logger = logging.getLogger("sts2.stats")


class StatsService:
    def __init__(self, repo: StatsRepository, steam_id_salt: str) -> None:
        self._repo = repo
        self._salt = steam_id_salt

    def _hash_optional(self, steam_id: str | None) -> str | None:
        if steam_id is None:
            return None
        return hash_steam_id(steam_id, self._salt)

    async def get_overview(
        self,
        *,
        steam_id: str | None = None,
    ) -> dict:
        return await self._repo.get_overview(
            steam_id_hash=self._hash_optional(steam_id),
        )

    async def get_characters(
        self,
        *,
        steam_id: str | None = None,
        ascension: int | None = None,
        game_mode: str | None = None,
    ) -> list[dict]:
        return await self._repo.get_characters(
            steam_id_hash=self._hash_optional(steam_id),
            ascension=ascension,
            game_mode=game_mode,
        )

    async def get_cards(
        self,
        *,
        steam_id: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
        min_appearances: int = 5,
    ) -> list[dict]:
        return await self._repo.get_cards(
            steam_id_hash=self._hash_optional(steam_id),
            character=character,
            ascension=ascension,
            min_appearances=min_appearances,
        )

    async def get_relics(
        self,
        *,
        steam_id: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
        min_appearances: int = 5,
    ) -> list[dict]:
        return await self._repo.get_relics(
            steam_id_hash=self._hash_optional(steam_id),
            character=character,
            ascension=ascension,
            min_appearances=min_appearances,
        )

    async def get_run_outcomes(
        self,
        *,
        steam_id: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> dict:
        return await self._repo.get_run_outcomes(
            steam_id_hash=self._hash_optional(steam_id),
            character=character,
            ascension=ascension,
        )

    async def get_encounters(
        self,
        *,
        steam_id: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> list[dict]:
        return await self._repo.get_encounters(
            steam_id_hash=self._hash_optional(steam_id),
            character=character,
            ascension=ascension,
        )

    async def get_deck_growth(
        self,
        *,
        steam_id: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> list[dict]:
        return await self._repo.get_deck_growth(
            steam_id_hash=self._hash_optional(steam_id),
            character=character,
            ascension=ascension,
        )
