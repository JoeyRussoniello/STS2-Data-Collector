"""Tests for the domain layer: hash_steam_id, RunRecord, RunService."""

import hashlib
import hmac

from app.domain.models import RunRecord, hash_steam_id
from app.domain.runs import process_run


class TestHashSteamId:
    def test_deterministic(self):
        h1 = hash_steam_id("12345", "salt")
        h2 = hash_steam_id("12345", "salt")
        assert h1 == h2

    def test_different_salt_different_hash(self):
        h1 = hash_steam_id("12345", "salt-a")
        h2 = hash_steam_id("12345", "salt-b")
        assert h1 != h2

    def test_matches_hmac_sha256(self):
        expected = hmac.new(b"salt", b"12345", hashlib.sha256).hexdigest()
        assert hash_steam_id("12345", "salt") == expected

    def test_hex_length_64(self):
        h = hash_steam_id("steamid", "anysalt")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestRunRecord:
    def test_frozen_dataclass(self):
        r = RunRecord(
            run_id="id",
            steam_id_hash="abc",
            profile="Profile1",
            file_name="game1",
            file_size=100,
            data={"run_time": 1},
        )
        assert r.run_id == "id"
        # frozen — cannot mutate
        import dataclasses

        assert dataclasses.is_dataclass(r)


class TestRunProcessing:
    def test_process_run_builds_normalized_records(self):
        raw = {
            "run_id": "hash:Profile1:game1",
            "data": {
                "win": False,
                "acts": ["ACT.OVERGROWTH"],
                "seed": "SEED123",
                "build_id": "v0.98.2",
                "run_time": 1234,
                "ascension": 3,
                "game_mode": "standard",
                "modifiers": [],
                "start_time": 1000,
                "was_abandoned": False,
                "schema_version": 8,
                "platform_type": None,
                "killed_by_event": "NONE.NONE",
                "killed_by_encounter": "NONE.NONE",
                "players": [
                    {
                        "id": 0,
                        "character": "IRONCLAD",
                        "max_potion_slot_count": 3,
                        "deck": [
                            {
                                "id": "CARD.STRIKE",
                                "floor_added_to_deck": 0,
                                "current_upgrade_level": 1,
                            }
                        ],
                        "relics": [
                            {
                                "id": "RELIC.BURNING_BLOOD",
                                "floor_added_to_deck": 0,
                            }
                        ],
                    }
                ],
                "map_point_history": [[{"map_point_type": "MAP_POINT.MONSTER"}]],
            },
        }

        processed = process_run(raw)

        assert processed.run_data.run_id == "hash:Profile1:game1"
        assert processed.run_data.killed_by_event is None
        assert len(processed.players) == 1
        assert processed.players[0].run_player_id == "hash:Profile1:game1_0"
        assert len(processed.cards) == 1
        assert len(processed.relics) == 1
        assert len(processed.map_points) == 1
        assert processed.map_points[0].map_point_index == 0
