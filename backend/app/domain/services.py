"""Business logic — depends only on domain ports, never on adapters."""

from __future__ import annotations

import logging
from typing import Any

from app.domain.models import RunRecord, hash_steam_id
from app.domain.ports import RunRepository
from app.domain.runs import ProcessedRun, process_run

logger = logging.getLogger("sts2.service")


class RunService:
    def __init__(self, repo: RunRepository, steam_id_salt: str) -> None:
        self._repo = repo
        self._salt = steam_id_salt

    async def upload_run(
        self,
        *,
        steam_id: str,
        profile: str,
        file_name: str,
        file_size: int,
        data: dict[str, Any],
    ) -> RunRecord:
        steam_id_hash = hash_steam_id(steam_id, self._salt)
        run_id = f"{steam_id_hash}:{profile}:{file_name}"
        processed = process_run({"run_id": run_id, "data": data})
        record = RunRecord(
            run_id=run_id,
            steam_id_hash=steam_id_hash,
            profile=profile,
            file_name=file_name,
            file_size=file_size,
            data=data,
        )
        return await self._repo.upsert(record, processed)

    async def get_run(self, run_id: str) -> RunRecord | None:
        record = await self._repo.get_by_run_id(run_id)
        if record is None:
            logger.debug("Run not found: %s", run_id)
        return record

    async def get_processed_run(self, run_id: str) -> ProcessedRun | None:
        record = await self._repo.get_processed_by_run_id(run_id)
        if record is None:
            logger.debug("Processed run not found: %s", run_id)
        return record

    async def get_runs_for_player(
        self, steam_id: str, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[RunRecord], int]:
        steam_id_hash = hash_steam_id(steam_id, self._salt)
        runs = await self._repo.get_by_steam_id_hash(
            steam_id_hash, limit=limit, offset=offset
        )
        total = await self._repo.count_by_steam_id_hash(steam_id_hash)
        return runs, total

    async def list_runs(
        self, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[RunRecord], int]:
        runs = await self._repo.list_all(limit=limit, offset=offset)
        total = await self._repo.count_all()
        return runs, total
