"""Shared fixtures and markers for the backend test suite."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "golden: requires production-like environment (database, credentials)",
    )
