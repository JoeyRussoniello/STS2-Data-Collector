"""Postgres implementation of the StatsRepository port."""

from __future__ import annotations

from sqlalchemy import Integer, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.postgres.models import (
    RunCardRow,
    RunDataRow,
    RunPlayerRow,
    RunRelicRow,
    RunRow,
)
from app.domain.ports import StatsRepository


def _apply_steam_filter(stmt, steam_id_hash: str | None):
    """Join to runs table and filter by steam_id_hash if provided."""
    if steam_id_hash is not None:
        stmt = stmt.join(RunRow, RunDataRow.run_id == RunRow.run_id).where(
            RunRow.steam_id_hash == steam_id_hash
        )
    return stmt


def _apply_common_filters(stmt, *, ascension: int | None, game_mode: str | None = None):
    if ascension is not None:
        stmt = stmt.where(RunDataRow.ascension == ascension)
    if game_mode is not None:
        stmt = stmt.where(RunDataRow.game_mode == game_mode)
    return stmt


def _apply_character_filter(
    stmt, character: str | None, *, player_joined: bool = False
):
    """Filter by character, joining run_players if not already joined."""
    if character is not None:
        if not player_joined:
            stmt = stmt.join(RunPlayerRow, RunDataRow.run_id == RunPlayerRow.run_id)
        stmt = stmt.where(RunPlayerRow.character == character)
    return stmt


