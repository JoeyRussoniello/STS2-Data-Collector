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


#* Responses
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
