"""DPI awareness is requested on Windows only, and can never crash startup."""

import sys
import types

from core import display


def fake_ctypes(shcore=None, user32=None):
    windll = types.SimpleNamespace(
        shcore=shcore or types.SimpleNamespace(),
        user32=user32 or types.SimpleNamespace(),
    )
    return types.SimpleNamespace(windll=windll)


def test_does_nothing_off_windows(monkeypatch):
    calls = []
    shcore = types.SimpleNamespace(SetProcessDpiAwareness=lambda v: calls.append(v))
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes(shcore=shcore))
    assert display.enable_dpi_awareness() is False
    assert calls == []


def test_windows_asks_for_dpi_awareness(monkeypatch):
    calls = []
    shcore = types.SimpleNamespace(SetProcessDpiAwareness=lambda v: calls.append(v))
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes(shcore=shcore))
    assert display.enable_dpi_awareness() is True
    assert calls == [1]


def test_older_windows_falls_back_to_user32(monkeypatch):
    calls = []
    user32 = types.SimpleNamespace(SetProcessDPIAware=lambda: calls.append("old"))
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes(user32=user32))
    assert display.enable_dpi_awareness() is True
    assert calls == ["old"]


def test_failure_is_swallowed(monkeypatch):
    def boom(_):
        raise OSError("denied")

    shcore = types.SimpleNamespace(SetProcessDpiAwareness=boom)
    user32 = types.SimpleNamespace(SetProcessDPIAware=lambda: (_ for _ in ()).throw(OSError("no")))
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "ctypes", fake_ctypes(shcore=shcore, user32=user32))
    assert display.enable_dpi_awareness() is False