class PostgresStatsRepository(StatsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_overview(self, *, steam_id_hash: str | None = None) -> dict:
        base = select(
            func.count().label("run_count"),
            func.sum(cast(RunDataRow.win, Integer)).label("win_count"),
            func.sum(cast(RunDataRow.was_abandoned, Integer)).label("abandon_count"),
            func.avg(RunDataRow.run_time).label("avg_run_time"),
            func.avg(RunDataRow.ascension).label("avg_ascension"),
            func.avg(func.jsonb_array_length(RunDataRow.acts)).label("avg_acts"),
        ).select_from(RunDataRow)
        base = _apply_steam_filter(base, steam_id_hash)

        result = await self._session.execute(base)
        row = result.one()

        run_count = row.run_count or 0
        win_count = row.win_count or 0
        abandon_count = row.abandon_count or 0

        # Character breakdown
        char_stmt = (
            select(
                RunPlayerRow.character,
                func.count(func.distinct(RunPlayerRow.run_id)).label("run_count"),
                func.sum(cast(RunDataRow.win, Integer)).label("win_count"),
            )
            .select_from(RunPlayerRow)
            .join(RunDataRow, RunPlayerRow.run_id == RunDataRow.run_id)
        )
        if steam_id_hash is not None:
            char_stmt = char_stmt.join(
                RunRow, RunDataRow.run_id == RunRow.run_id
            ).where(RunRow.steam_id_hash == steam_id_hash)
        char_stmt = char_stmt.group_by(RunPlayerRow.character)
        char_result = await self._session.execute(char_stmt)

        characters = []
        for cr in char_result:
            c_total = cr.run_count or 0
            c_wins = cr.win_count or 0
            characters.append(
                {
                    "character": cr.character,
                    "run_count": c_total,
                    "win_count": c_wins,
                    "win_rate": round(c_wins / c_total, 4) if c_total > 0 else 0.0,
                }
            )

        return {
            "run_count": run_count,
            "win_count": win_count,
            "win_rate": round(win_count / run_count, 4) if run_count > 0 else 0.0,
            "abandon_rate": round(abandon_count / run_count, 4)
            if run_count > 0
            else 0.0,
            "avg_run_time_seconds": round(float(row.avg_run_time or 0), 2),
            "avg_ascension": round(float(row.avg_ascension or 0), 2),
            "avg_acts_cleared": round(float(row.avg_acts or 0), 2),
            "characters": characters,
        }

    async def get_characters(
        self,
        *,
        steam_id_hash: str | None = None,
        ascension: int | None = None,
        game_mode: str | None = None,
    ) -> list[dict]:
        # Subquery: deck size per run_player
        deck_size_sq = (
            select(
                RunCardRow.run_player_id,
                func.count().label("deck_size"),
            )
            .group_by(RunCardRow.run_player_id)
            .subquery()
        )

        # Subquery: relic count per run_player
        relic_count_sq = (
            select(
                RunRelicRow.run_player_id,
                func.count().label("relic_count"),
            )
            .group_by(RunRelicRow.run_player_id)
            .subquery()
        )

        stmt = (
            select(
                RunPlayerRow.character,
                func.count(func.distinct(RunPlayerRow.run_id)).label("run_count"),
                func.sum(cast(RunDataRow.win, Integer)).label("win_count"),
                func.avg(RunDataRow.run_time).label("avg_run_time"),
                func.avg(func.coalesce(deck_size_sq.c.deck_size, 0)).label(
                    "avg_deck_size"
                ),
                func.avg(func.coalesce(relic_count_sq.c.relic_count, 0)).label(
                    "avg_relic_count"
                ),
            )
            .select_from(RunPlayerRow)
            .join(RunDataRow, RunPlayerRow.run_id == RunDataRow.run_id)
            .outerjoin(
                deck_size_sq,
                RunPlayerRow.run_player_id == deck_size_sq.c.run_player_id,
            )
            .outerjoin(
                relic_count_sq,
                RunPlayerRow.run_player_id == relic_count_sq.c.run_player_id,
            )
        )

        if steam_id_hash is not None:
            stmt = stmt.join(RunRow, RunDataRow.run_id == RunRow.run_id).where(
                RunRow.steam_id_hash == steam_id_hash
            )

        stmt = _apply_common_filters(stmt, ascension=ascension, game_mode=game_mode)
        stmt = stmt.group_by(RunPlayerRow.character)

        result = await self._session.execute(stmt)
        rows = []
        for r in result:
            total = r.run_count or 0
            wins = r.win_count or 0
            rows.append(
                {
                    "character": r.character,
                    "run_count": total,
                    "win_count": wins,
                    "win_rate": round(wins / total, 4) if total > 0 else 0.0,
                    "avg_run_time_seconds": round(float(r.avg_run_time or 0), 2),
                    "avg_deck_size": round(float(r.avg_deck_size or 0), 2),
                    "avg_relic_count": round(float(r.avg_relic_count or 0), 2),
                }
            )
        return rows

    async def get_cards(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
        min_appearances: int = 5,
    ) -> list[dict]:
        # How many distinct runs each card appears in, and win rate
        # A "run" for a card = distinct run_player_id's run_id
        stmt = (
            select(
                RunCardRow.card_id,
                # Number of distinct runs where this card is present
                func.count(func.distinct(RunPlayerRow.run_id)).label("times_in_deck"),
                # Total copies across all run-decks
                func.count().label("total_copies"),
                func.avg(RunCardRow.floor_added_to_deck).label("avg_floor_added"),
                func.avg(RunCardRow.current_upgrade_level).label("avg_upgrade_level"),
                func.sum(cast(RunDataRow.win, Integer)).label("win_copies"),
            )
            .select_from(RunCardRow)
            .join(RunPlayerRow, RunCardRow.run_player_id == RunPlayerRow.run_player_id)
            .join(RunDataRow, RunPlayerRow.run_id == RunDataRow.run_id)
        )

        if steam_id_hash is not None:
            stmt = stmt.join(RunRow, RunDataRow.run_id == RunRow.run_id).where(
                RunRow.steam_id_hash == steam_id_hash
            )

        if character is not None:
            stmt = stmt.where(RunPlayerRow.character == character)

        if ascension is not None:
            stmt = stmt.where(RunDataRow.ascension == ascension)

        stmt = stmt.group_by(RunCardRow.card_id).having(
            func.count(func.distinct(RunPlayerRow.run_id)) >= min_appearances
        )

        result = await self._session.execute(stmt)
        rows = []
        for r in result:
            times = r.times_in_deck or 0
            # win_copies counts card copies in winning runs; divide by total
            # copies to approximate win rate when present
            # More accurate: count distinct winning runs vs total runs
            # We'll use a subquery approach for accuracy
            rows.append(
                {
                    "card_id": r.card_id,
                    "times_in_deck": times,
                    "avg_copies_per_deck": round((r.total_copies or 0) / times, 2)
                    if times > 0
                    else 0.0,
                    "avg_floor_added": round(float(r.avg_floor_added or 0), 2),
                    "avg_upgrade_level": (
                        round(float(r.avg_upgrade_level), 2)
                        if r.avg_upgrade_level is not None
                        else None
                    ),
                }
            )

        # Compute accurate win_rate_when_present with a second pass
        # Count distinct winning runs per card vs total distinct runs per card
        win_stmt = (
            select(
                RunCardRow.card_id,
                func.count(func.distinct(RunPlayerRow.run_id)).label("total_runs"),
                func.count(
                    func.distinct(
                        case(
                            (RunDataRow.win.is_(True), RunPlayerRow.run_id),
                            else_=None,
                        )
                    )
                ).label("winning_runs"),
            )
            .select_from(RunCardRow)
            .join(RunPlayerRow, RunCardRow.run_player_id == RunPlayerRow.run_player_id)
            .join(RunDataRow, RunPlayerRow.run_id == RunDataRow.run_id)
        )
        if steam_id_hash is not None:
            win_stmt = win_stmt.join(RunRow, RunDataRow.run_id == RunRow.run_id).where(
                RunRow.steam_id_hash == steam_id_hash
            )
        if character is not None:
            win_stmt = win_stmt.where(RunPlayerRow.character == character)
        if ascension is not None:
            win_stmt = win_stmt.where(RunDataRow.ascension == ascension)
        win_stmt = win_stmt.group_by(RunCardRow.card_id).having(
            func.count(func.distinct(RunPlayerRow.run_id)) >= min_appearances
        )

        win_result = await self._session.execute(win_stmt)
        win_rates = {}
        for wr in win_result:
            total = wr.total_runs or 0
            wins = wr.winning_runs or 0
            win_rates[wr.card_id] = round(wins / total, 4) if total > 0 else 0.0

        for row in rows:
            row["win_rate_when_present"] = win_rates.get(row["card_id"], 0.0)

        return rows

    async def get_relics(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
        min_appearances: int = 5,
    ) -> list[dict]:
        # Win rate per relic (distinct runs)
        stmt = (
            select(
                RunRelicRow.relic_id,
                func.count(func.distinct(RunPlayerRow.run_id)).label("times_present"),
                func.avg(RunRelicRow.floor_added_to_deck).label("avg_floor_acquired"),
                func.count(
                    func.distinct(
                        case(
                            (RunDataRow.win.is_(True), RunPlayerRow.run_id),
                            else_=None,
                        )
                    )
                ).label("winning_runs"),
            )
            .select_from(RunRelicRow)
            .join(RunPlayerRow, RunRelicRow.run_player_id == RunPlayerRow.run_player_id)
            .join(RunDataRow, RunPlayerRow.run_id == RunDataRow.run_id)
        )

        if steam_id_hash is not None:
            stmt = stmt.join(RunRow, RunDataRow.run_id == RunRow.run_id).where(
                RunRow.steam_id_hash == steam_id_hash
            )
        if character is not None:
            stmt = stmt.where(RunPlayerRow.character == character)
        if ascension is not None:
            stmt = stmt.where(RunDataRow.ascension == ascension)

        stmt = stmt.group_by(RunRelicRow.relic_id).having(
            func.count(func.distinct(RunPlayerRow.run_id)) >= min_appearances
        )

        result = await self._session.execute(stmt)
        relic_ids = []
        relic_map = {}
        for r in result:
            total = r.times_present or 0
            wins = r.winning_runs or 0
            entry = {
                "relic_id": r.relic_id,
                "times_present": total,
                "win_rate_when_present": round(wins / total, 4) if total > 0 else 0.0,
                "avg_floor_acquired": round(float(r.avg_floor_acquired or 0), 2),
                "characters": [],
            }
            relic_ids.append(r.relic_id)
            relic_map[r.relic_id] = entry

        # Character distribution per relic
        if relic_ids:
            char_stmt = (
                select(
                    RunRelicRow.relic_id,
                    RunPlayerRow.character,
                    func.count(func.distinct(RunPlayerRow.run_id)).label("count"),
                )
                .select_from(RunRelicRow)
                .join(
                    RunPlayerRow,
                    RunRelicRow.run_player_id == RunPlayerRow.run_player_id,
                )
                .join(RunDataRow, RunPlayerRow.run_id == RunDataRow.run_id)
                .where(RunRelicRow.relic_id.in_(relic_ids))
            )
            if steam_id_hash is not None:
                char_stmt = char_stmt.join(
                    RunRow, RunDataRow.run_id == RunRow.run_id
                ).where(RunRow.steam_id_hash == steam_id_hash)
            if ascension is not None:
                char_stmt = char_stmt.where(RunDataRow.ascension == ascension)
            char_stmt = char_stmt.group_by(RunRelicRow.relic_id, RunPlayerRow.character)

            char_result = await self._session.execute(char_stmt)
            for cr in char_result:
                if cr.relic_id in relic_map:
                    relic_map[cr.relic_id]["characters"].append(
                        {"character": cr.character, "count": cr.count}
                    )

        return list(relic_map.values())

    async def get_run_outcomes(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> dict:
        base = select(
            func.count().label("total"),
            func.sum(cast(RunDataRow.win, Integer)).label("wins"),
            func.sum(cast(RunDataRow.was_abandoned, Integer)).label("abandoned"),
        ).select_from(RunDataRow)
        base = _apply_steam_filter(base, steam_id_hash)
        base = _apply_character_filter(base, character)
        if ascension is not None:
            base = base.where(RunDataRow.ascension == ascension)

        result = await self._session.execute(base)
        row = result.one()
        total = row.total or 0
        wins = row.wins or 0
        abandoned = row.abandoned or 0
        losses = total - wins - abandoned

        # killed_by_encounter
        enc_stmt = (
            select(
                RunDataRow.killed_by_encounter,
                func.count().label("count"),
            )
            .select_from(RunDataRow)
            .where(RunDataRow.killed_by_encounter.isnot(None))
        )
        enc_stmt = _apply_steam_filter(enc_stmt, steam_id_hash)
        enc_stmt = _apply_character_filter(enc_stmt, character)
        if ascension is not None:
            enc_stmt = enc_stmt.where(RunDataRow.ascension == ascension)
        enc_stmt = enc_stmt.group_by(RunDataRow.killed_by_encounter).order_by(
            func.count().desc()
        )

        enc_result = await self._session.execute(enc_stmt)
        death_total_enc = losses  # non-abandoned, non-win
        killed_by_encounter = [
            {
                "name": r.killed_by_encounter,
                "count": r.count,
                "share": round(r.count / death_total_enc, 4)
                if death_total_enc > 0
                else 0.0,
            }
            for r in enc_result
        ]

        # killed_by_event
        evt_stmt = (
            select(
                RunDataRow.killed_by_event,
                func.count().label("count"),
            )
            .select_from(RunDataRow)
            .where(RunDataRow.killed_by_event.isnot(None))
        )
        evt_stmt = _apply_steam_filter(evt_stmt, steam_id_hash)
        evt_stmt = _apply_character_filter(evt_stmt, character)
        if ascension is not None:
            evt_stmt = evt_stmt.where(RunDataRow.ascension == ascension)
        evt_stmt = evt_stmt.group_by(RunDataRow.killed_by_event).order_by(
            func.count().desc()
        )

        evt_result = await self._session.execute(evt_stmt)
        killed_by_event = [
            {
                "name": r.killed_by_event,
                "count": r.count,
                "share": round(r.count / death_total_enc, 4)
                if death_total_enc > 0
                else 0.0,
            }
            for r in evt_result
        ]

        # acts_reached distribution (grouped by the acts JSON array)
        acts_stmt = select(
            RunDataRow.acts,
            func.count().label("count"),
        ).select_from(RunDataRow)
        acts_stmt = _apply_steam_filter(acts_stmt, steam_id_hash)
        acts_stmt = _apply_character_filter(acts_stmt, character)
        if ascension is not None:
            acts_stmt = acts_stmt.where(RunDataRow.ascension == ascension)
        acts_stmt = acts_stmt.group_by(RunDataRow.acts).order_by(func.count().desc())

        acts_result = await self._session.execute(acts_stmt)
        acts_reached = [{"acts": r.acts, "count": r.count} for r in acts_result]

        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "abandoned": abandoned,
            "win_rate": round(wins / total, 4) if total > 0 else 0.0,
            "killed_by_encounter": killed_by_encounter,
            "killed_by_event": killed_by_event,
            "acts_reached": acts_reached,
        }

    async def get_encounters(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> list[dict]:
        # Deaths by encounter (non-null killed_by_encounter)
        stmt = (
            select(
                RunDataRow.killed_by_encounter,
                func.count().label("kill_count"),
            )
            .select_from(RunDataRow)
            .where(RunDataRow.killed_by_encounter.isnot(None))
        )
        stmt = _apply_steam_filter(stmt, steam_id_hash)
        stmt = _apply_character_filter(stmt, character)
        if ascension is not None:
            stmt = stmt.where(RunDataRow.ascension == ascension)
        stmt = stmt.group_by(RunDataRow.killed_by_encounter).order_by(
            func.count().desc()
        )

        result = await self._session.execute(stmt)
        encounters_raw = list(result)
        total_kills = sum(r.kill_count for r in encounters_raw)

        encounter_names = [r.killed_by_encounter for r in encounters_raw]
        encounter_map = {
            r.killed_by_encounter: {
                "encounter": r.killed_by_encounter,
                "kill_count": r.kill_count,
                "kill_share": round(r.kill_count / total_kills, 4)
                if total_kills > 0
                else 0.0,
                "characters": [],
            }
            for r in encounters_raw
        }

        # Character breakdown per encounter
        if encounter_names:
            char_stmt = (
                select(
                    RunDataRow.killed_by_encounter,
                    RunPlayerRow.character,
                    func.count().label("kill_count"),
                )
                .select_from(RunDataRow)
                .join(RunPlayerRow, RunDataRow.run_id == RunPlayerRow.run_id)
                .where(RunDataRow.killed_by_encounter.in_(encounter_names))
            )
            if steam_id_hash is not None:
                char_stmt = char_stmt.join(
                    RunRow, RunDataRow.run_id == RunRow.run_id
                ).where(RunRow.steam_id_hash == steam_id_hash)
            if ascension is not None:
                char_stmt = char_stmt.where(RunDataRow.ascension == ascension)
            char_stmt = char_stmt.group_by(
                RunDataRow.killed_by_encounter, RunPlayerRow.character
            ).order_by(func.count().desc())

            char_result = await self._session.execute(char_stmt)
            for cr in char_result:
                if cr.killed_by_encounter in encounter_map:
                    encounter_map[cr.killed_by_encounter]["characters"].append(
                        {"character": cr.character, "kill_count": cr.kill_count}
                    )

        return list(encounter_map.values())

    async def get_deck_growth(
        self,
        *,
        steam_id_hash: str | None = None,
        character: str | None = None,
        ascension: int | None = None,
    ) -> list[dict]:
        # Cards added per floor, with upgrade info
        stmt = (
            select(
                RunCardRow.floor_added_to_deck.label("floor"),
                func.count().label("cards_added"),
                func.sum(
                    case(
                        (
                            RunCardRow.current_upgrade_level.isnot(None)
                            & (RunCardRow.current_upgrade_level > 0),
                            1,
                        ),
                        else_=0,
                    )
                ).label("upgrades_at_floor"),
                func.count(func.distinct(RunPlayerRow.run_id)).label("run_count"),
            )
            .select_from(RunCardRow)
            .join(RunPlayerRow, RunCardRow.run_player_id == RunPlayerRow.run_player_id)
            .join(RunDataRow, RunPlayerRow.run_id == RunDataRow.run_id)
        )

        if steam_id_hash is not None:
            stmt = stmt.join(RunRow, RunDataRow.run_id == RunRow.run_id).where(
                RunRow.steam_id_hash == steam_id_hash
            )
        if character is not None:
            stmt = stmt.where(RunPlayerRow.character == character)
        if ascension is not None:
            stmt = stmt.where(RunDataRow.ascension == ascension)

        stmt = stmt.group_by(RunCardRow.floor_added_to_deck).order_by(
            RunCardRow.floor_added_to_deck.asc()
        )

        result = await self._session.execute(stmt)
        raw_floors = list(result)

        # Compute cumulative avg deck size per floor
        # total cards at floor N = sum of cards_added for floors 0..N
        # avg deck size = cumulative_cards / run_count at that floor
        cumulative_cards = 0
        entries = []
        for r in raw_floors:
            cumulative_cards += r.cards_added
            run_count = r.run_count or 1
            entries.append(
                {
                    "floor": r.floor,
                    "avg_deck_size": round(cumulative_cards / run_count, 2),
                    "cards_added": r.cards_added,
                    "upgrades_at_floor": r.upgrades_at_floor or 0,
                }
            )
        return entries
