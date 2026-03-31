"""Business logic — depends only on domain ports, never on adapters."""

from __future__ import annotations

from typing import Any

from app.domain.models import RunRecord, hash_steam_id
from app.domain.ports import RunRepository


class RunService:
    def __init__(self, repo: RunRepository, steam_id_salt: str) -> None:
        self._repo = repo
        self._salt = steam_id_salt

    async def upload_run(
        self,
        *,
        run_id: str,
        steam_id: str,
        profile: str,
        file_name: str,
        file_size: int,
        data: dict[str, Any],
    ) -> RunRecord:
        steam_id_hash = hash_steam_id(steam_id, self._salt)
        record = RunRecord(
            run_id=run_id,
            steam_id_hash=steam_id_hash,
            profile=profile,
            file_name=file_name,
            file_size=file_size,
            data=data,
        )
        return await self._repo.upsert(record)

    async def get_run(self, run_id: str) -> RunRecord | None:
        return await self._repo.get_by_run_id(run_id)

    async def get_runs_for_player(
        self, steam_id: str, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[RunRecord], int]:
        steam_id_hash = hash_steam_id(steam_id, self._salt)
        runs = await self._repo.get_by_steam_id_hash(
            steam_id_hash, limit=limit, offset=offset
        )
        total = await self._repo.count_by_steam_id_hash(steam_id_hash)
        return runs, total
