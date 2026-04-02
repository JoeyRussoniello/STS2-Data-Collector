"""Postgres implementation of the RunRepository port."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.postgres.models import (
    RunCardRow,
    RunDataRow,
    RunMapPointRow,
    RunPlayerRow,
    RunRelicRow,
    RunRow,
)
from app.domain.models import RunRecord
from app.domain.ports import RunRepository
from app.domain.runs import Card, MapPoint, ProcessedRun, Relic, RunData, RunPlayer


class PostgresRunRepository(RunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, record: RunRecord, processed_run: ProcessedRun) -> RunRecord:
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
            index_elements=["steam_id_hash", "profile", "file_name"],
            set_={
                "run_id": stmt.excluded.run_id,
                "data": stmt.excluded.data,
                "file_size": stmt.excluded.file_size,
                "uploaded_at": stmt.excluded.uploaded_at,
            },
        )
        await self._session.execute(stmt)

        # Replace normalized rows on every upload so re-uploads stay in sync.
        await self._session.execute(
            delete(RunMapPointRow).where(RunMapPointRow.run_id == record.run_id)
        )
        await self._session.execute(
            delete(RunDataRow).where(RunDataRow.run_id == record.run_id)
        )
        await self._session.execute(
            delete(RunPlayerRow).where(RunPlayerRow.run_id == record.run_id)
        )

        await self._session.execute(
            pg_insert(RunDataRow).values(
                run_id=processed_run.run_data.run_id,
                win=processed_run.run_data.win,
                acts=processed_run.run_data.acts,
                seed=processed_run.run_data.seed,
                build_id=processed_run.run_data.build_id,
                run_time=processed_run.run_data.run_time,
                ascension=processed_run.run_data.ascension,
                game_mode=processed_run.run_data.game_mode,
                modifiers=processed_run.run_data.modifiers,
                start_time=processed_run.run_data.start_time,
                was_abandoned=processed_run.run_data.was_abandoned,
                schema_version=processed_run.run_data.schema_version,
                platform_type=processed_run.run_data.platform_type,
                killed_by_event=processed_run.run_data.killed_by_event,
                killed_by_encounter=processed_run.run_data.killed_by_encounter,
            )
        )

        if processed_run.players:
            await self._session.execute(
                pg_insert(RunPlayerRow),
                [
                    {
                        "run_player_id": player.run_player_id,
                        "run_id": player.run_id,
                        "player_id": player.player_id,
                        "character": player.character,
                        "max_potion_slot_count": player.max_potion_slot_count,
                    }
                    for player in processed_run.players
                ],
            )

        if processed_run.cards:
            await self._session.execute(
                pg_insert(RunCardRow),
                [
                    {
                        "run_player_id": card.run_player_id,
                        "card_id": card.id,
                        "floor_added_to_deck": card.floor_added_to_deck,
                        "current_upgrade_level": card.current_upgrade_level,
                        "enchantment": (
                            card.enchantment.model_dump()
                            if card.enchantment is not None
                            else None
                        ),
                    }
                    for card in processed_run.cards
                ],
            )

        if processed_run.relics:
            await self._session.execute(
                pg_insert(RunRelicRow),
                [
                    {
                        "run_player_id": relic.run_player_id,
                        "relic_id": relic.id,
                        "floor_added_to_deck": relic.floor_added_to_deck,
                    }
                    for relic in processed_run.relics
                ],
            )

        if processed_run.map_points:
            await self._session.execute(
                pg_insert(RunMapPointRow),
                [
                    {
                        "run_id": map_point.run_id,
                        "map_point_index": map_point.map_point_index,
                        "map_point_type": map_point.map_point_type,
                        "raw": map_point.raw,
                    }
                    for map_point in processed_run.map_points
                ],
            )

        await self._session.commit()
        return record

    async def get_processed_by_run_id(self, run_id: str) -> ProcessedRun | None:
        run_data_row = await self._session.get(RunDataRow, run_id)
        if run_data_row is None:
            return None

        players_stmt = (
            select(RunPlayerRow)
            .where(RunPlayerRow.run_id == run_id)
            .order_by(RunPlayerRow.player_id.asc())
        )
        players_result = await self._session.execute(players_stmt)
        player_rows = list(players_result.scalars())

        run_player_ids = [row.run_player_id for row in player_rows]

        cards: list[Card] = []
        relics: list[Relic] = []
        if run_player_ids:
            cards_stmt = (
                select(RunCardRow)
                .where(RunCardRow.run_player_id.in_(run_player_ids))
                .order_by(RunCardRow.id.asc())
            )
            cards_result = await self._session.execute(cards_stmt)
            cards = [
                Card(
                    run_player_id=row.run_player_id,
                    id=row.card_id,
                    floor_added_to_deck=row.floor_added_to_deck,
                    current_upgrade_level=row.current_upgrade_level,
                    enchantment=row.enchantment,
                )
                for row in cards_result.scalars()
            ]

            relics_stmt = (
                select(RunRelicRow)
                .where(RunRelicRow.run_player_id.in_(run_player_ids))
                .order_by(RunRelicRow.id.asc())
            )
            relics_result = await self._session.execute(relics_stmt)
            relics = [
                Relic(
                    run_player_id=row.run_player_id,
                    id=row.relic_id,
                    floor_added_to_deck=row.floor_added_to_deck,
                )
                for row in relics_result.scalars()
            ]

        map_stmt = (
            select(RunMapPointRow)
            .where(RunMapPointRow.run_id == run_id)
            .order_by(RunMapPointRow.map_point_index.asc())
        )
        map_result = await self._session.execute(map_stmt)
        map_points = [
            MapPoint(
                run_id=row.run_id,
                map_point_index=row.map_point_index,
                map_point_type=row.map_point_type,
                raw=row.raw,
            )
            for row in map_result.scalars()
        ]

        return ProcessedRun(
            run_data=RunData(
                run_id=run_data_row.run_id,
                win=run_data_row.win,
                acts=run_data_row.acts,
                seed=run_data_row.seed,
                build_id=run_data_row.build_id,
                run_time=run_data_row.run_time,
                ascension=run_data_row.ascension,
                game_mode=run_data_row.game_mode,
                modifiers=run_data_row.modifiers,
                start_time=run_data_row.start_time,
                was_abandoned=run_data_row.was_abandoned,
                schema_version=run_data_row.schema_version,
                platform_type=run_data_row.platform_type,
                killed_by_event=run_data_row.killed_by_event,
                killed_by_encounter=run_data_row.killed_by_encounter,
            ),
            players=[
                RunPlayer(
                    run_id=row.run_id,
                    player_id=row.player_id,
                    character=row.character,
                    max_potion_slot_count=row.max_potion_slot_count,
                    run_player_id=row.run_player_id,
                )
                for row in player_rows
            ],
            cards=cards,
            relics=relics,
            map_points=map_points,
        )

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

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[RunRecord]:
        stmt = (
            select(RunRow)
            .order_by(RunRow.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_to_domain(row) for row in result.scalars()]

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(RunRow)
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
