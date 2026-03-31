"""Request/response schemas — decoupled from domain and ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ── Requests ──


class RunUploadRequest(BaseModel):
    steam_id: str = Field(..., min_length=1)
    profile: str = Field(..., min_length=1)
    file_name: str = Field(..., min_length=1)
    file_size: int = Field(..., ge=0)
    data: dict[str, Any]


# ── Responses ──


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
