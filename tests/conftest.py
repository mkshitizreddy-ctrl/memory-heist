"""Shared test setup."""

import pytest

from systems.settings import ENV_VAR


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Never read or write the player's real saves/settings.json in a test."""
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "settings.json"))
