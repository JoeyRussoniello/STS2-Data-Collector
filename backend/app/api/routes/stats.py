"""Public statistics API — no authentication required."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_stats_service
from app.api.schemas import (
    ActsReachedEntry,
    CardStatsResponse,
    CharacterBreakdown,
    CharacterDistribution,
    CharacterStatsResponse,
    DeckGrowthEntry,
    EncounterCharacterBreakdown,
    EncounterStatsResponse,
    KilledByEntry,
    OverviewResponse,
    RelicStatsResponse,
    RunOutcomesResponse,
)
from app.domain.stats import StatsService

router = APIRouter(prefix="/api/stats", tags=["public-statistics"])

limiter = Limiter(key_func=get_remote_address)


@router.get("/overview")
@limiter.limit("30/minute")
async def get_overview(
    request: Request,
    steam_id: str | None = Query(
        default=None, description="Raw Steam ID to scope stats to a single player"
    ),
    svc: StatsService = Depends(get_stats_service),
) -> OverviewResponse:
    """Dashboard summary: counts, rates, averages, and character breakdown."""
    data = await svc.get_overview(steam_id=steam_id)
    return OverviewResponse(
        run_count=data["run_count"],
        win_count=data["win_count"],
        win_rate=data["win_rate"],
        abandon_rate=data["abandon_rate"],
        avg_run_time_seconds=data["avg_run_time_seconds"],
        avg_ascension=data["avg_ascension"],
        avg_acts_cleared=data["avg_acts_cleared"],
        characters=[CharacterBreakdown(**c) for c in data["characters"]],
    )


@router.get("/characters")
@limiter.limit("30/minute")
async def get_characters(
    request: Request,
    steam_id: str | None = Query(
        default=None, description="Raw Steam ID to scope stats to a single player"
    ),
    ascension: int | None = Query(
        default=None, ge=0, description="Filter by ascension level"
    ),
    game_mode: str | None = Query(default=None, description="Filter by game mode"),
    svc: StatsService = Depends(get_stats_service),
) -> list[CharacterStatsResponse]:
    """Per-character performance: win rate, avg run time, deck/relic size."""
    rows = await svc.get_characters(
        steam_id=steam_id,
        ascension=ascension,
        game_mode=game_mode,
    )
    return [CharacterStatsResponse(**r) for r in rows]


@router.get("/cards")
@limiter.limit("30/minute")
async def get_cards(
    request: Request,
    steam_id: str | None = Query(
        default=None, description="Raw Steam ID to scope stats to a single player"
    ),
    character: str | None = Query(default=None, description="Filter by character"),
    ascension: int | None = Query(
        default=None, ge=0, description="Filter by ascension level"
    ),
    min_appearances: int = Query(
        default=5, ge=1, description="Minimum runs a card must appear in"
    ),
    svc: StatsService = Depends(get_stats_service),
) -> list[CardStatsResponse]:
    """Per-card metrics: win rate when present, avg copies, floor added."""
    rows = await svc.get_cards(
        steam_id=steam_id,
        character=character,
        ascension=ascension,
        min_appearances=min_appearances,
    )
    return [CardStatsResponse(**r) for r in rows]


@router.get("/relics")
@limiter.limit("30/minute")
async def get_relics(
    request: Request,
    steam_id: str | None = Query(
        default=None, description="Raw Steam ID to scope stats to a single player"
    ),
    character: str | None = Query(default=None, description="Filter by character"),
    ascension: int | None = Query(
        default=None, ge=0, description="Filter by ascension level"
    ),
    min_appearances: int = Query(
        default=5, ge=1, description="Minimum runs a relic must appear in"
    ),
    svc: StatsService = Depends(get_stats_service),
) -> list[RelicStatsResponse]:
    """Per-relic metrics: win rate when present, floor acquired, character distribution."""
    rows = await svc.get_relics(
        steam_id=steam_id,
        character=character,
        ascension=ascension,
        min_appearances=min_appearances,
    )
    return [
        RelicStatsResponse(
            relic_id=r["relic_id"],
            times_present=r["times_present"],
            win_rate_when_present=r["win_rate_when_present"],
            avg_floor_acquired=r["avg_floor_acquired"],
            characters=[CharacterDistribution(**c) for c in r["characters"]],
        )
        for r in rows
    ]


@router.get("/runs/outcomes")
@limiter.limit("30/minute")
async def get_run_outcomes(
    request: Request,
    steam_id: str | None = Query(
        default=None, description="Raw Steam ID to scope stats to a single player"
    ),
    character: str | None = Query(default=None, description="Filter by character"),
    ascension: int | None = Query(
        default=None, ge=0, description="Filter by ascension level"
    ),
    svc: StatsService = Depends(get_stats_service),
) -> RunOutcomesResponse:
    """Run outcome distribution: wins, losses, abandoned, killed-by leaderboards."""
    data = await svc.get_run_outcomes(
        steam_id=steam_id,
        character=character,
        ascension=ascension,
    )
    return RunOutcomesResponse(
        total=data["total"],
        wins=data["wins"],
        losses=data["losses"],
        abandoned=data["abandoned"],
        win_rate=data["win_rate"],
        killed_by_encounter=[KilledByEntry(**e) for e in data["killed_by_encounter"]],
        killed_by_event=[KilledByEntry(**e) for e in data["killed_by_event"]],
        acts_reached=[ActsReachedEntry(**a) for a in data["acts_reached"]],
    )


@router.get("/encounters")
@limiter.limit("30/minute")
async def get_encounters(
    request: Request,
    steam_id: str | None = Query(
        default=None, description="Raw Steam ID to scope stats to a single player"
    ),
    character: str | None = Query(default=None, description="Filter by character"),
    ascension: int | None = Query(
        default=None, ge=0, description="Filter by ascension level"
    ),
    svc: StatsService = Depends(get_stats_service),
) -> list[EncounterStatsResponse]:
    """Per-encounter kill stats with character breakdown."""
    rows = await svc.get_encounters(
        steam_id=steam_id,
        character=character,
        ascension=ascension,
    )
    return [
        EncounterStatsResponse(
            encounter=r["encounter"],
            kill_count=r["kill_count"],
            kill_share=r["kill_share"],
            characters=[EncounterCharacterBreakdown(**c) for c in r["characters"]],
        )
        for r in rows
    ]


@router.get("/deck/growth")
@limiter.limit("30/minute")
async def get_deck_growth(
    request: Request,
    steam_id: str | None = Query(
        default=None, description="Raw Steam ID to scope stats to a single player"
    ),
    character: str | None = Query(default=None, description="Filter by character"),
    ascension: int | None = Query(
        default=None, ge=0, description="Filter by ascension level"
    ),
    svc: StatsService = Depends(get_stats_service),
) -> list[DeckGrowthEntry]:
    """Deck size progression by floor: avg deck size, cards added, upgrades."""
    rows = await svc.get_deck_growth(
        steam_id=steam_id,
        character=character,
        ascension=ascension,
    )
    return [DeckGrowthEntry(**r) for r in rows]
