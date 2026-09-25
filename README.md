# Memory Heist

An interactive 2D Python learning game built with Pygame. The player is a
hacker escaping the "Memory Vault" by solving puzzles based on core Python
concepts: variables, operators, loops, lists/dictionaries, functions, and
exception handling.

Built for the **Coding for AI** course at Bennett University, under
**Dr. Prateek**.

See `docs/PROJECT_REPORT.md` for the full design document and
`docs/TEAM_WORKFLOW.md` for how the 5-person team collaborates.

## Team

| Member | Area |
|---|---|
| Kshitiz Reddy | Core game system, repo owner/maintainer, integration |
| Paranthama Selvan | Level 1 & Level 2 |
| Yashovardhan Kushva | Level 3 & Level 4 |
| Apporov Sahu | Level 5 & Final Vault |
| Divyash | UI, systems, integration |

## Setup

```powershell
conda create -n ai_env python=3.11
conda activate ai_env
pip install -r requirements.txt
python main.py
```

## Project Structure

```text
memory-heist/
├── main.py                    # Entry point
├── core/                      # Member 1: game loop, player, level manager
├── levels/                    # Members 2-4: levels and shared helpers
│   ├── level1/
│   ├── level2/
│   ├── level3_loops/
│   ├── level4_memory/
│   ├── level5_control/
│   ├── final_vault/
│   └── common/                # Shared drawing/JSON helpers
├── systems/                   # Inventory, scoring, security, timer,
│                              # hints, audio
├── ui/                        # Menu, HUD, win/lose screens
├── data/
│   └── puzzles.json           # Level 1 & 2 puzzle content
├── assets/                    # Sound effects
└── docs/                      # Design document + team workflow notes
```

## Controls

| Key | Action |
|---|---|
| ENTER | Start game from menu |
| Mouse | Answer Level 1 & 2 puzzles |
| 1 / 2 / 3 / 4 | Answer Level 3, 5, and Final Vault puzzles |
| WASD | Move (Level 4 only) |
| E | Collect items / interact (Level 4 only) |
| ESC | Pause during gameplay; quit from the win/lose/menu screen |
| R | Retry from the lose screen |

Close the window using its title bar (X) to quit from the menu or mid-level.

## Status

All 5 levels plus the Final Vault are complete and fully chained.

### Features Working

- Scoring system (points for correct answers + level completion bonuses)
- Security meter that rises on wrong answers
- Lockdown / lose condition when security reaches 100, with retry
- Live HUD showing level, score and security
- Sound effects (correct / wrong / unlock / click)
- Procedurally generated ambient background audio (no royalty-free music
  file was sourced, so a seamless ambient loop is synthesized in code)
- Animated cyber-grid background and glowing text applied across the
  menu, win/lose screens, and all gameplay levels (1-5 and Final Vault)
- Fade transition between level changes

### Possible Future Polish

- Extra visual assets (sprites/icons instead of colored shapes)
- More elaborate animations or particle effects