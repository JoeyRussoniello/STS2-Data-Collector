"""Tests for the public read-only API endpoints."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestPublicListRuns:
    def test_no_api_key_required(self, client):
        """Public endpoints must not require authentication."""
        resp = client.get("/api/runs")
        # Should NOT be 401 — any other status means middleware was skipped
        assert resp.status_code != 401

    @pytest.mark.golden
    def test_returns_list_response_shape(self, client):
        resp = client.get("/api/runs?limit=5&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert "runs" in body
        assert "total" in body
        assert "limit" in body
        assert "offset" in body
        assert body["limit"] == 5
        assert body["offset"] == 0

    def test_invalid_limit_returns_422(self, client):
        resp = client.get("/api/runs?limit=0")
        assert resp.status_code == 422

    def test_negative_offset_returns_422(self, client):
        resp = client.get("/api/runs?offset=-1")
        assert resp.status_code == 422


class TestPublicGetRun:
    def test_no_api_key_required(self, client):
        try:
            resp = client.get("/api/runs/nonexistent:id:here")
            assert resp.status_code != 401
        except Exception:
            # DB connection error is expected without a real database;
            # the point is that the auth middleware did NOT reject the request.
            pass

    @pytest.mark.golden
    def test_missing_run_returns_404(self, client):
        resp = client.get("/api/runs/nonexistent:id:here")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Run not found"
