"""Shared test setup."""

import pytest

from systems.settings import ENV_VAR


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Never read or write the player's real saves/settings.json in a test."""
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "settings.json"))


@pytest.fixture(autouse=True)
def fresh_fonts():
    """Some tests shut the font module down; a cached font would then crash."""
    from ui import fonts

    fonts.clear_cache()
    yield
    fonts.clear_cache()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "real_music: renders the real composed music instead of a short stand-in")


@pytest.fixture(autouse=True)
def quick_music(request, monkeypatch):
    """Most tests only need *a* music loop, not 10 seconds of real synthesis.

    Rendering a floor's five stems takes about a quarter of a second, and
    several tests walk through every floor. Tests marked `real_music`
    (the music and composer tests) get the real thing.
    """
    if request.node.get_closest_marker("real_music"):
        return
    try:
        import numpy as np
        from systems import music
    except ImportError:
        return

    def stand_in(stem, key):
        return np.zeros((4410, 2), dtype=np.int16)

    monkeypatch.setattr(music, "synth_stem", stand_in)
