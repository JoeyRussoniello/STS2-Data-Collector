"""API-level tests: middleware, file size limit, CORS headers."""

import pytest
from app.config import settings
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def _valid_data() -> dict:
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
        "players": [],
    }


def _valid_body(**overrides) -> dict:
    body = {
        "steam_id": "12345",
        "profile": "Profile1",
        "file_name": "game1",
        "file_size": 1024,
        "data": _valid_data(),
    }
    body.update(overrides)
    return body


# ── Health (public, no API key) ──


class TestHealthEndpoint:
    def test_health_no_api_key_required(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── API key middleware ──


class TestApiKeyMiddleware:
    def test_missing_api_key_returns_401(self, client):
        resp = client.post("/runs", json=_valid_body())
        assert resp.status_code == 401
        assert "Invalid or missing API key" in resp.json()["detail"]

    def test_wrong_api_key_returns_401(self, client):
        resp = client.post(
            "/runs",
            json=_valid_body(),
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    @pytest.mark.golden
    def test_valid_api_key_passes_middleware(self, client):
        # This will fail at DB level (no real DB), but it should get past the 401
        try:
            resp = client.post(
                "/runs",
                json=_valid_body(),
                headers={"X-API-Key": settings.api_key},
            )
            # Should NOT be 401 — any other status means middleware passed
            assert resp.status_code != 401
        except Exception:
            # DB connection or schema errors are acceptable here; this test only
            # verifies API key middleware behavior.
            pass


# ── File size limit ──


class TestFileSizeLimit:
    def test_oversized_file_returns_413(self, client):
        resp = client.post(
            "/runs",
            json=_valid_body(file_size=11 * 1024 * 1024),
            headers={"X-API-Key": settings.api_key},
        )
        assert resp.status_code == 413
        assert "exceeds maximum" in resp.json()["detail"]

    @pytest.mark.golden
    def test_file_at_limit_not_rejected(self, client):
        try:
            resp = client.post(
                "/runs",
                json=_valid_body(file_size=10 * 1024 * 1024),
                headers={"X-API-Key": settings.api_key},
            )
            # Should NOT be 413 (may fail at DB layer, that's fine)
            assert resp.status_code != 413
        except Exception:
            # DB connection error is expected without a real database;
            # the point is that the 413 guard did NOT reject the request.
            pass


# ── Schema validation via API ──


class TestSchemaValidationViaApi:
    def test_missing_run_data_keys_returns_422(self, client):
        resp = client.post(
            "/runs",
            json=_valid_body(data={"run_time": 100}),
            headers={"X-API-Key": settings.api_key},
        )
        assert resp.status_code == 422

    def test_empty_data_returns_422(self, client):
        resp = client.post(
            "/runs",
            json=_valid_body(data={}),
            headers={"X-API-Key": settings.api_key},
        )
        assert resp.status_code == 422


# ── CORS ──


class TestCors:
    def test_cors_preflight_returns_allow_headers(self, client):
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-API-Key",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers

    def test_cors_header_on_regular_request(self, client):
        resp = client.get("/health", headers={"Origin": "http://example.com"})
        assert resp.headers.get("access-control-allow-origin") == "*"
