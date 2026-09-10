# Memory Heist

An interactive 2D Python learning game built with Pygame. The player is a
hacker escaping the "Memory Vault" by solving puzzles based on core Python
concepts: variables, operators, loops, lists/dictionaries, functions, and
exception handling.

See `docs/PROJECT_REPORT.md` for the full design document and
`docs/TEAM_WORKFLOW.md` for how the 5-person team collaborates.

## Setup

```powershell
conda create -n ai_env python=3.11
conda activate ai_env
pip install -r requirements.txt
python main.py
```

## Project Structure

```
memory-heist/
  main.py                 # entry point
  core/                    # Member 1: game loop, player, level manager
  levels/                  # Members 2-4: level1-5 puzzle logic
  systems/                 # Member 5 (+3): inventory, scoring, security, timer, hints
  ui/                       # Member 5: menu, HUD, win/lose screens
  data/puzzles.json        # puzzle content, separate from code
  assets/                   # images, sounds, fonts
  docs/                     # design doc + team workflow notes
```

## Controls

| Key | Action |
|---|---|
| W / A / S / D | Move |
| E | Interact |
| ESC | Quit |
| Mouse | Menu / puzzle interaction |

## Status

Core game system is complete: player movement, wall collision, screen
boundary clamping, diagonal movement normalization, an E-to-interact
system, and the level manager are all working and merged into main.

Level 1 currently shows a placeholder rectangle to confirm the level
manager wiring works end to end — it isn't the real puzzle yet.

Next: individual level puzzle logic (Levels 1-5), Final Vault, menu/HUD,
and full integration between levels.