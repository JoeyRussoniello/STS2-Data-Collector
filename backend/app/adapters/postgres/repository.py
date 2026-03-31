"""Postgres implementation of the RunRepository port."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.postgres.models import RunRow
from app.domain.models import RunRecord
from app.domain.ports import RunRepository


class PostgresRunRepository(RunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, record: RunRecord) -> RunRecord:
        stmt = pg_insert(RunRow).values(
            run_id=record.run_id,
            steam_id_hash=record.steam_id_hash,
            profile=record.profile,
            file_name=record.file_name,
            file_size=record.file_size,
            data=record.data,
            uploaded_at=record.uploaded_at,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[RunRow.run_id],
            set_={
                "data": stmt.excluded.data,
                "file_size": stmt.excluded.file_size,
                "uploaded_at": stmt.excluded.uploaded_at,
            },
        )
        await self._session.execute(stmt)
        await self._session.commit()
        return record

    async def get_by_run_id(self, run_id: str) -> RunRecord | None:
        row = await self._session.get(RunRow, run_id)
        return _to_domain(row) if row else None

    async def get_by_steam_id_hash(
        self, steam_id_hash: str, *, limit: int = 50, offset: int = 0
    ) -> list[RunRecord]:
        stmt = (
            select(RunRow)
            .where(RunRow.steam_id_hash == steam_id_hash)
            .order_by(RunRow.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_to_domain(row) for row in result.scalars()]

    async def count_by_steam_id_hash(self, steam_id_hash: str) -> int:
        stmt = (
            select(func.count())
            .select_from(RunRow)
            .where(RunRow.steam_id_hash == steam_id_hash)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()


def _to_domain(row: RunRow) -> RunRecord:
    return RunRecord(
        run_id=row.run_id,
        steam_id_hash=row.steam_id_hash,
        profile=row.profile,
        file_name=row.file_name,
        file_size=row.file_size,
        data=row.data,
        uploaded_at=row.uploaded_at,
    )
