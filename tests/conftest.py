"""Shared test setup."""

import pytest

from systems.settings import ENV_VAR


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Never read or write the player's real saves/settings.json in a test."""
    monkeypatch.setenv(ENV_VAR, str(tmp_path / "settings.json"))


@pytest.fixture(autouse=True)
def isolated_progress(tmp_path, monkeypatch):
    """Never read or write the player's real saves/progress.json in a test."""
    from systems.progress import ENV_VAR as PROGRESS_ENV

    monkeypatch.setenv(PROGRESS_ENV, str(tmp_path / "progress.json"))


@pytest.fixture(autouse=True)
def isolated_stats(tmp_path, monkeypatch):
    """Never read or write the player's real saves/stats.json in a test."""
    from systems.achievements import ENV_VAR as STATS_ENV

    monkeypatch.setenv(STATS_ENV, str(tmp_path / "stats.json"))


@pytest.fixture(autouse=True)
def no_recorded_voice(tmp_path_factory, monkeypatch):
    """Tests hear the blip voices, whether or not clips are generated in assets/voice."""
    from systems import voice_clips

    monkeypatch.setattr(voice_clips, "CLIP_DIR", str(tmp_path_factory.mktemp("no_clips")))


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
