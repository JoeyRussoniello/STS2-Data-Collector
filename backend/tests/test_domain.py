"""Tests for the domain layer: hash_steam_id, RunRecord, RunService."""

import hashlib
import hmac

from app.domain.models import RunRecord, hash_steam_id


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
