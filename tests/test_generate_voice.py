"""tools/generate_voice.py: what it asks for, how it retries, what it writes."""

import io
import json
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import generate_voice as G  # noqa: E402
from systems import voice_clips as vc  # noqa: E402

CLIPS = [("echo", "Stay low."), ("warden", "I am watching."), ("narrator", "A story.")]


class Response:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def http_error(code):
    return urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(b'{"detail":"nope"}'))


def scripted(*outcomes):
    """An opener that returns/raises each outcome in turn, recording the requests."""
    calls = []
    queue = list(outcomes)

    def opener(request, timeout=0):
        calls.append(request)
        outcome = queue.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return Response(outcome)

    opener.calls = calls
    return opener


# --- choosing what to make ----------------------------------------------------------------
def test_everything_is_pending_in_an_empty_folder(tmp_path):
    todo = G.pending(CLIPS, str(tmp_path))
    assert [(s, t) for s, t, _ in todo] == CLIPS


def test_existing_clips_are_skipped_unless_forced(tmp_path):
    open(vc.clip_path("echo", "Stay low.", str(tmp_path)), "wb").write(b"x")
    assert [s for s, _, _ in G.pending(CLIPS, str(tmp_path))] == ["warden", "narrator"]
    assert len(G.pending(CLIPS, str(tmp_path), force=True)) == 3


def test_only_limits_to_one_speaker(tmp_path):
    assert [s for s, _, _ in G.pending(CLIPS, str(tmp_path), only="warden")] == ["warden"]


# --- the request ---------------------------------------------------------------------------
def test_the_request_carries_the_voice_text_model_and_key():
    url, headers, body = G.build_request("echo", "Stay low.", "KEY", vc.CAST, "m1")
    assert vc.CAST["echo"]["voice_id"] in url and "output_format=mp3" in url
    assert headers["xi-api-key"] == "KEY" and headers["Accept"] == "audio/mpeg"
    data = json.loads(body)
    assert data["text"] == "Stay low." and data["model_id"] == "m1"
    assert data["voice_settings"]["stability"] == vc.CAST["echo"]["stability"]


def test_the_premade_cast_uses_other_voice_ids():
    a, _, _ = G.build_request("warden", "x", "K", vc.CAST)
    b, _, _ = G.build_request("warden", "x", "K", vc.PREMADE_CAST)
    assert a != b


# --- fetching --------------------------------------------------------------------------------
def test_a_good_response_is_returned_as_is():
    opener = scripted(b"MP3DATA")
    assert G.fetch("echo", "x", "K", vc.CAST, "m", opener, sleep=lambda s: None) == b"MP3DATA"
    assert len(opener.calls) == 1


def test_rate_limits_are_retried_with_growing_pauses():
    sleeps = []
    opener = scripted(http_error(429), http_error(503), b"OK")
    assert G.fetch("echo", "x", "K", vc.CAST, "m", opener, sleep=sleeps.append) == b"OK"
    assert sleeps == [1, 2] and len(opener.calls) == 3


def test_a_bad_key_is_not_retried():
    opener = scripted(http_error(401))
    sleeps = []
    with pytest.raises(G.ApiError, match="HTTP 401"):
        G.fetch("echo", "x", "K", vc.CAST, "m", opener, sleep=sleeps.append)
    assert len(opener.calls) == 1 and sleeps == []


def test_it_gives_up_after_the_retry_limit():
    opener = scripted(*[http_error(500)] * (G.RETRIES + 1))
    with pytest.raises(G.ApiError, match="HTTP 500"):
        G.fetch("echo", "x", "K", vc.CAST, "m", opener, sleep=lambda s: None)
    assert len(opener.calls) == G.RETRIES + 1


def test_network_errors_are_retried_then_reported():
    opener = scripted(*[urllib.error.URLError("offline")] * (G.RETRIES + 1))
    with pytest.raises(G.ApiError, match="network error: offline"):
        G.fetch("echo", "x", "K", vc.CAST, "m", opener, sleep=lambda s: None)


# --- generating ---------------------------------------------------------------------------------
def todo_in(tmp_path):
    return G.pending(CLIPS, str(tmp_path))


