"""Thin wrapper around the STS2 backend stats API."""

from __future__ import annotations

import logging
from typing import Any

import requests
from flask import current_app

log = logging.getLogger(__name__)

_TIMEOUT = 10  # seconds


def _base_url() -> str:
    return current_app.config["API_BASE_URL"].rstrip("/")


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{_base_url()}{path}"
    try:
        resp = requests.get(url, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        log.exception("API request failed: %s", url)
        return None


# -- Overview ----------------------------------------------------------------

def get_overview(steam_id: str | None = None) -> dict | None:
    params = {}
    if steam_id:
        params["steam_id"] = steam_id
    return _get("/api/stats/overview", params or None)


# -- Characters --------------------------------------------------------------

def get_characters(
    steam_id: str | None = None,
    ascension: int | None = None,
    game_mode: str | None = None,
) -> list[dict] | None:
    params: dict[str, Any] = {}
    if steam_id:
        params["steam_id"] = steam_id
    if ascension is not None:
        params["ascension"] = ascension
    if game_mode:
        params["game_mode"] = game_mode
    return _get("/api/stats/characters", params or None)


# -- Cards -------------------------------------------------------------------

def get_cards(
    steam_id: str | None = None,
    character: str | None = None,
    ascension: int | None = None,
    min_appearances: int = 3,
) -> list[dict] | None:
    params: dict[str, Any] = {"min_appearances": min_appearances}
    if steam_id:
        params["steam_id"] = steam_id
    if character:
        params["character"] = character
    if ascension is not None:
        params["ascension"] = ascension
    return _get("/api/stats/cards", params)


# -- Relics ------------------------------------------------------------------

def get_relics(
    steam_id: str | None = None,
    character: str | None = None,
    ascension: int | None = None,
    min_appearances: int = 3,
) -> list[dict] | None:
    params: dict[str, Any] = {"min_appearances": min_appearances}
    if steam_id:
        params["steam_id"] = steam_id
    if character:
        params["character"] = character
    if ascension is not None:
        params["ascension"] = ascension
    return _get("/api/stats/relics", params)


# -- Run outcomes ------------------------------------------------------------

def get_run_outcomes(
    steam_id: str | None = None,
    character: str | None = None,
    ascension: int | None = None,
) -> dict | None:
    params: dict[str, Any] = {}
    if steam_id:
        params["steam_id"] = steam_id
    if character:
        params["character"] = character
    if ascension is not None:
        params["ascension"] = ascension
    return _get("/api/stats/runs/outcomes", params or None)


# -- Encounters --------------------------------------------------------------

def get_encounters(
    steam_id: str | None = None,
    character: str | None = None,
    ascension: int | None = None,
) -> list[dict] | None:
    params: dict[str, Any] = {}
    if steam_id:
        params["steam_id"] = steam_id
    if character:
        params["character"] = character
    if ascension is not None:
        params["ascension"] = ascension
    return _get("/api/stats/encounters", params or None)


# -- Deck growth -------------------------------------------------------------

def get_deck_growth(
    steam_id: str | None = None,
    character: str | None = None,
    ascension: int | None = None,
) -> list[dict] | None:
    params: dict[str, Any] = {}
    if steam_id:
        params["steam_id"] = steam_id
    if character:
        params["character"] = character
    if ascension is not None:
        params["ascension"] = ascension
    return _get("/api/stats/deck/growth", params or None)


# -- Runs list ---------------------------------------------------------------

def get_runs(limit: int = 10, offset: int = 0) -> dict | None:
    return _get("/api/runs", {"limit": limit, "offset": offset})


# -- Helpers -----------------------------------------------------------------

def format_character_name(raw: str) -> str:
    """'CHARACTER.NECROBINDER' -> 'Necrobinder'"""
    return raw.replace("CHARACTER.", "").replace("_", " ").title()


def format_duration(seconds: float) -> str:
    """Seconds -> human-readable duration like '1h 23m'."""
    if seconds < 0:
        return "—"
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m"
