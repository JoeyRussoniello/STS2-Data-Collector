"""Pure domain objects — no framework dependencies."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    steam_id_hash: str
    profile: str
    file_name: str
    file_size: int
    data: dict[str, Any]
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def hash_steam_id(steam_id: str, salt: str) -> str:
    """One-way HMAC-SHA256 hash of a Steam ID, hex-encoded."""
    return hmac.new(
        salt.encode(), steam_id.encode(), hashlib.sha256
    ).hexdigest()
