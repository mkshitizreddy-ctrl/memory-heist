# Team Workflow & Precautions

## 1. Who owns what

| Area | Owner |
|---|---|
| `main.py`, `core/` (game loop, player, level manager, maps, difficulty), repo, CI, integration | Kshitiz Reddy |
| `levels/level1.py`, `levels/level2.py` | Paranthama Selvan |
| `levels/level3_loops.py`, `levels/level4_memory.py` | Yashovardhan Kushva |
| `levels/level5_control.py`, `levels/level5_questions.py`, `levels/final_vault.py` | Apporov Sahu |
| `ui/`, `systems/`, `entities/` | Divyash |

Edit only your own files. If you find a problem in someone else's file, do not
fix it there: message the owner with what you saw (file, line, what happens,
how to reproduce) and let them change it.

Shared files (`main.py`, `core/game.py`, `core/level_manager.py`,
`data/puzzles.json`, `requirements.txt`): ask in the group chat before
changing them. Core changes go through Kshitiz.

## 2. Branches and pull requests

`main` is always playable and is only changed through pull requests.

- One short-lived branch per change, named `<type>/<what>`:
  `fix/hints-default-path`, `feat/run-timer`, `perf/pause-assets`.
- Keep a PR to one change. Small PRs are reviewed and merged faster.
- Start from a fresh `main`:

```bash
git switch main
git pull
git switch -c fix/short-description
```

- Open the PR on GitHub. CI must be green before it is merged. Kshitiz merges.
- After merging, pull `main` and delete the branch.

## 3. Before you open a PR

1. `python -m pytest tests -q` passes (CI runs the same command).
2. `python main.py` starts, and you have played the part you changed.
3. `git status --short` lists only the files you meant to change.
4. A bug fix comes with a test that fails without the fix and passes with it.

## 4. Module contract

Each level class exposes:

```python
update(dt)
render(surface)
handle_event(event)
is_complete() -> bool
```

Systems modules take data in and return data out. They should not need the
Pygame screen, so they can be unit-tested without opening a window.

## 5. Rules learned from bugs in this codebase

- Never call `sys.exit()` inside game code. `Game.run()` returns, and `main.py`
  quits Pygame and exits.
- Build fonts and surfaces once, not every frame. `pygame.font.Font()` costs
  about 2 ms per call, and a frame has 16.7 ms. Create them in a helper and
  reuse them.
- Do not use paths relative to the working directory. Build them from the
  repo root, so the game works when started from any folder.
- Movement uses `dt`. `Game` caps `dt` at 0.05 s, so a stalled frame cannot
  jump timers or push the player through a wall.
- The run has one countdown (`BASE_RUN_SECONDS` in `core/difficulty.py`, scaled
  by difficulty). Do not assume a level has unlimited time.
- The players are reset to their start positions whenever the level changes.
  Levels do not place the player themselves.
- A key that triggers a state change (starting a run, retrying) must be consumed
  and must not reach the next screen or level.

## 6. Communication

- Short check-in every day or two: what you finished, what you touch next,
  what is blocking you.
- Say in the group chat before touching a shared file.
- If you are stuck for more than 30 to 45 minutes, ask.
- Put `# TODO(name):` in the code instead of leaving unfinished logic silent.
