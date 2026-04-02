"""Request/response schemas — decoupled from domain and ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

REQUIRED_RUN_KEYS = {
    "run_time",
    "schema_version",
    "seed",
    "start_time",
    "was_abandoned",
    "win",
    "acts",
    "ascension",
    "build_id",
    "game_mode",
    "killed_by_encounter",
    "killed_by_event",
    "map_point_history",
    "players",
}


class RunUploadRequest(BaseModel):
    steam_id: str = Field(..., min_length=1)
    profile: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    file_size: int = Field(..., ge=0)
    data: dict[str, Any]

    @field_validator("data")
    @classmethod
    def validate_run_data_keys(cls, v: dict[str, Any]) -> dict[str, Any]:
        missing = REQUIRED_RUN_KEYS - v.keys()
        if missing:
            raise ValueError(f"Missing required .run data keys: {sorted(missing)}")
        return v


# * Responses
class RunResponse(BaseModel):
    run_id: str
    steam_id_hash: str
    profile: str
    file_name: str
    file_size: int
    data: dict[str, Any]
    uploaded_at: datetime


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int
    limit: int
    offset: int


class RunDataResponse(BaseModel):
    run_id: str
    win: bool
    acts: list[str]
    seed: str
    build_id: str
    run_time: int
    ascension: int
    game_mode: str
    modifiers: list[str]
    start_time: int
    was_abandoned: bool
    schema_version: int
    platform_type: str | None
    killed_by_event: str | None
    killed_by_encounter: str | None


class RunPlayerResponse(BaseModel):
    run_id: str
    player_id: int
    character: str
    max_potion_slot_count: int
    run_player_id: str


class CardResponse(BaseModel):
    run_player_id: str
    id: str
    floor_added_to_deck: int
    current_upgrade_level: int | None
    enchantment: dict[str, Any] | None


class RelicResponse(BaseModel):
    run_player_id: str
    id: str
    floor_added_to_deck: int


class MapPointResponse(BaseModel):
    run_id: str
    map_point_index: int
    map_point_type: str
    raw: dict[str, Any]


class ProcessedRunResponse(BaseModel):
    run_data: RunDataResponse
    players: list[RunPlayerResponse]
    cards: list[CardResponse]
    relics: list[RelicResponse]
    map_points: list[MapPointResponse]


# ---------------------------------------------------------------------------
# Stats response schemas
# ---------------------------------------------------------------------------


class CharacterBreakdown(BaseModel):
    character: str
    run_count: int
    win_count: int
    win_rate: float


class OverviewResponse(BaseModel):
    run_count: int
    win_count: int
    win_rate: float
    abandon_rate: float
    avg_run_time_seconds: float
    avg_ascension: float
    avg_acts_cleared: float
    characters: list[CharacterBreakdown]


class CharacterStatsResponse(BaseModel):
    character: str
    run_count: int
    win_count: int
    win_rate: float
    avg_run_time_seconds: float
    avg_deck_size: float
    avg_relic_count: float


class CardStatsResponse(BaseModel):
    card_id: str
    times_in_deck: int
    win_rate_when_present: float
    avg_copies_per_deck: float
    avg_floor_added: float
    avg_upgrade_level: float | None


class CharacterDistribution(BaseModel):
    character: str
    count: int


class RelicStatsResponse(BaseModel):
    relic_id: str
    times_present: int
    win_rate_when_present: float
    avg_floor_acquired: float
    characters: list[CharacterDistribution]


class KilledByEntry(BaseModel):
    name: str
    count: int
    share: float


class ActsReachedEntry(BaseModel):
    acts: list[str]
    count: int


class RunOutcomesResponse(BaseModel):
    total: int
    wins: int
    losses: int
    abandoned: int
    win_rate: float
    killed_by_encounter: list[KilledByEntry]
    killed_by_event: list[KilledByEntry]
    acts_reached: list[ActsReachedEntry]


class EncounterCharacterBreakdown(BaseModel):
    character: str
    kill_count: int


class EncounterStatsResponse(BaseModel):
    encounter: str
    kill_count: int
    kill_share: float
    characters: list[EncounterCharacterBreakdown]


class DeckGrowthEntry(BaseModel):
    floor: int
    avg_deck_size: float
    cards_added: int
    upgrades_at_floor: int
