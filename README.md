# Memory Heist

Memory Heist is a 2D Python learning game built with Pygame. Play as a
hacker escaping a security facility by solving challenges about variables,
operators, loops, lists, dictionaries, functions, and exception handling.

The project was built for the **Coding for AI** course at Bennett
University, under **Dr. Prateek**. The team is upgrading the existing game
to Memory Heist 2.0; development extends the current project instead of
rebuilding it.

See `docs/PROJECT_REPORT.md` for the design document and
`docs/TEAM_WORKFLOW.md` for team branching and integration guidance.

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
├── main.py
├── core/                      # Game loop, player, maps, difficulty, progression
├── entities/                  # Gates, particles, character and drone sprites
├── levels/                    # Level 1-5, Final Vault, shared drawing helpers
├── systems/                   # Inventory, scoring, security, timer, audio, hints, leaderboard
├── ui/                        # Menu, HUD, win/lose screens
├── data/                      # Puzzle content
├── assets/sounds/             # Sound effects
├── saves/                     # Local leaderboard (created at runtime, not committed)
└── docs/                      # Project report and team workflow
```

## Controls

| Key | Action |
|---|---|
| ENTER | Start game from menu |
| 1 / 2 / 3 (menu) | Select Easy / Medium / Hard |
| Mouse | Answer Level 1 & 2 puzzles |
| 1 / 2 / 3 / 4 | Answer Level 3, Level 5, and Final Vault puzzles |
| WASD | Move in spatial levels (currently Levels 3 and 4) |
| E | Collect items / interact in Level 4 |
| C (menu) | Toggle local co-op |
| Arrow keys | Player 2 movement (co-op) |
| Right Shift | Player 2 interact in Level 4 (co-op) |
| Q / X (Level 4) | Ally drone scan / distract the security drone |
| Type + ENTER (win screen) | Enter a name for the leaderboard |
| ESC | Pause during gameplay; quit from the win/lose/menu screen |
| R | Retry from the lose screen |

Close the window using its title bar (X) to quit from the menu or mid-level.

## Current status

The base game has five learning levels and a Final Vault, connected through
the game flow. The team is now adding Memory Heist 2.0 features incrementally.

### 2.0 work merged into main

- A reusable `Room` and `RoomMap` system supports named rooms, exits,
  gates, configurable start rooms, reset, and safe room transitions.
- Gates remain locked until unlocked, and an exit associated with a gate
  cannot be used until the gate is open.
- Core automatically enables player movement and rendering for levels that
  provide room maps, bounds, or obstacles.
- Easy, Medium, and Hard can be selected in the menu. Security penalties
  scale with difficulty; the Level 3 room timer uses the selected time
  multiplier.
- Level 3 currently has a three-room progression with gates, lasers, and a
  security robot. Other levels have not yet been converted to multi-room maps.
- Local co-op: press C on the menu to add a second player (arrow keys,
  Right Shift to interact). In Levels 3 and 4 either player can trigger
  lasers, pass open gates, and interact; the robot scans whichever player
  is closer.
- Pixel-art player sprites (cyan and orange palettes) with a walk
  animation, and sprite drones in Level 4 that change colour when alerted
  or distracted. Sprites are drawn from character maps in code, so no image
  files are needed.
- Gate unlock sparks use the shared particle system.
- Local leaderboard: the win screen asks for a name and shows the top five
  scores with difficulty and co-op tag. Scores are stored in
  `saves/leaderboard.json` on each machine.

### Features Working

- Scoring system (points for correct answers + level completion bonuses)
- Security meter that rises on wrong answers
- Lockdown / lose condition when security reaches 100, with retry
- Live HUD showing level, score, security, and an active timer
- Sound effects (correct / wrong / unlock / click)
- Procedurally generated ambient background audio (no royalty-free music
  file was sourced, so a seamless ambient loop is synthesized in code)
- Animated cyber-grid background and glowing text applied across the
  menu, win/lose screens, and all gameplay levels (1-5 and Final Vault)
- Fade transition between level changes

### Still planned for 2.0

- Multiple question pools and randomized question selection across levels
- Multi-room layouts and gate progression for Levels 1, 2, 4, 5, and Final Vault
- Easy / Medium / Hard effects for any additional timed challenges
- Sprites for the remaining enemies and objects, and more particle effects
- Additional backgrounds, music, and sound effects
- Hints on/off by difficulty (the setting exists but is not applied yet)
