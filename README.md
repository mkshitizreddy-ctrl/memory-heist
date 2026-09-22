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
  levels/                  # Members 2-4: level1, level2, level3_loops,
                            # level4_memory, level5_control, final_vault,
                            # common (shared drawing/JSON helpers)
  systems/                 # inventory (used by Level 4), scoring, security,
                            # timer, hints (not yet wired into gameplay)
  ui/                       # menu, HUD, win screen
  data/puzzles.json        # Level 1 & 2 puzzle content, separate from code
  assets/                   # images, sounds, fonts
  docs/                     # design doc + team workflow notes
```

## Controls

| Key | Action |
|---|---|
| ENTER | Start game from menu |
| Mouse | Answer Level 1 & 2 puzzles |
| 1 / 2 / 3 / 4 | Answer Level 3, 5, and Final Vault puzzles |
| WASD | Move (Level 4 only) |
| E | Collect items / interact (Level 4 only) |
| ESC | Pause during gameplay; quit from the win screen |

Close the window using its title bar (X) to quit from the menu or mid-level.

## Status

All 5 levels plus the Final Vault are built, registered, and chained
together — the game runs a complete arc: menu → Level 1 → Level 2 →
Level 3 → Level 4 → Level 5 → Final Vault → win screen. A HUD shows
current level progress.

Each level teaches its topic directly through gameplay:
- Level 1: variables & data types (agent record quiz)
- Level 2: operators & conditionals (expression-building tiles)
- Level 3: loops (`break` identification under a timer)
- Level 4: lists & dictionaries (inventory collection + vault unlock)
- Level 5: functions & exceptions (concept quiz + terminal input)
- Final Vault: all topics combined across 6 stages

Pending: no lose condition yet, menu/HUD/win screen are placeholder
styling, no sound, and the scoring/timer/security systems exist in code
but aren't wired into gameplay yet.

---