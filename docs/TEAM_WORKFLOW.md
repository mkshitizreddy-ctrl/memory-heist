# Team Workflow & Precautions (5 Members)

## 1. Branching Strategy

Do NOT all push directly to `main`. Use one branch per member:

```
main                 -> always playable, protected
  member1-core
  member2-levels12
  member3-levels34
  member4-level5
  member5-ui
```

Workflow for everyone:
```bash
git checkout main
git pull origin main
git checkout -b member2-levels12   # once, then reuse
# ...work...
git add .
git commit -m "Level 1: variable puzzle logic"
git push origin member2-levels12
```
Then open a Pull Request into `main`. At least one other teammate should
glance at it before merging (even a 2-minute read) — this is what makes
Rubric 2 "understanding of code" credible later.

## 2. Merge Conflict Prevention

Conflicts almost always happen in **shared** files, not in the level files
that belong to one person. Watch these specifically:
- `main.py`, `core/game.py`, `core/level_manager.py` — only Member 1 edits
  these directly; others request changes via PR comment instead of editing
  live.
- `data/puzzles.json` — agree on who adds entries and when; consider each
  person adding only their own puzzle keys in a single commit.
- `requirements.txt` — announce in chat before adding a new dependency.

Pull `main` before starting each session (`git pull origin main`) so your
branch doesn't drift too far and conflicts stay small.

## 3. Module Contracts (so work can happen in parallel)

Each level class must expose exactly:
```python
update(dt)
render(surface)
is_complete() -> bool
```
Each systems module should have no dependency on Pygame's `screen` object
directly (pass data in, get data out) so it can be unit-tested without
running the whole game. This lets Member 5 build the HUD against level 1's
interface before level 3 is even finished.

## 4. Communication Precautions

- Short daily or every-other-day check-in (15 min): what did you finish,
  what are you touching next, anything blocking you.
- Before touching a shared file, say so in the group chat.
- If you're stuck for more than ~30-45 minutes, ask — don't silently lose
  a day.

## 5. Code Quality Precautions

- Every function/class gets a one-line docstring (already started in the
  stubs) — this is what makes Rubric 2 easy to demonstrate live.
- Keep puzzle content in `data/puzzles.json`, not hardcoded in level files,
  so a design change doesn't need a code change.
- Run the game after merging your branch into a local `main` copy before
  actually pushing to shared `main` — catch import errors early.
- Add a `# TODO(name):` comment instead of leaving silent unfinished logic.

## 6. Timeline Risk Precautions

- Don't start Optional Features (sound, animations, save system) until
  the Minimum Viable Product list in the report is fully working end to
  end (menu -> 5 levels -> final vault -> win/lose).
- If a level is behind schedule by Day 10, simplify its puzzle rather than
  cutting scope elsewhere — the report's five-level structure is core to
  the grading rubric.
