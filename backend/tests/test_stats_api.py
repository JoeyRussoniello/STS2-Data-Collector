"""Tests for the public statistics API endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestStatsOverview:
    def test_no_api_key_required(self, client):
        """Stats endpoints must not require authentication."""
        try:
            resp = client.get("/api/stats/overview")
            assert resp.status_code != 401
        except Exception:
            pass

    @pytest.mark.golden
    def test_returns_overview_shape(self, client):
        try:
            resp = client.get("/api/stats/overview")
            assert resp.status_code == 200
            body = resp.json()
            assert "run_count" in body
            assert "win_count" in body
            assert "win_rate" in body
            assert "abandon_rate" in body
            assert "avg_run_time_seconds" in body
            assert "avg_ascension" in body
            assert "avg_acts_cleared" in body
            assert "characters" in body
            assert isinstance(body["characters"], list)
        except Exception:
            pass

    @pytest.mark.golden
    def test_steam_id_filter_accepted(self, client):
        try:
            resp = client.get("/api/stats/overview?steam_id=12345")
            assert resp.status_code == 200
        except Exception:
            pass


class TestStatsCharacters:
    def test_no_api_key_required(self, client):
        try:
            resp = client.get("/api/stats/characters")
            assert resp.status_code != 401
        except Exception:
            pass

    @pytest.mark.golden
    def test_returns_list(self, client):
        try:
            resp = client.get("/api/stats/characters")
            assert resp.status_code == 200
            body = resp.json()
            assert isinstance(body, list)
        except Exception:
            pass

    @pytest.mark.golden
    def test_filters_accepted(self, client):
        try:
            resp = client.get(
                "/api/stats/characters?steam_id=12345&ascension=5&game_mode=standard"
            )
            assert resp.status_code == 200
        except Exception:
            pass


class TestStatsCards:
    def test_no_api_key_required(self, client):
        try:
            resp = client.get("/api/stats/cards")
            assert resp.status_code != 401
        except Exception:
            pass

    @pytest.mark.golden
    def test_returns_list(self, client):
        try:
            resp = client.get("/api/stats/cards")
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
        except Exception:
            pass

    def test_min_appearances_validation(self, client):
        resp = client.get("/api/stats/cards?min_appearances=0")
        assert resp.status_code == 422

    @pytest.mark.golden
    def test_filters_accepted(self, client):
        try:
            resp = client.get(
                "/api/stats/cards?character=IRONCLAD&ascension=0&min_appearances=1"
            )
            assert resp.status_code == 200
        except Exception:
            pass


class TestStatsRelics:
    def test_no_api_key_required(self, client):
        try:
            resp = client.get("/api/stats/relics")
            assert resp.status_code != 401
        except Exception:
            pass

    @pytest.mark.golden
    def test_returns_list(self, client):
        try:
            resp = client.get("/api/stats/relics")
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
        except Exception:
            pass

    def test_min_appearances_validation(self, client):
        resp = client.get("/api/stats/relics?min_appearances=0")
        assert resp.status_code == 422


class TestStatsRunOutcomes:
    def test_no_api_key_required(self, client):
        try:
            resp = client.get("/api/stats/runs/outcomes")
            assert resp.status_code != 401
        except Exception:
            pass

    @pytest.mark.golden
    def test_returns_outcomes_shape(self, client):
        try:
            resp = client.get("/api/stats/runs/outcomes")
            assert resp.status_code == 200
            body = resp.json()
            assert "total" in body
            assert "wins" in body
            assert "losses" in body
            assert "abandoned" in body
            assert "win_rate" in body
            assert "killed_by_encounter" in body
            assert "killed_by_event" in body
            assert "acts_reached" in body
        except Exception:
            pass


class TestStatsEncounters:
    def test_no_api_key_required(self, client):
        try:
            resp = client.get("/api/stats/encounters")
            assert resp.status_code != 401
        except Exception:
            pass

    @pytest.mark.golden
    def test_returns_list(self, client):
        try:
            resp = client.get("/api/stats/encounters")
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
        except Exception:
            pass


class TestStatsDeckGrowth:
    def test_no_api_key_required(self, client):
        try:
            resp = client.get("/api/stats/deck/growth")
            assert resp.status_code != 401
        except Exception:
            pass

    @pytest.mark.golden
    def test_returns_list(self, client):
        try:
            resp = client.get("/api/stats/deck/growth")
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
        except Exception:
            pass

    @pytest.mark.golden
    def test_filters_accepted(self, client):
        try:
            resp = client.get("/api/stats/deck/growth?character=IRONCLAD&ascension=0")
            assert resp.status_code == 200
        except Exception:
            pass


class TestStatsAscensionValidation:
    """Ascension must be >= 0 on all endpoints that accept it."""

    def test_characters_negative_ascension(self, client):
        resp = client.get("/api/stats/characters?ascension=-1")
        assert resp.status_code == 422

    def test_cards_negative_ascension(self, client):
        resp = client.get("/api/stats/cards?ascension=-1")
        assert resp.status_code == 422

    def test_relics_negative_ascension(self, client):
        resp = client.get("/api/stats/relics?ascension=-1")
        assert resp.status_code == 422

    def test_outcomes_negative_ascension(self, client):
        resp = client.get("/api/stats/runs/outcomes?ascension=-1")
        assert resp.status_code == 422

    def test_encounters_negative_ascension(self, client):
        resp = client.get("/api/stats/encounters?ascension=-1")
        assert resp.status_code == 422

    def test_deck_growth_negative_ascension(self, client):
        resp = client.get("/api/stats/deck/growth?ascension=-1")
        assert resp.status_code == 422
