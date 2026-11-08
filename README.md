# Memory Heist

Memory Heist is a 2D Python learning game built with Pygame. Play as Ghost,
a hacker breaking into NovaCorp's tower to steal back the Master Memory chip
from WARDEN, the building's security AI. Every floor teaches a Python idea
(data types, operators, loops, lists and dictionaries, functions and
exception handling), and you open the gates by answering questions about it.
Echo, your partner on the radio, guides you; the story is narrated.

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

Run the automated tests (no window or sound device needed):

```powershell
python -m pytest -q
```

## Controls

| Key | Action |
|---|---|
| ENTER | Start a new run from the menu |
| L (menu) | Continue the saved run, when there is one (progress is saved at each floor) |
| 1 / 2 / 3 (menu) | Select Easy / Medium / Hard |
| C (menu) | Toggle local co-op |
| B (menu) | Badges and stats |
| S (menu or paused) | Settings: music, effects and voice volume, mute |
| F11 | Fullscreen (works on every screen) |
| WASD | Move on Levels 1-4 |
| E | Pick up, drop or answer (Levels 1 and 2); collect or interact (Levels 3 and 4) |
| 1 / 2 / 3 / 4 | Choose an answer on Levels 3, 5 and the Final Vault |
| Arrow keys, Right Shift | Player 2 move and interact (co-op) |
| Q / X (Level 4) | Ally drone scan / distract the security drone |
| ESC | Pause while playing; skip a story card; leave the badges page; quit from the menu |
| R / M (win or lose screen) | Start a new run / return to the menu |
| Type + ENTER (win screen) | Enter a name for the leaderboard |

Close the window using its title bar (X) to quit at any time.

## What the game has

- **Story and voices.** An intro, a briefing before each floor and an
  ending, with the narrator and the radio lines (Echo and WARDEN) spoken.
  Recorded clips live in `assets/voice/`; if a clip is missing, a short
  generated "blip" voice plays instead, so nothing breaks.
- **Floors.** Levels 1, 2 and 5 are rebuilt as walkable floors (tile rooms,
  crates and bins, a maintenance grid, a server hall with a control
  terminal); Level 3 has laser rooms with a security robot; Level 4 has
  the memory vault with drones. Level 4 and the Final Vault are still
  being reworked by their owners.
- **Characters.** Ghost and Echo (co-op) with walk animation and shading,
  animated portraits for Ghost, Echo and WARDEN, and staff NPCs on Floor 1.
  All sprites are drawn from character maps in code, so no image files are
  needed.
- **Sound.** A composed music loop per floor, generated sound effects and
  the voices, with separate Music, Effects and Voice sliders and a mute
  switch in Settings (saved between runs).
- **Presentation.** One theme across all screens (NovaCorp palette, themed
  fonts), a HUD with floating score and security popups, a skyline backdrop
  with searchlights on the menu and end screens, fades between screens and
  an elevator transition between floors.
- **Progress.** Saved run per floor (L on the menu), six badges with a
  Badges and Stats page, and a local leaderboard (top five with difficulty
  and co-op tag).
- **Difficulty.** Easy, Medium and Hard change the timers, hints, security
  penalty and score multiplier.
- **Co-op.** Press C on the menu to add a second player.

Old Level 1, Level 2 and Level 5 can be switched back on for comparison with
the environment variables `MEMORY_HEIST_OLD_LEVEL1=1`,
`MEMORY_HEIST_OLD_LEVEL2=1` and `MEMORY_HEIST_OLD_LEVEL5=1`.

## Voice clips

The spoken lines are mp3 files in `assets/voice/`, named by speaker and a
short hash of the text (for example `echo_1d2150a78f.mp3`). Change a line in
`core/story.py` or `core/comms.py` and that line falls back to the blip voice
until its clip is regenerated.

To regenerate clips you need an ElevenLabs API key:

1. Create a key at https://elevenlabs.io/app/api/api-keys.
2. Put it in a file named `.env` in the project folder, as
   `ELEVENLABS_API_KEY=your-key`. The file is ignored by git: never commit a
   key and never paste one into chat or code.
3. Run:

```powershell
python tools/generate_voice.py --list     # what would be made and the credit cost (nothing is spent)
python tools/generate_voice.py            # make every missing clip
python tools/generate_voice.py --only echo --force   # remake one speaker's clips
python tools/generate_voice.py --premade  # use ElevenLabs' built-in voices instead
```

The default cast (`CAST` in `systems/voice_clips.py`) uses voices created in
the project owner's ElevenLabs account, which other accounts cannot use. On
another account, run with `--premade`, or replace the voice ids in `CAST`.
The whole set is about 2,700 characters, which is about 2,700 credits.

## Project Structure

```text
memory-heist/
├── main.py
├── core/                      # Game loop, story, comms, player, NPCs, sprites, maps, difficulty
├── entities/                  # Gates, particles, character and drone sprites
├── levels/                    # Levels 1-5, Final Vault, shared room and drawing helpers
├── systems/                   # Audio, music, voice, settings, progress, badges, scoring, hints, leaderboard
├── ui/                        # Menu, HUD, story and end screens, settings, theme and fonts
├── data/                      # Puzzle content
├── assets/                    # fonts/, sounds/, voice/
├── tools/                     # generate_voice.py (makes the voice clips)
├── tests/                     # Automated tests (pytest)
├── saves/                     # Settings, progress, badges and leaderboard (created at runtime, not committed)
└── docs/                      # Project report and team workflow
```

## Still planned

- Walkable floors with story and radio lines for Levels 3 to 5 and the
  Final Vault, in the same style as Levels 1 and 2
- More questions per level, with random selection
- More music variety and a credits screen

## Credits

- Fonts: Chakra Petch and Share Tech Mono (SIL Open Font License; the
  licence files are in `assets/fonts/`)
- Voices: generated with ElevenLabs
