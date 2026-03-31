"""Tests for schema validation, API key middleware, file size limits, and CORS."""

import pytest
from pydantic import ValidationError

from app.api.schemas import REQUIRED_RUN_KEYS, RunUploadRequest


def _valid_data() -> dict:
    """Return a minimal valid .run data dict with all required keys."""
    return {
        "run_time": 1980,
        "schema_version": 8,
        "seed": "RPX15C3BBT",
        "start_time": 1773000187,
        "was_abandoned": False,
        "win": False,
        "acts": ["ACT.OVERGROWTH"],
        "ascension": 0,
        "build_id": "v0.98.2",
        "game_mode": "standard",
        "killed_by_encounter": "ENCOUNTER.THE_INSATIABLE_BOSS",
        "killed_by_event": "NONE.NONE",
        "map_point_history": [],
    }


def _valid_body(**overrides) -> dict:
    """Return a valid upload request body, with optional overrides."""
    body = {
        "steam_id": "12345",
        "profile": "Profile1",
        "file_name": "game1",
        "file_size": 1024,
        "data": _valid_data(),
    }
    body.update(overrides)
    return body


# ── Schema validation ──


class TestRunUploadRequestValidation:
    def test_valid_payload_accepted(self):
        req = RunUploadRequest(**_valid_body())
        assert req.steam_id == "12345"
        assert "run_time" in req.data

    def test_missing_required_run_data_keys(self):
        incomplete_data = {"run_time": 100, "seed": "ABC"}
        with pytest.raises(ValidationError) as exc_info:
            RunUploadRequest(**_valid_body(data=incomplete_data))
        error_text = str(exc_info.value)
        assert "Missing required .run data keys" in error_text

    def test_extra_keys_in_data_are_allowed(self):
        data = _valid_data()
        data["custom_field"] = "hello"
        req = RunUploadRequest(**_valid_body(data=data))
        assert req.data["custom_field"] == "hello"

    def test_empty_steam_id_rejected(self):
        with pytest.raises(ValidationError):
            RunUploadRequest(**_valid_body(steam_id=""))

    def test_negative_file_size_rejected(self):
        with pytest.raises(ValidationError):
            RunUploadRequest(**_valid_body(file_size=-1))

    def test_all_required_keys_present_in_constant(self):
        expected = {
            "run_time", "schema_version", "seed", "start_time",
            "was_abandoned", "win", "acts", "ascension", "build_id",
            "game_mode", "killed_by_encounter", "killed_by_event",
            "map_point_history",
        }
        assert REQUIRED_RUN_KEYS == expected
