# Memory Heist

An interactive 2D Python learning game built with Pygame. The player is a
hacker escaping the "Memory Vault" by solving puzzles based on core Python
concepts: variables, operators, loops, lists/dictionaries, functions, and
exception handling.

See `docs/PROJECT_REPORT.md` for the full design document and
`docs/TEAM_WORKFLOW.md` for how the 5-person team collaborates.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
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
| ESC | Pause |
| Mouse | Menu / puzzle interaction |

## Status

Project initialized — core game loop runs (empty window). Levels and
systems are stubbed out per the module contracts described in each file's
docstring. Next step: Week 1, Day 3-4 (player movement, room structure,
collision, interaction system) per the development plan.
