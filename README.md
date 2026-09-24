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
| R     | Retry from lose screen |

Close the window using its title bar (X) to quit from the menu or mid-level.

## Status

All 5 levels plus the Final Vault are complete and fully chained.

Features now working:
- Scoring system (points for correct answers + level completion bonuses)
- Security meter that rises on wrong answers
- Lockdown / lose condition when security reaches 100
- Retry from the lose screen (press R)
- Live HUD showing level, score and security
- Polished menu, win and lose screens

Optional / future:
- Sound effects
- Extra visual assets

---