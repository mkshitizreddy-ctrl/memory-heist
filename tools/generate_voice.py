"""Generate the game's spoken lines with ElevenLabs.

    Put your key in the project's .env file as ELEVENLABS_API_KEY=... (git ignores it),
    or set ELEVENLABS_API_KEY in the environment. Never commit it or paste it in chat.
    python tools/generate_voice.py --list          what would be made, and how many characters
    python tools/generate_voice.py                 make every missing clip into assets/voice/
    python tools/generate_voice.py --only echo     just one speaker (narrator, echo, warden)
    python tools/generate_voice.py --premade       use the built-in voices instead of the designed ones
    python tools/generate_voice.py --voices        list the voices your key can use

Clips that already exist are skipped, so it is safe to run again after editing
story or radio text: only the changed lines are made. Uses only the standard
library.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from systems import voice_clips as vc  # noqa: E402

API = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
RETRIES = 4
USER_AGENT = "memory-heist-voice-tool"


def read_env_file(path):
    """KEY=VALUE pairs from a .env file; a missing file is just empty. Never printed."""
    values = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                name = name.strip()
                if name.startswith("export "):
                    name = name[len("export "):].strip()
                values[name] = value.strip().strip("'\"")
    except OSError:
        pass
    return values


def find_key(env, env_path):
    """The API key from the environment, else from the .env file, else ''."""
    return (env.get("ELEVENLABS_API_KEY") or read_env_file(env_path).get("ELEVENLABS_API_KEY", "")).strip()


def pending(clips, folder=None, force=False, only=None):
    """The clips still to make, as (speaker, text, path)."""
    todo = []
    for speaker, text in clips:
        if only and speaker != only:
            continue
        path = vc.clip_path(speaker, text, folder)
        if force or not os.path.exists(path):
            todo.append((speaker, text, path))
    return todo


def build_request(speaker, text, key, cast, model=DEFAULT_MODEL):
    """(url, headers, body bytes) for one text-to-speech call."""
    voice = cast[speaker]
    body = {
        "text": text,
        "model_id": model,
        "voice_settings": {"stability": voice["stability"], "similarity_boost": 0.8},
    }
    url = f"{API}/text-to-speech/{voice['voice_id']}?output_format={OUTPUT_FORMAT}"
    headers = {"xi-api-key": key, "Content-Type": "application/json",
               "Accept": "audio/mpeg", "User-Agent": USER_AGENT}
    return url, headers, json.dumps(body).encode("utf-8")


class ApiError(Exception):
    """A response that retrying will not fix (bad key, no credits, unknown voice)."""


def fetch(speaker, text, key, cast, model, opener=urllib.request.urlopen, sleep=time.sleep):
    """The mp3 bytes for one line; retries rate limits and server errors."""
    url, headers, body = build_request(speaker, text, key, cast, model)
    for attempt in range(RETRIES + 1):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with opener(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or error.code >= 500
            if not retryable or attempt == RETRIES:
                detail = error.read().decode("utf-8", "replace")[:300] if hasattr(error, "read") else ""
                raise ApiError(f"HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            if attempt == RETRIES:
                raise ApiError(f"network error: {error.reason}") from error
        sleep(2 ** attempt)
    raise ApiError("gave up")


def write_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".part"
    with open(temporary, "wb") as f:
        f.write(data)
    os.replace(temporary, path)


def generate(todo, key, cast, model=DEFAULT_MODEL, opener=urllib.request.urlopen,
             sleep=time.sleep, out=print):
    """Make every pending clip. Returns (made, failed); stops early on a fatal error."""
    made, failed = 0, 0
    for index, (speaker, text, path) in enumerate(todo, start=1):
        try:
            data = fetch(speaker, text, key, cast, model, opener, sleep)
        except ApiError as error:
            failed += 1
            out(f"[{index}/{len(todo)}] FAILED {speaker}: {error}")
            if any(code in str(error) for code in ("HTTP 401", "HTTP 402", "HTTP 403", "HTTP 404")):
                out("Stopping: this will not get better by retrying. Check the key, credits and voice ids.")
                break
            continue
        if not data:
            failed += 1
            out(f"[{index}/{len(todo)}] FAILED {speaker}: empty response")
            continue
        write_atomic(path, data)
        made += 1
        out(f"[{index}/{len(todo)}] {speaker}: {os.path.basename(path)} ({len(data) // 1024} KB)")
    return made, failed


def list_voices(key, opener=urllib.request.urlopen):
    request = urllib.request.Request(f"{API}/voices", headers={"xi-api-key": key, "User-Agent": USER_AGENT})
    with opener(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8")).get("voices", [])


def main(argv=None, env=None, out=print):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="show what would be made and exit")
    parser.add_argument("--only", choices=sorted(vc.CAST), help="only this speaker")
    parser.add_argument("--force", action="store_true", help="remake clips that already exist")
    parser.add_argument("--premade", action="store_true", help="use the built-in voices")
    parser.add_argument("--voices", action="store_true", help="list the voices your key can use")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--folder", default=None, help="output folder (default assets/voice)")
    args = parser.parse_args(argv)
    env = os.environ if env is None else env
    env_path = os.path.join(vc.ROOT, ".env")

    cast = vc.PREMADE_CAST if args.premade else vc.CAST
    todo = pending(vc.all_clips(), args.folder, args.force, args.only)
    characters = sum(len(text) for _, text, _ in todo)
    if args.list:
        for speaker, text, path in todo:
            out(f"{speaker:9} {len(text):4} chars  {os.path.basename(path)}  {text[:60]}")
        out(f"{len(todo)} clips to make, {characters} characters (about {characters} credits)")
        return 0

    key = find_key(env, env_path)
    if not key:
        out("No API key found. Paste it after ELEVENLABS_API_KEY= in the project's .env file.")
        return 2
    if args.voices:
        for voice in list_voices(key):
            out(f"{voice['voice_id']}  {voice.get('name', '')}  ({voice.get('category', '')})")
        return 0
    if not todo:
        out("Nothing to make: every clip already exists.")
        return 0
    out(f"Making {len(todo)} clips, {characters} characters (about {characters} credits).")
    made, failed = generate(todo, key, cast, args.model, out=out)
    out(f"Done: {made} made, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