def test_generate_writes_each_clip_and_counts(tmp_path):
    lines = []
    made, failed = G.generate(todo_in(tmp_path), "K", vc.CAST, opener=scripted(b"a", b"b", b"c"),
                              sleep=lambda s: None, out=lines.append)
    assert (made, failed) == (3, 0)
    for speaker, text in CLIPS:
        assert open(vc.clip_path(speaker, text, str(tmp_path)), "rb").read() in (b"a", b"b", b"c")
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".part")]
    assert len(lines) == 3


def test_a_fatal_error_stops_the_run_and_says_why(tmp_path):
    lines = []
    made, failed = G.generate(todo_in(tmp_path), "K", vc.CAST, opener=scripted(b"a", http_error(402)),
                              sleep=lambda s: None, out=lines.append)
    assert (made, failed) == (1, 1)
    assert any("Stopping" in line for line in lines)
    assert not os.path.exists(vc.clip_path("narrator", "A story.", str(tmp_path)))


def test_a_transient_failure_skips_that_clip_and_carries_on(tmp_path):
    sleeps = []
    outcomes = [b"a"] + [http_error(500)] * (G.RETRIES + 1) + [b"c"]
    made, failed = G.generate(todo_in(tmp_path), "K", vc.CAST, opener=scripted(*outcomes),
                              sleep=sleeps.append, out=lambda s: None)
    assert (made, failed) == (2, 1)


def test_an_empty_response_counts_as_a_failure_and_writes_nothing(tmp_path):
    made, failed = G.generate(todo_in(tmp_path)[:1], "K", vc.CAST, opener=scripted(b""),
                              sleep=lambda s: None, out=lambda s: None)
    assert (made, failed) == (0, 1) and not os.listdir(tmp_path)


# --- the .env file ---------------------------------------------------------------------------------
def test_read_env_file_parses_keys_comments_quotes_and_export(tmp_path):
    path = tmp_path / ".env"
    path.write_text("# comment\n\nA=1\nexport B = two \nC='three'\nD=\"four\"\nnonsense\nE=a=b\n")
    assert G.read_env_file(str(path)) == {"A": "1", "B": "two", "C": "three", "D": "four", "E": "a=b"}


def test_a_missing_env_file_is_empty(tmp_path):
    assert G.read_env_file(str(tmp_path / "nope")) == {}


def test_the_environment_wins_over_the_env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text("ELEVENLABS_API_KEY=from_file\n")
    assert G.find_key({"ELEVENLABS_API_KEY": "from_env"}, str(path)) == "from_env"
    assert G.find_key({}, str(path)) == "from_file"
    assert G.find_key({}, str(tmp_path / "none")) == ""


# --- command line -------------------------------------------------------------------------------------
def test_list_shows_the_work_and_never_needs_a_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(vc, "ROOT", str(tmp_path))
    lines = []
    assert G.main(["--list", "--folder", str(tmp_path)], env={}, out=lines.append) == 0
    assert "clips to make" in lines[-1] and "credits" in lines[-1]


def test_without_a_key_it_stops_before_spending_anything(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", str(tmp_path))
    monkeypatch.setattr(G, "generate", lambda *a, **k: pytest.fail("must not generate"))
    lines = []
    assert G.main(["--folder", str(tmp_path)], env={}, out=lines.append) == 2
    assert ".env" in lines[0]


def test_with_a_key_in_the_env_file_it_generates_and_reports_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", str(tmp_path))
    (tmp_path / ".env").write_text("ELEVENLABS_API_KEY=abc\n")
    seen = {}

    def fake_generate(todo, key, cast, model, out):
        seen.update(count=len(todo), key=key, cast=cast, model=model)
        return len(todo) - 1, 1

    monkeypatch.setattr(G, "generate", fake_generate)
    code = G.main(["--only", "echo", "--premade", "--folder", str(tmp_path / "out")], env={}, out=lambda s: None)
    assert code == 1
    assert seen["key"] == "abc" and seen["cast"] is vc.PREMADE_CAST
    assert seen["count"] == sum(1 for s, _ in vc.all_clips() if s == "echo")


def test_when_every_clip_exists_there_is_nothing_to_do(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", str(tmp_path))
    (tmp_path / ".env").write_text("ELEVENLABS_API_KEY=abc\n")
    for speaker, text in vc.all_clips():
        open(vc.clip_path(speaker, text, str(tmp_path)), "wb").write(b"x")
    lines = []
    assert G.main(["--folder", str(tmp_path)], env={}, out=lines.append) == 0
    assert "Nothing to make" in lines[-1]
