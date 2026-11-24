# PROJECT REPORT

# MEMORY HEIST
## An Interactive Python Learning Game

---

## 1. Project Title

**Memory Heist: An Interactive Python Learning Game**

---

## 2. Project Type

- **Game Type:** 2D Interactive Puzzle and Adventure Game
- **Programming Language:** Python
- **Framework:** Pygame
- **Project Level:** Intermediate
- **Team Size:** 5 Members
- **Target Development Time:** Approximately 2–3 Weeks
- **Target Version:** Good College-Project Version

---

# 3. Abstract

Memory Heist is a 2D interactive educational puzzle and adventure game designed to help players understand fundamental Python programming concepts through gameplay.

The player takes the role of a hacker who infiltrates a highly secured digital facility known as the Memory Vault. During the mission, the security system detects the player and locks the exit. To escape successfully, the player must navigate through different rooms and solve challenges based on Python programming concepts.

The game focuses on topics including variables and data types, operators and conditional logic, loops, lists and dictionaries, functions, and exception handling. Instead of presenting these concepts only through traditional questions or multiple-choice quizzes, Memory Heist integrates them directly into the gameplay.

For example, lists are used through the player's inventory system, dictionaries are used to retrieve information from a digital vault, loops control repeated security patterns, and functions are used to operate security systems.

The project aims to combine programming education with entertainment by providing an interactive, visually appealing, and easy-to-understand learning experience.

---

# 4. Introduction

Learning programming concepts can sometimes be difficult when students only study definitions and solve traditional exercises. Interactive learning can make programming concepts easier to understand by allowing students to observe and apply concepts in practical situations.

Memory Heist is designed around the concept of **learning by playing**.

The game transforms Python programming concepts into interactive gameplay mechanics. The player does not simply answer questions about Python. Instead, the player uses programming concepts to solve challenges and progress through the game.

The game follows a cyber-security and digital-heist theme to make the experience engaging and visually appealing.

---

# 5. Problem Statement

Traditional methods of learning Python programming often rely on:

- Reading theory
- Memorizing syntax
- Solving isolated programming questions
- Multiple-choice questions

These methods may not always provide an engaging learning experience.

The problem addressed by this project is:

> **How can basic Python programming concepts be presented in an interactive and enjoyable way while still helping players understand their practical use?**

Memory Heist addresses this problem by converting programming concepts into gameplay challenges.

---

# 6. Project Objective

The primary objective of Memory Heist is:

> **To develop a 2D interactive game that teaches fundamental Python programming concepts through puzzles, exploration, and gameplay-based challenges.**

### Secondary Objectives

- Make Python concepts easier to understand.
- Provide an interactive learning experience.
- Encourage logical thinking and problem-solving.
- Combine programming education with entertainment.
- Create a visually appealing 2D game.
- Ensure that the game is easy to play and understand.
- Demonstrate practical Python programming skills.
- Develop a modular and organized software project.

---

# 7. Project Concept

The player takes the role of a hacker who enters a high-security digital facility called the **Memory Vault**.

The player's mission is to retrieve valuable information known as the **Master Memory**.

However, after entering the facility, the security system detects the intrusion.

All exits are locked.

The player must now navigate through different security zones, solve challenges, unlock systems, and finally escape with the Master Memory.

Each security zone is connected to one or more Python programming concepts.

The basic gameplay flow is:

**Explore → Interact → Understand the Challenge → Solve the Puzzle → Receive Feedback → Unlock the Next Area**

---

# 8. Storyline

The player enters the highly secured Memory Vault to complete a digital heist.

Shortly after entering the facility, the security system displays:

**INTRUDER DETECTED**

The facility enters lockdown mode, and all exit doors are locked.

To escape, the player must bypass different security systems.

Each security system requires the player to understand and apply a Python programming concept.

The player gradually progresses through multiple levels and eventually reaches the final location: the **Master Vault**.

The final mission requires the player to combine knowledge gained from previous levels.

After retrieving the Master Memory and escaping the facility, the player successfully completes the mission.

---

# 9. Main Learning Approach

The main educational principle of Memory Heist is:

## Learn by Doing

The player follows the learning process:

**Concept → Interaction → Challenge → Solution → Feedback → Understanding**

The game is designed to avoid becoming a simple quiz with a game background.

Instead, Python concepts are connected to actual gameplay mechanics.

Examples include:

- **Lists** are used for the player's inventory.
- **Dictionaries** store and retrieve vault information.
- **Loops** control repeated laser and robot movements.
- **Functions** operate security systems.
- **Exception handling** helps recover from system errors.

This allows the player to see the practical use of each concept.

---

# 10. Python Topics Covered

The game will cover the following Python topics:

1. Variables and Data Types
2. Operators and Conditional Logic
3. Loops
4. Lists and Dictionaries
5. Functions and Exception Handling
6. Combined Application of Concepts

---

> **Note.** Sections 1-10 and 24-33 are the original proposal and are kept as written. Sections 11-23 were rewritten at the end of the project to describe the game as it was actually built; section 34 records how it got there.

# 11. Game Structure

The finished game is one run through NovaCorp's tower: five floors and WARDEN's core, each teaching one Python idea. Every floor is a walkable room built on one shared kit (tile map, lighting, NPCs, badge doors), so the player learns by doing the job the room asks for, not by answering a quiz screen.

**Menu** → **Intro story** → **Floor 1 – Reception Lobby** (data types) → **Floor 2 – Maintenance Grid** (operators) → **Floor 3 – Night Patrol** (loops) → **Floor 4 – Records Archive** (lists and dictionaries) → **Floor 5 – Server Hall** (functions and exceptions) → **Final Floor – WARDEN's Core** (everything combined) → **Ending and win screen**

Before each floor a story card names the concept and the job; between floors the crew rides the elevator. The run is saved at every floor reached.

---

# 12. Floor 1 – The Reception Lobby (data types)

The intake belt is jammed, so parcels lie around the lobby, each stamped with a real Python value such as `"A-4471"`, `-7`, `9.99` or `True`. Ghost carries each parcel (E) to the chute for its type: `int`, `str`, `float` or `bool`. The right chute is Python's own `type(value)`, so the game can never disagree with the language. Two parcels open a gate; three gates open the badge door.

- Wrong chute: the parcel comes back, security +20, score -10.
- The receptionist, guard and cleaner patrol and talk; the filing cabinets read out the chute rules; lost visitor badges are bonus points.

**Learning outcome:** values have types, and the type decides what a value is for.

---

# 13. Floor 2 – The Maintenance Grid (operators)

A snaking utility tunnel with three relay bays. Each relay screen asks a question written fresh each run: Relay 1 "What does `7 + 3 * 2` evaluate to?" (precedence, `//`, `%`, `/` giving a float, `**` grouping from the right), Relay 2 "Which x makes `3 < x <= 6` True?" (boundaries, chains), Relay 3 "Which x makes `x < 3 or x > 5 and x != 8` False?" (`and`/`or`/`not` and their precedence). Ghost stands on the breaker plate that answers it and throws it (E); the other three plates are the mistakes beginners make. A right answer powers the next gate; a wrong one raises security. Floor panels show expressions too, and the ones that evaluate to `True` are live and zap (score only).

**Learning outcome:** arithmetic, comparison and logical operators, and how Python evaluates an expression to one value.

---

# 14. Floor 3 – The Night Patrol (loops)

Three rooms, each running a short loop shown on its PATROL LOOP board, and the room does exactly what the code says: in the staff corridor a `for lane in range(...)` decides which lane columns fire and in what order; in the camera gallery a `while` loop with a counter decides which cameras sweep; in the checkpoint hall a `for` nested in the droid's `while patrol():`, sometimes with `break` or `continue`, decides which tripwire rows fire. The door question asks about that loop (which lanes fire, which fires first, what the counter is when the loop stops), so Ghost can read the code or watch the room to check it. The door's badge reader takes the answer, so Ghost has to cross the room first; answer with keys 1-4 at the door before the room timer runs out; the door scans his badge and slides open. The code and answers are generated each run and checked by running real Python.

- A wrong answer or the room timer running out raises security; lane hits and the droid spotting Ghost cost points only.

**Learning outcome:** `for` and `while` loops, `range()`, and reading a repeating pattern.

---

# 15. Floor 4 – The Records Archive (lists and dictionaries)

The archivist's request slips come down a tube, one at a time, against a clock:

1. **List indexing.** Pull the shelf box at the index the slip asks for (`shelf[-1]`, `shelf[2]`...).
2. **Dictionary lookup.** Open the card-catalogue drawer for a key.
3. **Feeding the vault.** Put the right item from Ghost's satchel (a list) into the intake tray.

Echo's ally drone can scan the shelves (Q) or lure the security drone away (X) while it patrols the aisle.

**Learning outcome:** lists, indexing (including negative indices), dictionaries and key-value lookup.

---

# 16. Floor 5 – The Server Hall (functions and exceptions)

Every machine is a function with its `def` stencilled on the casing. The job ticket asks for three jobs:

1. **Router (arguments):** patch the cable to the port whose value lands in a parameter.
2. **Press (return values):** route the conveyor to the bay the return value goes to.
3. **Reactor (exceptions):** pull the `except` breaker that catches its error before the reactor overheats.

Then Ghost types an access level into WARDEN's console, and a real `try/except` runs it. Steam vents cost points (score only).

**Learning outcome:** calling functions, parameters and arguments, return values, and `try/except`.

---

# 17. Final Floor – WARDEN's Core (everything combined)

A round chamber with six locks around WARDEN's eye, one for each lesson. Each lock's terminal shows a short piece of code; Ghost stands on the plate with the right answer and presses E, while a searchlight sweeps the floor. The locks can be opened in any order. When all six are open the iris opens, Ghost takes the Master Memory chip (+150), and the extraction door opens.

**Outcome:** ACCESS GRANTED, MASTER MEMORY ACQUIRED, ESCAPE SUCCESSFUL.

---

# 18. Gameplay Design

Every floor follows the same loop: **explore → read the code in the room → act on it → see the result → move on.** Answers are physical: a chute, a breaker plate, a shelf box, a cable port, a floor plate. Correct answers are checked by running real Python, so the game and the language always agree. Short code is shown everywhere; the player never has to type a program, except the one-line access level on WARDEN's console.

---

# 19. Game Features

- **Movement and co-op:** Ghost moves with WASD; press C on the menu to add Echo as Player 2 (arrow keys, Right Shift).
- **Score:** points for right answers, floors and bonuses; mistakes and hazards cost points.
- **Security meter:** mistakes raise it; at 100 the tower locks down and the run is lost. It cools in the lift after each floor: the lift takes off half the meter, and never less than 25. (The proposal's lives system was replaced by this meter.)
- **Timers:** a whole-run clock (15 minutes on Medium) and a per-question clock on Floors 2-5, both scaled by difficulty.
- **Hints:** H shows a hint for a small score cost; off on Hard.
- **Difficulty:** Easy, Medium and Hard change the clocks, hints, security penalty and score multiplier.
- **Story and radio:** intro, a briefing card per floor and an ending, with narrated and spoken lines; Echo and WARDEN talk over the radio during play.
- **Progress:** the run is saved at each floor (Continue on the menu); after a loss, F retries that floor and R starts a new run.
- **Badges, stats and leaderboard:** six badges, a stats page with the deepest floor reached, and a local top-five leaderboard.
- **Sound:** procedural music per floor, generated sound effects and recorded voices, with volume settings.

---

# 20. Controls

| Key | Action |
|---|---|
| WASD | Move |
| E | Act: pick up, throw, pull, open, stand-and-answer |
| 1-4 | Answer at a Floor 3 door |
| H | Hint (where hints are on) |
| Q / X | Floor 4: ally drone scan / lure |
| Arrow keys, Right Shift | Player 2 (co-op) |
| ESC | Pause; skip a story card; quit from the menu |
| F / R / M | After a loss: retry the floor / new run / menu |
| F11 | Full screen or window |

The menu shows these controls before the run starts.

---

# 21. Visual Design

A grim, surveillance-state pixel-art look in the style of Beholder: NovaCorp propaganda posters, WARDEN's red eye on screens and walls, steel badge doors that scan and slide, dynamic lighting with soft shadows, dust motes, steam and sparks. Each floor has its own layout and colour mood, getting warmer and redder as the crew nears the core. The 16:9 window frames the 3:2 play area with NovaCorp wall panels. All sprites, NPCs and portraits are drawn from character maps in code.

---

# 22. Technology Stack

- **Language:** Python 3.11
- **Framework:** Pygame 2.6
- **Data:** JSON for puzzles, settings, saves and the leaderboard
- **Audio:** music composed in code (NumPy), generated sound effects, voices recorded with ElevenLabs
- **Fonts:** Chakra Petch and Share Tech Mono (SIL Open Font License)
- **Testing:** pytest, more than 2,000 automated tests, run headless
- **Version control:** Git and GitHub

---

# 23. Project Structure (as built)

```text
memory-heist/
├── main.py
├── core/        game loop, level manager, story, comms, player, NPCs, sprites, tile maps, difficulty
├── levels/      the five floors and WARDEN's core, their decor and request generators,
│                the shared room kit (room_base, lighting, badge_door, depth_fx, novacorp_style)
│   └── legacy/  the first versions of Floor 1, Floor 4, the server hall and the Final Vault
├── systems/     audio, music, voice, settings, progress, achievements, scoring, hints, leaderboard
├── ui/          menu, HUD, story and end screens, settings, theme, fonts, side strips
├── entities/    gates, particles, sprites
├── data/        puzzle content
├── assets/      fonts, sounds, voice clips
├── tools/       voice-clip generator
├── tests/       automated tests
└── docs/        this report and the team workflow
```

---

# 24. Team Member Division

The project will be divided among five members.

## Member 1 – Core Game System

Responsibilities:

- Pygame setup
- Main game loop
- Player movement
- Collision detection
- Game states
- Level transitions

---

## Member 2 – Levels 1 and 2

Responsibilities:

### Level 1

- Variables
- Data types
- Security Gate

### Level 2

- Operators
- Conditional logic
- Security Grid

---

## Member 3 – Levels 3 and 4

Responsibilities:

### Level 3

- Loops
- Laser movement
- Robot patrol patterns

### Level 4

- Lists
- Dictionaries
- Inventory system
- Memory Vault challenges

---

## Member 4 – Level 5 and Final Challenges

Responsibilities:

- Functions
- Parameters and arguments
- Exception handling
- Control and Recovery Center
- Final Vault puzzle logic

---

## Member 5 – User Interface and Integration

Responsibilities:

- Main menu
- HUD
- Score system
- Lives system
- Timer
- Hint system
- Security meter
- Sound integration
- Final integration
- Testing

Each member must contribute meaningful Python code and understand the modules assigned to them.

---

## As built: who made what

The division above was the plan. The finished game credits each part to the member who first built it and, where a floor was later rebuilt on the shared kit, to who rebuilt it. The original versions are kept in `levels/legacy/` (or still extended by the rebuild), so every member's work is still in the project.

| Part | Originally built by | Rebuilt / extended by |
|---|---|---|
| Core game system, shared room kit, integration | Kshitiz Reddy (Member 1) | – |
| Floor 1 – Reception Lobby | Paranthama Selvan (Member 2), question-screen Level 1 | Kshitiz Reddy: walkable lobby |
| Floor 2 – Maintenance Grid | Paranthama Selvan (Member 2), Level 2 | Kshitiz Reddy: the tunnel extends Level 2 |
| Floor 3 – Night Patrol | Yashovardhan Kushva (Member 3), the laser loop rooms | Kshitiz Reddy: badge doors, droid, room dressing |
| Floor 4 – Records Archive | Yashovardhan Kushva (Member 3), memory vault | Kshitiz Reddy: walkable archive |
| Floor 5 – Server Hall | Apporov Sahu (Member 4), control and recovery centre | Kshitiz Reddy: the hall extends Level 5 and keeps its console |
| Final Floor – WARDEN's Core | Apporov Sahu (Member 4), master vault | Kshitiz Reddy: the round core |
| Menu, HUD, screens and systems | Divyash (Member 5) | Kshitiz Reddy: theme, side strips, polish |

---

# 25. Development Plan

## Week 1 – Core Development

### Day 1–2

- Finalize project structure
- Create GitHub repository
- Set up Pygame
- Create initial game window
- Create folder structure

### Day 3–4

- Implement player movement
- Implement room structure
- Implement collision detection
- Create interaction system

### Day 5–7

- Develop Level 1
- Develop Level 2
- Develop Level 3

### Week 1 Goal

A basic playable prototype.

---

## Week 2 – Main Game Development

### Day 8–10

- Develop Level 4
- Implement inventory
- Implement dictionary challenges

### Day 11–12

- Develop Level 5
- Implement functions and exception challenges

### Day 13–14

- Develop final challenge
- Implement score system
- Implement lives
- Implement timer
- Implement security meter

### Week 2 Goal

A complete playable game.

---

## Week 3 – Polishing and Testing

### Day 15–17

- Improve graphics
- Improve user interface
- Add animations
- Add sound effects

### Day 18–19

- Test all levels
- Fix bugs
- Balance difficulty
- Improve hints and feedback

### Day 20–21

- Prepare README documentation
- Prepare project presentation
- Practice demonstration
- Practice explaining individual code

### Final Goal

A polished and fully functional college project.

---

# 26. Minimum Viable Product

The following features are essential.

- 2D player movement
- Five learning levels
- Final challenge
- Python concept-based puzzles
- Interactive objects
- Level progression
- Score system
- Lives system
- Tutorial
- Win and lose conditions
- Clean user interface

These features must be completed before adding extra features.

---

# 27. Optional Features for Additional Polishing

If additional time is available, the following features may be added:

- Sound effects
- Background music
- Animated doors
- Advanced laser effects
- Moving security robots
- More puzzle variations
- Improved visual effects
- Additional hints
- Save and progress system
- More detailed story sequences

These features are optional and should not delay completion of the core game.

---

# 28. Evaluation Based on Project Rubrics

The project has been designed around the four given evaluation criteria.

## Rubric 1 – Code Submission

Memory Heist will demonstrate:

- Modular programming
- Multiple Python modules
- Functions
- Classes where appropriate
- Event handling
- Collision detection
- Game state management
- Lists and dictionaries
- Exception handling
- JSON data handling
- User interface logic

### Strength

The project has a strong potential for code evaluation because it is not limited to a single Python file.

---

## Rubric 2 – Understanding of Code

Each team member will have clearly defined responsibilities.

Every member should understand:

- Their own code
- Their Python concepts
- How their module connects to the main game

The project itself also makes Python concepts visible through gameplay.

### Examples

- Lists manage inventory.
- Dictionaries store vault information.
- Loops control repeated security patterns.
- Functions operate systems.
- Exceptions handle invalid situations.

### Strength

The project has strong potential for demonstrating practical understanding.

---

## Rubric 3 – Visual Appeal

The game will use:

- A consistent cyber-security theme
- Attractive menus
- Digital rooms
- Interactive terminals
- Laser effects
- Security robots
- HUD elements
- Score and alert animations
- Sound effects if time allows

The focus will be on creating a clean and consistent visual experience rather than overly complex graphics.

### Strength

Visual appeal can be significantly improved during the polishing stage.

---

## Rubric 4 – Easy to Play and Understand

The game will include:

- Simple controls
- A tutorial
- Clear objectives
- Gradual difficulty progression
- Immediate feedback
- Hints
- Clear win and lose conditions

The gameplay flow will remain simple:

**Move → Explore → Interact → Solve → Progress**

### Strength

The project is designed to be understandable even for a new player.

---

# 29. Expected Project Level

Memory Heist is classified as an **Intermediate-Level Python Project**.

The project combines:

- Python programming
- Pygame
- Event handling
- Game loops
- Player movement
- Collision detection
- Puzzle logic
- Data structures
- Functions
- Exception handling
- User interface development
- Modular programming

The project is more complex than a basic beginner game while remaining achievable for a five-member student team.

---

# 30. Project Feasibility

The project is feasible because it does not require:

- 3D graphics
- Multiplayer networking
- Large databases
- Complex machine learning models
- Online servers
- Advanced game engines

The main requirements are:

- Python knowledge
- Pygame
- Basic game assets
- Modular development
- Team coordination

With five members and a planned development period of approximately two to three weeks, the Good College-Project Version is achievable.

---

# 31. Risks and Solutions

## Risk: Project becomes too large

**Solution:** Complete the core five levels before adding optional features.

## Risk: Game looks like a quiz

**Solution:** Connect Python concepts directly to gameplay mechanics.

## Risk: Members do not understand each other's code

**Solution:** Conduct regular code-sharing sessions and explain modules to the entire team.

## Risk: Integration problems

**Solution:** Use GitHub and define clear module interfaces.

## Risk: Visual design takes too much time

**Solution:** Use simple but consistent 2D assets and focus on polish after core functionality is complete.

---

# 32. Expected Outcome

At the completion of the project, the team will have developed a working 2D Python game where players can:

- Explore a digital environment
- Interact with game objects
- Solve Python-based challenges
- Learn programming concepts
- Progress through multiple levels
- Manage items
- Avoid security systems
- Complete a final combined challenge

The project will demonstrate both technical programming ability and creative game design.

---

# 33. Conclusion

Memory Heist is an interactive 2D educational game designed to make Python learning more engaging and practical.

The project combines programming concepts with game mechanics instead of relying only on traditional questions or quizzes.

The player learns concepts such as variables, operators, loops, lists, dictionaries, functions, and exception handling by applying them during gameplay.

The project has been designed to meet the following key requirements:

- Strong and organized code submission
- Clear understanding of code and concepts
- Good visual appeal
- Easy and interactive gameplay

The project scope is appropriate for an intermediate-level college project and is achievable by a team of five members within approximately two to three weeks.

The final goal of Memory Heist is to demonstrate that programming concepts can be transformed into an enjoyable and interactive learning experience.

# 34. Implementation Notes

This section describes how the game was actually built, from the integrator's side (Member 1, core system and integration). It is written for a reader who has the code open: every item names the file that implements it.

## 34.1 How the game is put together

The game is one loop in `core/game.py`. A `Game` object owns a small state machine (`menu`, `intro`, `briefing`, `playing`, `outro`, `win`, `lose`) plus a `paused` flag and a settings panel that can open over the menu or the pause screen. `core/level_manager.py` holds the six levels and moves from one to the next when `is_complete()` becomes true.

Every level is a class with four methods: `update(dt)`, `render(surface)`, `handle_event(event)` and `is_complete()`. A level that wants the shared player movement also exposes `room_map.blocked(rect)`, and the game then moves and draws the players for it. This is the whole contract between a level and the rest of the game, which is why five people could build levels in parallel without touching each other's files.

Systems that need to react to the game (sound effects, music, mood colouring, the radio feed, the floor results) do not live inside the levels. Each one is an observer: once per frame the game hands it a snapshot (state, score, security, level, gates passed) and it decides what to do. `SoundEvents`, `Atmosphere`, `MusicPlayer` and `CommsFeed` all work this way, so no level ever calls them.

## 34.2 What was added to the game

| Area | What it does | Where |
| --- | --- | --- |
| Shared look | One palette, one colour per floor, panels, buttons, dialogue box, text typing | `ui/theme.py`, `ui/kit.py` |
| Motion | Easing curves, tweens, sprite animation, squash and stretch, screen shake | `core/easing.py`, `core/animation.py` |
| Music | Adaptive background music made in code: one key per floor, three stems (pad, pulse, alert) that fade in and out with danger | `systems/music.py` |
| Sound effects | Pickup, drop, footstep and door sounds made in code, on top of the original `.ogg` files | `systems/sfx.py`, `systems/audio.py` |
| Radio feed | WARDEN and teammate lines that appear at the bottom of the screen when something happens | `core/comms.py`, `ui/comms.py` |
| Characters | Ghost and Echo walking sprites, and animated portraits for Ghost, Echo and WARDEN | `core/hero_sprites.py`, `core/hero_portrait.py` |
| Map tools | Tile maps drawn from text layouts, with a camera that follows and shakes | `core/tilemap.py` |
| Reference floor | A fully rebuilt Floor 1 (Reception Lobby): walk around, carry crates to the right data-type bin | `levels/floor1_lobby.py` |
| HUD | Floor name in the floor's colour, counting-up score, cell security meter, timer pill | `ui/hud.py` |
| Screens | Restyled menu, win and lose screens with a shared animated backdrop | `ui/menu.py`, `ui/screens.py`, `ui/backdrop.py` |
| Between floors | Elevator-door transition, restyled pause panel, "floor cleared" panel with stars, points, time and mistakes | `ui/transitions.py`, `ui/overlays.py`, `core/floor_stats.py` |
| Settings | Music volume, effects volume and mute, saved between runs | `systems/settings.py`, `ui/settings_screen.py` |

## 34.3 Design decisions and why

1. **Sound and music are generated, not downloaded.** No royalty-free music file was available, and every outside file is a licensing question. The music and effects are short numpy waveforms, so the repository stays small and nothing needs credit. The cost is a simpler sound than recorded music.
2. **The tile map is our own, under 200 lines.** The usual library (pyscroll) is GPL-licensed, which would force the whole project under the same licence. The game only needs solid tiles, a camera and drawing, so writing it was cheaper than the licence question.
3. **Teammates' levels were restyled, not rewritten.** Levels 3 and 4 in particular had a lot of debugged behaviour. The shared layer therefore only changes how a level looks and fits (palette, panels, free HUD and radio strips). Questions, hints, scoring, the drone and the gate logic are untouched, and a floor is only rebuilt when its owner agrees.
4. **The rebuilt Floor 1 is now Level 1.** It started opt-in so the finished game never depended on an unfinished replacement. Once it was tested and polished it became the default. The original question-screen Level 1 is kept in `levels/level1.py` and returns with the environment variable `MEMORY_HEIST_OLD_LEVEL1=1`.
5. **Audio channels are reserved.** The mixer was running out of channels once the music stems were playing, which silently dropped sound effects. Channels 0 to 5 now belong to the music and the rest to effects.
6. **The floor results need no new game state.** The game stores a snapshot of score, time and mistakes when a floor starts and shows the difference on the next briefing card. Time spent reading cards is not counted, because the run clock is frozen there.
7. **Settings never touch the tests.** A test fixture points the settings file at a temporary folder, so a developer's saved volume cannot change a test result and tests never write to `saves/`.
8. **Floor 2 is rebuilt as a walkable maintenance grid.** The rules of the old Level 2 are unchanged (same question pool, per-question clock, +points, security +20 / score -10 on a wrong pad, security +25 / score -15 on a timeout, +100 for walking out), so scores stay comparable. Only the presentation changed: three chambers, a wall screen showing the question, answer pads on the floor, energy gates that retract, and a technician who gives tips. The room is `levels/level2_grid.py`, its drawing is `levels/grid_decor.py`, and the plumbing shared with later floors is `levels/room_base.py`. The original returns with `MEMORY_HEIST_OLD_LEVEL2=1`.
9. **Levels 1 and 2 got a readability pass.** Floor 1 now shows what you can do at that moment: a crate within reach gets a pulsing ring and an E key, and a bin glows when you are carrying a crate toward it. Floor 2 fits each screen prompt to the biggest font that stays on two lines, has an EXIT sign, hazard stripes under the gates, bay labels painted on the floor, and chevrons that run toward the exit once its door opens.
10. **The main menu got a polish pass.** The title glows and shimmers now and then, the two hero portraits bob (out of step with each other), Echo fades in and out when co-op is toggled instead of snapping, the chosen difficulty chip flashes when it changes, and a line under the chips states what the difficulty really changes (timer, hints, security penalty and score multiplier, read from the presets). The how-to-play panel now describes the walkable Levels 1 and 2.
11. **The HUD shows what just changed.** A gold "+50" or coral "-10" floats up and fades beside the score, a coral "+N" does the same beside the security meter, and the meter flashes bright for a moment when security rises. Big jumps (a run reset or bonus screen) are ignored so the HUD never spams.
12. **The win and lose screens count the score up.** The final score ticks up over about three-quarters of a second instead of appearing at once, the win screen restarts that count each time it opens, and empty leaderboard slots show as dim "- - -" rows so the table never looks half-drawn.
13. **Characters got depth.** Every hero and NPC sprite now has a shading pass (lit top edges, darker undersides and right edges, eyes and visors untouched), and the stride frames squash and stretch so the head bobs as they walk. Both come from the shared sprite builder, so Ghost, Echo, the guard, the receptionist and the technician all get them.
14. **Save and continue.** Each time a floor is cleared, the run is saved to `saves/progress.json` (floor, score, time left, difficulty, co-op). When a save exists the menu shows "L: continue (Floor 3 - 450 pts)", and pressing L resumes that floor with its briefing, score, clock and settings. Winning clears the save; losing keeps it. A missing or damaged file just means no Continue. Logic is in `systems/progress.py`; tests never touch the real save (`MEMORY_HEIST_PROGRESS`).
15. **Badges and stats.** Six badges (First Escape, Flawless, Speed Runner, Dynamic Duo, Nerves of Steel, Veteran) are earned by how a run is won; the win screen shows the ones earned this run, with new ones in solid gold. Pressing B on the menu opens a Badges & Stats page (wins, losses, best score, best time left, and every badge with how to earn it). A run resumed with Continue never counts as flawless or fast. Stored in `saves/stats.json` by `systems/achievements.py`; tests never touch the real file (`MEMORY_HEIST_STATS`).
16. **Backdrops and screen changes.** The menu, win, lose and badges screens now have a NovaCorp skyline along the bottom with windows that switch on and off, and two searchlight beams sweeping the sky (all cached surfaces, about 1.4 ms per frame). Screens also fade in from black (0.35 s) instead of cutting, while levels still arrive through the elevator doors. The scenery is on by default and `draw_backdrop(..., scenery=False)` turns it off.
17. **Recorded narration.** Story cards and radio lines can now play real voice clips from `assets/voice/` (narrator, Echo, warden). Clips are named by speaker and a hash of the text, so editing a line simply drops back to the old blip voice until its clip is regenerated. `python tools/generate_voice.py` makes the clips through the ElevenLabs API using the key in the git-ignored `.env`; it skips clips that already exist, retries rate limits, and `--list` shows the work and credit cost without spending anything. Clips follow the sound-effects volume and the mute setting.
18. **Voice volume.** The settings panel has a third slider, VOICE, between Effects and Sound. It sets how loud the recorded narration, the radio lines and the talking blips are, separately from the sound effects; 0% turns the voices off while leaving the effects on. The value is saved with the other settings (older settings files simply get 100%), and moving the slider plays a sample line so the level can be judged. The Sound (mute) switch still silences everything.
19. **Floor 5 is rebuilt as a walkable server hall.** The rules of the old Level 5 are unchanged: the same question pools, five questions in three gates (parameters, return values, exceptions), +40 per question, security +20 / score -10 and the option struck out on a wrong answer, hints that cost 10 points (15 on Hard) and are off on Hard, and the control terminal that runs a real `try`/`except` (letters give a genuine `ValueError` from `int()`, a number below 5 makes `unlock_vault` raise, +50 and the +100 bonus for a level of 5 or more). Only the way you play it changed. It uses Floor 2's three-chamber plan: the program is on the wall in two code blocks with the lines a question is about lit up, the question is on the screen of the chamber you stand in, and the four answers are pads on the floor (E, or Right Shift for the second player). After the last question the control terminal in the south-east corner wakes up; press E beside it, type an access level, ENTER runs it, and the arrow keys step away. While someone types, the game stops reading the walking keys (a generic `movement_locked` flag on the level), so typing a W or an A does not move anyone. The exit door opens when the terminal accepts you and the level ends when you walk through it. The class extends `Level5ControlCenter` (`levels/level5_hall.py`, art in `levels/hall_decor.py`), so the scoring code exists once; the old screen is kept and returns with `MEMORY_HEIST_OLD_LEVEL5=1`. 63 new tests cover the geometry (every pad and the console are reachable, props leave the lane and spawns free, every prompt, answer, hint and explanation fits its screen, pad or the readout strip), the rules, the terminal and a whole run in the real game; 27 deliberate breakages were each caught.
20. **The Final Vault is rebuilt as a walkable Master Vault.** The rules of the old Final Vault are unchanged: the same six stages (data types, operators, loops, dictionaries, functions, exceptions) with the same questions, code and answers, +50 per stage, +150 for unlocking the vault, security +20 and score -10 for a wrong answer, and the stage 6 terminal that shows a `ValueError` being caught (+5 security for text or a wrong number, and it never finishes the level by itself). It reuses the Floor 2 and Floor 5 plan with two stages in each chamber: the stage's objective is on the wall screen, its code is on a monitor under it with the blank line lit, and the three answers are pads on the floor (E, or Right Shift for the second player). Gate 1 opens after stage 2, gate 2 after stage 4, and the vault door after stage 6; the level ends when you walk through it. Stage 6 also has a console you walk up to, press E, and type at (arrow keys step away). This fixes a known bug of the old screen: 1, 2 and 3 were answer keys, so those digits could not be typed into the stage 6 terminal. The class extends `FinalVault` (`levels/final_vault_hall.py`, art in `levels/vault_decor.py`) and the old screen returns with `MEMORY_HEIST_OLD_FINAL_VAULT=1`. 41 new tests cover the geometry (including that standing at the console is never standing on a pad), the rules against the old numbers, the terminal and a whole run in the real game; 30 deliberate breakages were each caught or the dead line removed.
21. **Floor 1 gets a camera beam, hidden chips and usable props.** The crate rules and scoring are unchanged. New: the WARDEN camera sweeps a narrow beam across the lobby floor; standing in it for about half a second gets you spotted, which costs 5 score and never touches the security meter, so a spotting cannot end a run or spoil a no-mistakes badge. After a spotting the camera rests for 3 seconds, and it gives up after 4 spottings. Running across the beam is safe; lingering in it is not. Three visitor chips are hidden on open floor (chosen from seven spots by the level's seed, using their own random generator so the crate layout is untouched): walking over one gives +10 and finding all three gives +30 more. E with empty hands next to the reception desk rings the bell (the receptionist answers) and E next to the vending machine gives a one-time +5. A crate in reach always wins over a prop. The code is in `levels/lobby_extras.py`, with hooks in `levels/floor1_lobby.py`. 26 new tests cover the beam geometry, spotting and cooldown, chip placement and scoring, the props and drawing; every deliberate breakage was caught.
22. **The NovaCorp sound pack.** Fourteen new synthesized effects join the original four in `systems/sfx.py`, all built with numpy so there are no files and no licences: `bell`, `vending`, `chip`, `alarm` (the harsh two-tone buzz for a mistake), `switch`, `zap`, `drone`, `laser`, `stamp`, `chime` (the intercom ding-dong), `fanfare`, and a footstep for each kind of floor (`step_metal`, `step_server`, `step_marble`; plain `step` stays tile and carpet). `Audio` loads them all by name, so a level plays one with `audio.play("bell")`. To listen to them, run `python tools/sound_test.py` (all of them, one after another, each with its name) or `python tools/sound_test.py bell zap`. 59 sound tests check each effect's character (the bell rings at 1760 Hz, the chip and fanfare rise, the laser falls, the alarm alternates two pitches, the marble step has an echo and so on); every deliberate breakage was caught.
23. **The NovaCorp look, starting with Floor 1.** `levels/novacorp_style.py` is the shared look for every floor: a grade that washes colour out toward grey with a faint yellow cast, dark corners and film grain; floor grime (smudges, scuffs, a crack); faded floor stencils and painted dashed lines; filing cabinets, a water cooler and propaganda posters (a watching eye and a slogan); and a ceiling PA speaker. The `PA` class makes a short announcement every 28 seconds (the first after 8), plays the intercom chime and shows the line as a caption beside the title. Floor 1 now uses all of it: a graded and stained lobby, "PLEASE REMAIN VISIBLE" on the rug, a "WAIT HERE" queue line, two posters on the left wall, two cabinets and a cooler (solid, with the exit and every crate and chip spot still reachable), and the new sounds: the bell rings `bell`, the vending machine plays `vending`, a chip plays `chip`, being spotted plays `alarm`. 33 new tests; every deliberate breakage was caught except two that change nothing you can see or hear.
24. **Four more faceless staff, and Floor 1's cleaner.** `core/npc_sprites.py` gains a cleaner, an engineer, a sysadmin and a curator, drawn in muted colours with blank faces like the rest of the NovaCorp look; each has its own voice in `systems/voice.py` (the cleaner tired and sighing, the engineer gruff, the sysadmin quick and nervous, the curator slow and pompous). Floor 1 now has the cleaner mopping a slow route along the bottom left of the lobby and muttering a line when a player comes close ("Mind the wet floor."). The engineer, sysadmin and curator are ready for Floors 2, 5 and the Final Vault. 7 new tests.
25. **Raised walls and real lighting.** Walls are no longer flat lines: `draw_walls` in `levels/novacorp_style.py` gives every wall a lit face with panel seams, a chair rail, a baseboard, a bevelled cap and a soft shadow on the floor beside it, using the room's tile map so it works for any floor. `levels/lighting.py` adds a light map: a dim cool ambient layer, soft coloured light pools that multiply over the scene, a bloom on the brightest pixels, and soft shadows under crates, staff, furniture and props. Floor 1 lights its wall lamps, a ceiling panel, the reception desk lamp, the vending machine, the elevator, the exit lamp (coral then teal), the camera LED (red when alerted) and the sweeping beam's own pool, and each hidden chip glows. The player is drawn after the level, so it stays unlit and stands out as the focus. One frame of Floor 1 takes about 13 ms in the test sandbox. 18 new tests (8 for walls, 10 for lighting).
26. **Floor 1 now has a reason: parcel intake.** Reception is also NovaCorp's mail room and Ghost walks in as a courier, so sorting makes sense in the story. The rules, points and security effects are unchanged; only the wording and feel changed. The wall prompt reads "File each parcel in the chute for its type.", picking one up says "Got 42. Which chute?", a correct filing plays the `stamp` sound and says "42 is an int. Stamped!", a faded stencil "PARCEL INTAKE - FILE BY DECLARED TYPE" sits above the chutes, and the Level 1 story card tells the courier story. The staff speak in character (the guard says "Move along, courier." and scolds "Wrong chute, courier.", the receptionist says "Stamped. Next."), the three lamps above the exit are labelled STAMPS, and finishing says "All parcels stamped. The elevator is waiting." The strings live in constants at the top of `levels/floor1_lobby.py`, and the wall-width test reads those same constants so they cannot drift. The design reasons are in the "Memory Heist: Floor Concept Plan" doc.
27. **Floor 1 gets a reason for every object, and more game feel.** *Why are the parcels on the floor?* The intake belt above the chutes is jammed (jammed parcels sit at its left end, a red lamp blinks, and a sign reads "BELT OUT OF ORDER / FILE BY HAND"), so a courier has to file them by hand; the story card and the wall prompt say so. *Why does Ghost look the same?* While Floor 1 runs, Ghost (and Echo in co-op) wear a courier disguise: a red delivery cap and a hi-vis orange vest with a silver reflective stripe, built in `core/hero_sprites.py` (`make_hero_frames(name, outfit="courier")`, `Player.set_outfit`). The disguise is applied when the floor starts running, so a continued run at a later level is not dressed, and it comes off when the floor is finished. The crates are now cardboard parcels with packing tape and a shipping label. `levels/lobby_juice.py` adds game feel without touching any rule or score: a filed parcel arcs into its chute, floating +25 and -10 pop-ups, a STREAK counter from two in a row (and an x3! pop-up), chute pipes with chevrons flowing toward each bin that flash when a parcel lands, a slow ceiling-fan shadow and one flickering wall lamp. 35 new tests.
28. **The game starts full-screen.** As a laptop/PC game it now opens full-screen by default; F11 switches to a window and back on every screen, and the choice is saved in `saves/settings.json` (`fullscreen`, default true) so the next start matches. The picture is still drawn at 960 by 640 and scaled to the screen with mouse positions mapped back; scaling is now smoothed (`SDL_RENDER_SCALE_QUALITY=1`) so pixels do not shimmer at fractional sizes. If the machine refuses full-screen the game falls back to a scaled window and then a plain one. Setting `MEMORY_HEIST_WINDOWED=1` forces a window (useful for screenshots), and test runs never go full-screen. On a wide 16:9 screen the 3:2 picture has dark bars at the sides. 9 new tests.
36. **Floor 2 live panels: read the expression, walk the False one (step 4).** The floor hazard is the operators in action. Each corridor has a crossing of four-tile-wide floor panels, one per row, and every panel shows an expression (`2 ** 3 == 8`, `5 > 3`, `True and False`). A panel is live when its expression is True and zaps whoever steps on it for 5 points (never security) with a shake, spark burst, the existing `zap` sound and an engineer line; walk the row whose expression is False. There is no timer and nothing changes while you stand there: the safe rows move with the level seed, each corridor always keeps at least one safe and one live row, every expression is checked against real Python in the tests, and a panel remembers what happened (teal border once stepped on safely, coral once it zapped). Panels are floor, not walls, so every route and pad stays reachable. (A first version used a ticking counter; it was confusing and was replaced.) Boots ring on a steel grating (`step_metal`, through a new per-floor `STEP_SOUND` on the room base) and a right answer plays the `switch` clunk before the gate hum. Full suite 1849 passed.
37. **Floor 2 props with a job: fuse box, safety poster, steam, a watchful engineer (step 5).** The wall of the tunnel now holds two things you can use with E from the corridor beside them (a breaker plate always wins, so answering is never blocked): a spare-fuse box (one fuse for +5 once, then empty) and a yellow safety poster that reads the operator rules in turn (brackets then `**` then `* / // %` then `+ -`; a True panel is live; `and` needs both, `or` needs one), blank when hints are off. Valves on the separator walls now hiss steam puffs that rise and fade, and the engineer turns to look at whoever was just zapped. Display, small bonus and text only; rules unchanged. 6 new tests; full suite 1855 passed.
38. **Floor 2 gamer review: a blocked safe row, and a sign for the panels.** Playing Floor 2 with a scripted player that walks the shortest route avoiding live panels found a real fairness bug: a breaker cabinet beside the first crossing walled off the top rows, so on about one seed in four the only safe row could be reached only by stepping on a live panel. The cabinet moved two columns left, and a new test now proves, for 40 seeds, that every corridor can be crossed from entry to gate without touching a live panel. A first-time player also had no way to learn what the panels meant, so a small "TRUE = LIVE" plate now sits on the wall under each crossing. Timing was checked too: reaching the right plate takes about 1.4 to 3.4 s of a 25 s clock.
39. **Floor 2 environment pass: pipes, rivets, toolbox and a working engineer.** The separator walls now carry pipe runs along the top and a flat conduit along the bottom (with brackets and cable ties, and nothing across the open shafts) and a pressure gauge each; every corridor tile has tread-plate rivets so the floor reads as steel decking; and a red toolbox sits beside the engineer's cabinet. The engineer's patrol is now a four-point loop along the open floor beneath the plates (never standing on an answer plate), and when nobody is talking to him he mutters a line every 16 s ("Pressure's up again.", "Who keeps flipping my breakers?"). Display and text only. Floor 1 got the same gamer check as Floor 2: a bot flood-filling the free tiles over 60 seeds found every parcel, chute and the exit door reachable. Full suite 1901 passed.

40. **Designer pass on Floors 1 and 2.** Floor 2's floor stencils (RELAY BAY n) were nearly invisible on the pipe row, so they are brighter on a dark plate; the two idle wall screens now read WAITING FOR RELAY n with a blinking cursor instead of a bare STANDBY (Floor 5 and the vault keep the shared screen). The tunnel lights ease up with every relay thrown, so power visibly returns. Floor 1's BELT OUT OF ORDER sign flips to BELT RESTARTED once every parcel is filed. Display only; no rules changed.

41. **Menu and lose-screen story pass.** The menu subtitle now carries the story (WARDEN is watching; steal the Master Memory) and a small NovaCorp security line with a blinking red dot sits at the top. The lose screen gives a tip for the floor where the run ended (e.g. Floor 2: panels marked False zap) and falls back to the general tip. Characters were reviewed against the story and kept: Ghost (disguised courier), Echo (partner) and WARDEN (the red eye). The How to Play controls table is left for the end, because Floors 3-5 and the vault are still being rebuilt.

42. **Pause: a way back to the menu.** The pause card only offered resume and settings, so a player stuck on a floor could not leave a run (ESC only resumes there). It now reads ESC resume | S settings | M menu, and M while paused returns to the main menu (Continue still offers the last saved floor). HUD, pause card and settings screen were reviewed with screenshots and left as they are.

43. **Floor 3 started: hazards cost score only.** Yash's branches were checked first: `yashovardhan-level3-presentation` is already merged and identical to `ui` for `levels/level3_loops.py`, and the Level 4 branch holds an older copy, so there is nothing to conflict with. Per the design brief, a laser hit (-10) and the patrol robot spotting you (-10, and the alert -15) now cost score only and never raise security, as on Floors 1 and 2. Wrong answers and a timed-out question still raise security as before. The laser tests now fail loudly if a hazard ever touches security. Next: a full rebuild of Floor 3 as NovaCorp's night patrol (three different rooms, patrol schedule board, night guard, lighting, cleaner header).

44. **Floor 3 as NovaCorp's night patrol: look, three rooms, live loop board (step 1).** Level 3's drawing moved into a new `levels/patrol_decor.py`; Yash's laser timing, robot, gates and questions are untouched. The plain purple frame is now a security wing in the floor's own teal-grey palette with a painted amber patrol route, a lit wall and a baked, different wall in each room: Room 1 the staff corridor (lockers, time clock with a blinking LED, extinguisher), Room 2 the camera gallery (a CCTV bank with scanning lines, a ceiling camera with a blinking REC dot), Room 3 the checkpoint hall (WARDEN's pulsing plaque and barrier posts). The crowded header is one slim line (floor, room name, question, difficulty, points, clock); the objective is a notice pinned to the wall; the old SECURITY CODE panel is now a PATROL LOOP board whose `if laser_detected:` line lights while a beam is live and whose `break` line lights once the gate is open, so the loop is shown running. The big LASER SECURITY SYSTEM heading, the robot's SPEED label and the long LASER n labels are gone (rails are marked L1-L3). Next: a night-guard NPC, lighting and a step sound.

45. **Floor 3: night guard, lighting, sounds and story (step 2).** A new NPC, the night guard (navy uniform, teal badge), walks a lap on the clear floor below the lowest rail in every room, greets the player when they come near, grumbles a line every 18 s and reacts when a laser or the robot catches you; his lines differ per room and he never blocks the player or touches score or security. The room is now lit: red glow from live beams, amber for a beam about to fire, a cool torch on the patrol robot (red during an alert), a lamp over the gate (red locked, teal open), and each room's own wall lamp (warm over the lockers, teal from the monitors, red from WARDEN's plaque). The wall text, board and question panel are drawn after the lighting so they stay crisp. New sounds: metal footsteps, a zap on a laser hit, the alarm when the robot catches you, a door sound when a gate unlocks. The story card and Echo's radio line now describe the night patrol (lasers sweep, a robot walks its route). Two laser tests now check the beam's own colours before lighting (`_draw_rails`) instead of the lit screen. Full suite 1912 passed.
46. **Floor 3 gameplay rebuilt: laser curtains.** The short beam bars were easy to walk around, so a laser is now a curtain across the whole room with one moving gap that sweeps back and forth (gap 170 px on Easy, 130 on Medium, 110 on Hard). Players now start below the curtains and the gates are above them, so crossing is required in every room (Room 1 has one curtain, Room 2 two, Room 3 three). The gap has bright green brackets so it is easy to find, and the warning phase is a dashed beam so it reads without colour. The robot's detection circle shrank from 180 px to 120 px so it is a threat near its lane instead of a near-constant tax. A laser hit flashes the room red. The gate label moved beside the door and the night guard walks the clear floor between the robot lane and the curtains. Everything stays score-only. A scripted gap-aware player averages about 0.5 to 1.7 hits per room.
47. **Floor 3 rebuild, step 1: Room 1 becomes the lane loop.** The user found the curtain design mediocre, so Floor 3 is being rebuilt so the code on the wall is the hazard. Room 1 now runs `for lane in range(4): zap(lane)` for real: four full-height electric lanes (new `levels/patrol_lanes.py`) fire one after another, neighbours overlap, then the loop rests and starts again. Each lane warns first (a dashed amber lane, readable without colour), then crackles with animated lightning and a red glow, between emitter caps. The wall board lights the line being run and shows `lane = n`. Lane speed and overlap scale with difficulty. The guard in Room 1 paces in the gap between two lanes. Hazards stay score-only. Rooms 2 and 3 still use the sweeping-gap curtains until their steps. 12 new tests in tests/test_patrol_lanes.py; four laser tests moved to Room 2.
48. **Floor 3 rebuild, step 2: Room 2 becomes the camera gallery.** The curtains are gone from Room 2. Three ceiling cameras (two on Easy) sweep glowing sight cones with scan rings; the wall board runs `while camera.on: sweep()` and `camera.on = False`. Standing in a cone for 0.6 s counts as being spotted (-10 score, then everything re-arms with a 2 s safe window); the cone turns red and the camera lens lights while it tracks you. Cones widen and swing faster with difficulty. Answering the room's question opens the gate and runs `camera.on = False`: the cones switch off and the board turns green. The new module is `levels/patrol_cameras.py`; hit handling in Level 3 is now one `_hazard_hit` for lasers, lanes and cameras. The story card and Echo's radio line were reworded to match the new floor. 10 new tests in tests/test_patrol_cameras.py; the four laser tests moved to Room 3, which still uses the sweeping-gap curtains until Step 3. The floating "GATE n: LOCKED" text on the floor was removed: the gate's own colour, lock icon and EXIT sign already show its state.
49. **Floor 3 rooms now have real walls.** The exit gate used to stand alone in an open floor, and the player could walk into the back wall and under the question panel. Each room now has solid back, left, right and front walls (real collision rectangles, drawn with panel seams and rivets). The exit door is set into the right wall with a dark service corridor and chevrons beyond it, and a shut steel door in the left wall marks where you came in. The rails, curtains and robot route were shortened to fit between the walls. Camera cones and lanes are clipped to the room. The earlier floating gate text stays removed.
50. **Floor 3 rebuild, step 3: Room 3 and the old curtains retired.** Room 3 is now the checkpoint hall's nested loop: the patrol robot walks above as the outer `while patrol():` and three wall-to-wall tripwire rows fire in turn as the inner `for lane in range(3):` (the wall board shows both loops, lights the line being run and shows `lane = n`). Rows are placed so every route to the door crosses one, and the gaps between rows are wide enough to stand in. Answering the question opens the door, which runs `break`: the board shows `break` and the robot stands down. With that the sweeping-gap curtains were no longer used anywhere, so the whole old laser system (rails, curtains, labels, glow, movement, timing constants) was removed from `levels/level3_loops.py`. `levels/patrol_lanes.py` now builds both layouts (columns for Room 1, rows for Room 3). The laser tests were rewritten for lanes and cameras; the hit rule is shared. A scripted player who reads the pattern averages 0.3 hits (Easy) to 0.5 (Hard) in Room 3.
51. **Floor 3: the patrol robot becomes an NPC, and Floors 1 and 2's rules are applied.** The vector-drawn robot looked out of place, so it is now `patrol_droid`, a pixel character built like the other NovaCorp staff (gunmetal dome, dark visor with red eyes that blink, amber lamps, a walking animation and shadow). The level still owns its route and detection; the NPC gives it a body and a voice (`NPC.drive`). It reacts like the other NPCs: it logs the courier as they pass ("Courier. Badge logged."), says "Unauthorised. Hold position." when it catches you, mutters an idle line now and then, and trades a greeting with the night guard when they pass ("Evening, Unit 7." / "Greeting logged."). When the door opens it says "Patrol ended. Standing down." and stops. Both the guard and the droid now have their own speech voices in `systems/voice.py`. The floor's name is "Night patrol" everywhere (HUD, story title, lose tip, Echo and WARDEN lines), replacing the old laser wording.

52. **Sliding badge doors on Floors 1, 2 and 3, and a proper droid scan zone.** Every exit is now one shared door, `levels/badge_door.py`. A locked door shows a padlock on its badge reader; when the answer is right the reader scans the courier's badge (a bright bar sweeps the card), turns green with a tick, and the two steel leaves slide apart into the wall pockets, with a soft light spilling out of the corridor. The level still owns the logic and hands the module one number (0 locked, then scan, then slide, 1 open): Floor 1 runs it on a 1.2 s tween, Floor 2's exit on a linear clock, and Floor 3's `PatrolGate` (a `Gate` that takes 1.2 s to unlock) on its own timer, so the door stays solid until the leaves have moved. The droid's spinning red line is replaced by its sensor field: a soft disc, a dashed rim and a ping that spreads from it, amber while it patrols and red and solid when it has spotted you. It is the same circle the detection uses, so a courier inside it is seen, and it is clipped to the room floor.

53. **Floors 1-3 review pass.** Rendered all three floors and checked them against the design brief. Two real problems on Floor 3 were fixed: (a) the droid "detected" the courier the instant a room loaded (the check ran before the player settled at the spawn), costing score and playing the alarm before any move, so it now has a 2.5 s grace period at the start of each room (`DROID_GRACE`); (b) the droid's speech bubble sat above its head, directly over the wall code board it patrols under, so the bubble is now drawn below the droid. The droid's sensor field was also toned down to a faint dotted ring that only lights red when it spots you. Two tests added.

54. **Floor 3: the rooms are dressed and the exit sign is part of the wall.** Floor 3 felt bare next to Floors 1 and 2, so each room now has its own floor and only the furniture it needs. Room 1 (staff corridor): the four lanes are rubber runners on the lino, numbered 0-3 like the loop's `lane`, plus floor drains and a staff vending machine. Room 2 (camera gallery): a raised floor with access hatches and a cable tray running from the monitor desk to a junction box under each ceiling camera, so the cameras visibly belong to the room. Room 3 (checkpoint hall): bare concrete, the checkpoint zone ruled off in yellow corner marks, and the rows labelled `row 0-2` like the nested loop. The floating EXIT chip with its dotted guide and bobbing arrow is replaced by a plate bolted to the wall above the door that shows the door's state as code (`open = False`, `badge.scan()`, `open = True`), so the lock is the same boolean the questions are about. The guard and droid greetings no longer stack: the droid answers 1.6 s after the guard.

55. **Floors 1-3 detail audit.** Searched Floors 1-3 for placeholder text (none) and rendered every floor in several states. Floor 3 still showed the old vocabulary in what the player reads, so it was renamed to match the story: banners and feedback say `LANE HIT`, `DOOR n: BADGE SCAN...`, `DOOR n OPEN! WALK THROUGH TO CONTINUE`, `PATROL DROID SAW YOU` and `!! PATROL DROID ALERT !!`; the footer reads `Doors opened: n/3` instead of `gates/challenges`; the completion line reads `Night patrol cleared`; the idle code sample uses `spotted`. The objective note is now a worn state form with a fold and a red `FORM 7-C` stamp instead of a plain sticky note. Frame cost was measured per floor (about 12-13 ms of render in the headless test, the same on all three), so the new effects add no weight. Left alone on purpose: on Floor 2 the Echo message box briefly covers the bottom label of relay bay 3 when the level opens (it clears by itself); the sign sits on the bottom wall row and there is no free floor above it to move it to.

56. **Depth and effects pass (researched first).** Beholder 3 pairs faceless 2D characters with grungy, half-3D environments, and pixel games fake depth cheaply with a rim light on characters, drop shadows, patterned spotlights and dust in the light (sources: GameGrin's Beholder 3 review, the xDasher devlog on light and depth, and a Pygame game-feel guide on particles, easing and micro-animations). Floors 1 and 2 already had steam, dust, a fan shadow and camera beams; Floor 3 had none of it. New `levels/depth_fx.py` holds stateless effects drawn from the clock alone: `light_bars` (slanted light through grilles, Rooms 1 and 3), `steam` (the Room 1 drain hisses), `sparks` (the Room 2 junction boxes spit sparks now and then) and `motes` (dust in every room). Every character on every floor now has a thin cool rim light (`core/character.py`) so it lifts off the dark floor. The badge door also vents a little steam from each wall pocket as the leaves slide and lights a halo round the reader. Seven tests added.

57. **Floor 4 rebuilt: the Records Archive.** Yash's Level 4 was a prototype of labelled boxes on a flat panel, answered with keys 1-4. Floor 4 is now a room on the shared kit (`levels/floor4_archive.py`, `levels/archive_decor.py`, `levels/archive_requests.py`): the hall where NovaCorp keeps a file on every citizen, Ghost's stolen memory in the vault at the end. A request slip on the wall asks for three things in turn, and you answer by doing them: pull Ghost's dossier from the shelf by index (`shelf[-2]`, `shelf[len(shelf) - 2]`), open the card-catalogue drawer a dictionary lookup lands on (`codes[name]`, `codes.get('ghost', 'none')`, or which key holds a value, with decoy drawers like `'Ghost'` and `'name'`), and feed the vault the satchel item a list method picks (`satchel.pop()`, `pop(0)`, `[-2]`, `remove` then `[0]`). Ghost's satchel is a real list shown on the wall; it starts with the courier badge from Floor 1. The archivist (a new NPC with her own voice) re-shelves, mutters, notices you, praises and scolds; a security drone sweeps the aisle (score only, with a grace period) and Echo's drone can scan the slip for a hint (Q, hints on) or lure the security drone away (X). Rules keep Floor 4's numbers: right +40, wrong security +15 and score -10, out of time security +25 and score -15 with a new slip, walk out +100. The exit is the shared badge door into the memory vault. Every slip's right answer is checked in the tests by running the slip's Python; a pathfinding bot reaches Floor 5 in solo and co-op, and a rushing player is logged by the drone about once on average. The old Level 4 returns with `MEMORY_HEIST_OLD_LEVEL4=1`.

58. **Floor 4 review pass.** Rendered the states not yet checked (wrong answer, scan, lure, the last seconds, co-op) and measured frame cost (about 12 ms of render, the same as Floors 1-3). Fixed: Echo's lure pulled the security drone up over the bookshelves, so it now pulls it along its own aisle and Echo's drone hovers beside it. Added: each new request slip drops out of the pneumatic tube instead of appearing; a right answer throws loose file pages; in the last five seconds the slip's edge pulses red and the clock ticks out loud once a second. Three tests added.

59. **Floor 5 rebuilt: WARDEN's Server Hall.** The previous Floor 5 used the same three-chambers-and-answer-pads pattern as the old Floor 2. It is now a machine room on the shared kit (`levels/floor5_server.py`, `levels/server_decor.py`, `levels/server_requests.py`) where every machine is a function with its def on the casing, and the job ticket on the wall asks for three jobs you do with your hands: patch the ROUTER's cable to the port whose value lands in the asked parameter (positional, keyword and default arguments), route the PRESS's conveyor to the bay its return value goes to (including None when it only prints, and an early return), and pull the except breaker that catches the REACTOR's error (ValueError, KeyError, ZeroDivisionError, IndexError, TypeError) before its heat bar fills and it trips. Then WARDEN's console runs Apporov's real try/except on the access level you type. The floor extends Level5ControlCenter, so Floor 5's numbers, hints (H, cost points, off on Hard) and terminal are unchanged; wrong choices are ruled out as before. A nervous sysadmin walks the top aisle, notices you and reacts; WARDEN's eye watches from a wall screen over a scrolling log; server racks blink; steam vents scald in the lower corridor (score only) and can be avoided by the upper aisle. Every ticket's answer is proved in the tests by running the real Python (the call, the return, the error raised); a pathfinding bot reaches the Final Vault in solo and co-op (score 270, security 0) and a rushing player is scalded about 0.5 times on average. The old hall's tests now register it explicitly; `MEMORY_HEIST_OLD_LEVEL5=1` still returns the original Level 5.

60. **Floor 5 review pass.** Rendered the states not yet checked (a wrong choice, a hint, a hot reactor, a vent scald, a bad console entry, co-op) and measured frame cost (about 13 ms of render, in line with Floors 1-4). Fixed: a ruled-out port, bay or breaker lost its value under the red strike, so the label now stays readable in dim red; the message line ran into the top of the job ticket and WARDEN's eye screen, so the wall screens sit a few pixels lower. Added: when the reactor passes 75% heat it sounds one alarm, the sysadmin shouts, and its casing flashes red until you pull the right breaker or it trips. Two tests added.

61. **The Final Vault rebuilt: WARDEN's Core.** The previous finale used the same three-chambers-and-pads pattern. It is now a round chamber (the only round floor in the game; `levels/final_core.py`, `levels/core_decor.py`, `levels/core_requests.py`) with the Master Memory chip sealed in an iris at its centre. Six lock pylons ring the core, one for every floor of the run (data types, operators, loops, lists and dictionaries, functions, exceptions), each with a few lines of Python on WARDEN's lock terminal and three answer plates in front of it; open them in any order. WARDEN's eye sits in the iris and sweeps a searchlight round the room that speeds up with every lock (score only, after a short grace); the eye cracks, his integrity bar drains and the room's light turns from red to teal as locks fall, and he taunts, then pleads. When all six are open the iris opens; take the chip at the core and run for the extraction lift (the shared badge door). Rules keep the old Final Vault's numbers: +50 per lock once, +150 for the chip, a wrong plate costs security +20 and score -10 and is ruled out. The optional typed terminal was dropped (Floor 5 already ends on a real try/except console). Every lock's right plate is proved in the tests by running its Python; a pathfinding bot reaches the win state in solo and co-op; a rushing player is caught by the searchlight about 2.5 times a run. The story's finale and ending lines now name the Master Memory chip. The previous hall's tests register it explicitly; `MEMORY_HEIST_OLD_FINAL_VAULT=1` still returns the original.

62. **Polish pass, step 1: the How to play table.** The title screen still described the old floors ("Levels 3, 4: E to collect", "1-4 keys" for Level 5 and the Final Vault). It now matches the game: WASD and E on every floor, 1-4 and H on Floor 3, Q scan and X lure on Floor 4, H hints on Floor 5 and the finale, co-op and pause rows unchanged. It stays at five rows, because a sixth would push the start prompt off a 640 px screen; a test pins that.

63. **Polish pass, step 2: the floor strip on the badges screen.** The badges screen showed wins, losses and badges but nothing about how far a player had got. The stats file now also keeps the deepest floor ever cleared (it never goes down, and an old stats file without it reads as 0); the level manager records it each time the game moves past a floor. The badges screen draws six floor chips under the badges (Lobby, Grid, Patrol, Archive, Servers, Core): cleared floors are lit teal, the next one is outlined in pulsing gold, the rest are dim. Eight tests added.

64. **Polish pass, step 3: main characters that stand out.** Ghost and Echo were drawn on the same 16x16 grid as every NPC, so on screen they were the same size as a receptionist, against the design brief's rule that the main characters need presence. They now have their own 16x22 art (drawn at 32x46, a head taller than any NPC) with more detail: Ghost's hood with a cyan visor slit, a scarf, a belted coat with a buckle, a satchel strap, gloves and split coat tails; Echo's ponytail, goggles pushed up on her forehead (her eyes now blink), a headset mic, teal-trimmed jacket and tool belt. The Floor 1 courier disguise was redrawn to fit. The collision box stays 32x32 and the sprite now stands on its feet, so movement, layouts and NPCs are unchanged; NPCs still use the 16x16 builder. Tests updated for the new size, the feet anchoring and a check that the heroes stand taller than every NPC.

65. **Polish pass, step 4: lobby muzak on Floor 1.** Floor 1's music was a generic mid-tempo track. It is now NovaCorp's lobby muzak, the bland "calming" tune the ceiling speakers play between WARDEN's announcements: slower (88 BPM), no kick, brushed hats, a soft electric-piano arpeggio and a hollow cheerful melody on two chords, filtered like a cheap ceiling speaker (no deep bass, no air) with a faint tape warble. The filter works in the frequency domain, which treats the loop as circular, so the seam stays clean (a test checks it). WARDEN's alert drone is never filtered, so it cuts through the muzak with full weight. Two synth-engine tests that had borrowed Floor 1 moved to Floor 2; four tests added.

66. **Polish pass, step 5: the 16:9 side strips.** The game draws at 960x640 (3:2), so a 16:9 screen showed black bars either side. The window is now 1136x640 (16:9): every screen and floor still draws into the central 960x640 slice (`display.game_area`), and `ui/sidebars.py` fills the strips with dark NovaCorp wall panels in the current floor's colour, the floor's name stencilled down the left wall and WARDEN's eye and a column of status lights on the right. The game itself is unchanged pixel for pixel; F11 re-takes the slice if the switch hands back a new surface. Six tests added.
67. **Fresh-review quick fixes.** A review with no memory of the build found small things a player would trip on. The Floor 2 lose tip said False panels zap; it now says panels that read True zap, which is the rule. Floor 3's "INCORRECT! Try again." was drawn green because the colour check looked for the word CORRECT inside it; it now checks the start of the message, so a wrong answer is red. A new run placed the crew at the default corner, over Floor 1's instruction line, because the players were positioned before Floor 1 was started; the reset now runs after, and the lobby has its own spawn points at the elevator door. Radio lines about a mistake are dropped once the crew makes progress, so Echo never scolds after a door has opened. Names agree everywhere: the HUD reads "Floor n of 6" and "Final floor", the story cards read "FLOOR n - ...", and the finale says one lock for every lesson. Readability: the engineer on Floor 2 speaks under himself so his bubble never covers the answer pads; Final floor plates grow to fit a long answer such as ZeroDivisionError (the stand-on area grows with them, and a check over 400 seeds shows no plates overlap); the Floor 5 job ticket uses larger code when it has few lines; posters keep their slogan inside the card. The audio start-up no longer prints debug lines to the console. Six tests added.
68. **Fairness: a lost floor is not a lost run.** Three changes so one bad floor does not end the game. (1) Security cools by 25 in the lift each time a floor is cleared (`SecurityMeter.cool`, `FLOOR_COOLDOWN`), so early mistakes do not carry a whole run into lockdown. (2) Each floor's question clock now has its own difficulty scale, `question_time_multiplier` (Easy x2.0, Medium x1.3, Hard x0.7), separate from the whole-run clock; Floors 2-5 use it, so on Medium Floor 3's room question gives 26 s instead of 20 and Floor 4's slip 58 s instead of 45. (3) When a floor after the first is lost, the lose screen offers "F: retry floor": it reloads that floor's save (the score and time the crew arrived with, security back to zero) and drops straight into the floor with no story card; R still starts a new run, and Floor 1 offers only R. Seven tests added.
69. **Presentation hygiene.** Sections 11-23 of this report described the planned levels (and a lives system that was never built); they now describe the finished floors, features, controls, look, stack and structure, with a note that sections 1-10 and 24-33 are the original proposal. Section 24 gains an "As built" table crediting each floor to the member who first built it and to who rebuilt it. The README was brought up to date the same way (floors, controls, credits, nothing left "being reworked"). The old levels the game no longer plays (the question-screen Level 1, the memory vault, the first server hall and both earlier Final Vaults, with their decor) moved to `levels/legacy/`; the escape hatches and their tests import them from there. Level 2 and Level 5's control centre stay in `levels/` because Floors 2 and 5 extend them. The menu's last controls row now names F (retry floor) and R (new run).
70. **Floor 3 questions are about the room's own loop.** The door questions came from a fixed bank of trivia ("Which statement stops a loop?") that had nothing to do with the room. Now `levels/patrol_requests.py` writes each room's loop and its question, per difficulty: Room 1 `for lane in range(...)` with start, stop and step (Medium counts down, Hard adds `if ...: continue` or `break`); Room 2 a `while` loop with a camera counter ("which cameras sweep?", "what is cam when it stops?"); Room 3 a `for` nested in `while patrol():` with `break`/`continue` on Hard. The code is run to find what fires, and the room follows it: `LaneLoop` takes the firing order (a lane the loop never reaches never fires) and `CameraBank` sweeps only the chosen cameras, now labelled `cam 0`-`cam 2`; the rest hang still. The PATROL LOOP board is wider (it takes the old notice's place), shows the multi-line indented code at up to 17 px, lights the loop header and the zap/sweep line, and shows the loop variable. Options are the answer plus off-by-one style distractors (include the stop value, miss the start, ignore the skip). `MEMORY_HEIST_OLD_LEVEL3=1` brings back the old question bank. 17 tests added: every answer is checked by running the code again, the lanes and cameras follow it, and the old bank returns with the switch.
71. **The heroes are back to human size.** Ghost and Echo had been redrawn 22 rows tall (46 px) for more detail, and in play they towered over every NPC like giants. They are now 16 rows plus the outline (34 px) against an NPC's 32: a protagonist's half-step taller, no more. The detail stays (Ghost's hood, visor slit, scarf, satchel strap, belt buckle and split coat tails; Echo's goggles, headset, teal trim and tool belt), packed into fewer rows, and the courier vest was redrawn to match. Collision boxes and feet anchoring are unchanged. The size test now checks the heroes are taller than any NPC by at most 4 px.
72. **Floor 2 relays ask real questions.** The relays drew from a fixed bank of 27 questions, many trivial ("What does `2 ** 3` evaluate to?" against 8, 6, 9, 5) and half of the True/False ones padded with "Error" and "None". `levels/grid_requests.py` now writes each relay's question per difficulty. Arithmetic: the wrong breakers are the same expression worked out wrongly (left to right instead of by precedence, `/` instead of `//`, `//` instead of `%`, `(2 ** 3) ** 2` instead of `2 ** 3 ** 2`, `-7 // 2` rounded towards zero), and when `/` gives `4.0` the plate `4` is offered beside it. Comparison and logic: "Which x makes ... True/False?", where Python checks every plate and exactly one answers it; the answer is picked at the edge (the boundary value) and the wrong plates are its neighbours. Divisors never divide evenly, so `//` and `%` always matter. The briefing now says what the floor does ("stand on the breaker that answers it"), and Echo's progress lines no longer say "Good sum." after a comparison. The old bank is still used by the original Level 2 (`MEMORY_HEIST_OLD_LEVEL2=1`). 20 tests added: every answer is re-evaluated, exactly one plate fits each "which x" question, runs vary, and the classic mistakes are offered.
73. **Floor 3: cross the room, then answer.** A review found the room could be skipped: keys 1-4 worked from the spawn point, so the lanes, cameras and tripwires were scenery. Now the door's badge reader takes the answer: away from the door the footer reads "Cross to the door to answer" and a key press only says so (no penalty); within reach of the door it reads "At the door: press 1-4". Reading the loop now decides how you cross. The room timer grew from 20 to 28 s at x1 (36 s on Medium) to allow for the walk. Lane and row numbers, which were faint stencils that a live beam covered, are now plates on every lane in the lane's own colour (white idle, amber warning, red live). The camera room's board steps through its counter (`cam = 0`, `cam = 2`, `cam = 4  stop`) instead of showing `on = True`, so the `while` loop can be followed line by line. "Doors opened" counts a door as soon as it takes the right answer, instead of lagging until you walk through. 2 tests added.
74. **Floor 3 becomes Yash's laser rooms, and each door asks about its own room again.** Yash's `level3-yashovardhan` branch (rotating beam room, sentry robot with an override terminal, core reactor, airlock corridors) replaced the night-patrol rebuild. His door questions came from the fixed bank, so they had nothing to do with the room. `levels/laser_requests.py` now writes each room a short loop for the LOOP LOGIC board, and the room obeys it: in Room 1 `for pad in range(...): light(pad)` decides which safe pads shield you (all pads look alike until a beam warms up, then lit pads glow SHIELD and the rest show OFF); in Room 2 the team's while-loop camera request picks the cameras that sweep; in Room 3 the core vents (goes offline for 6 s) after the number of `overload()` calls its loop makes, always 1 or 2, and a two-pulse board adds 5 s to the room clock. The answer is found by running the code, so board, room and answer cannot disagree. The board widens to fit up to four lines and the objective uses two lines beside it. `MEMORY_HEIST_OLD_LEVEL3=1` still brings back the fixed bank. 28 new tests; full suite 2264 passed.
75. **Floor 3's laser rooms get the NovaCorp look.** Yash's rooms were drawn as a violet neon grid, so Floor 3 looked like a different game. `levels/laser_decor.py` now bakes each room once, in the Night Patrol palette, with the same worn-concrete tiles, back and front walls, stains and washed-out grade as the other floors, plus dressing that follows the live positions: Room 1 is a test range (scorch streaks fan out from the rotor's bolted hub plate, "STAND ON A LIT PAD" painted on the floor), Room 2 has the sentry's patrol loop painted in amber dashes with arrows along its real waypoints, and Room 3 is a reactor deck (grating, coolant pipes, and red-and-black OVERLOAD LIMIT dashes where the ring stops). Bulkheads and door jambs use the team's steel wall face, and panel borders and answer buttons use the muted teal and navy of the UI kit. Drawing only: no position, timing or rule changed. 3 new tests; full suite 2267 passed.
76. **Floor 3 review fixes.** In Room 2 the "cam 1" tag sat on the vertical beam rail; `CameraBank` now takes `label_left`, and Floor 3 puts cam 1's tag on the left of its mount. The CAMERA GALLERY floor stencil moved left so the rail no longer cuts it. The robot's speed and route were set twice in `Level3LaserLoop.__init__`; the duplicate lines are gone (setup_room_hazards still sets each room's real route). 2 new tests; full suite 2269 passed.
77. **Floor 3 playtest: a longer breather after a hit, and the fixed question bank is the default again.** A playtest found Floor 3 too punishing: security carries over from Floor 2, and the 1 s window after a laser hit was short. The protection after a hit (laser, core ring or camera sighting, all one shared timer) is now 2 s. The door questions come from the fixed bank in `data/puzzles.json` again, so Floor 3 plays as Yash built it; `MEMORY_HEIST_GENERATED_LEVEL3=1` switches on the generated questions (`levels/laser_requests.py`), which also bring the room mechanics that follow them (lit pads in Room 1, the sweeping cameras in Room 2, the core vent in Room 3). The decor and the LOOP LOGIC board stay in both modes (the board shows the original code lines without the switch). `MEMORY_HEIST_OLD_LEVEL3=1` is still accepted and wins. 5 tests added or changed.
35. **Floor 2 lighting (step 3).** The tunnel now uses the same lighting pipeline as Floor 1 with a dimmer, warmer ambient. Light sources: the three relay screens (the active one brightest, an accepted one teal), three amber work bulbs along each corridor (the middle bulb of each flickers), a lamp on every gate that turns from coral to teal as it opens, a teal glow on the breaker cabinets, the engineer's bench lamp and the shaft lights. Blob shadows sit under the engineer, cabinets, bench and transformers, and the title is redrawn above the lighting so it stays readable. Rules unchanged; the quiet-wall test now checks the baked background.
34. **Floor 2 becomes a snaking utility tunnel (step 2: layout).** The three chambers in a row are replaced by three corridors that snake: corridor 1 runs east to power gate 1, a shaft drops to corridor 2 which runs west to gate 2, a shaft drops to corridor 3 which runs east to the exit shutter. Each corridor holds its own breaker plates and a RELAY BAY stencil; animated power pulses flow east, west, east along the corridors, arrows mark the shafts, valve wheels sit in the separator walls, breaker cabinets and the engineer's workbench line corridor 1 and two transformer blocks stand in corridor 3. The new geometry lives in `levels/snake_decor.py`; `levels/grid_decor.py` is untouched so Floor 5 and the Final Vault keep their straight hall. Rules, questions, scoring and security are unchanged; the geometry tests were rewritten for the snake (corridor reachability, gates hold in order, pads inside corridors, props off lanes and pads).
33. **Floor 2 becomes power routing (step 1: concept layer).** The maintenance grid is now a job: NovaCorp's power to the lower floors runs through three relay bays. Wall screens are relays ("RELAY 1  ARITHMETIC") showing an expression, the floor pads are breaker plates (two screws and a lever slot), the bays are stencilled "RELAY BAY n", and the gates are power gates. The wandering technician is now the gruff Engineer (his own sprite and voice, previously unused) with lines about operator order and what trips a relay. All messages, the level card and the radio line were rewritten to match. Questions, timers, scoring, security and pad logic are untouched. Next steps for Floor 2: the zig-zag tunnel layout, lighting, live floor panels and sounds.
32. **Ghost and Echo redrawn in a muted palette with more detail.** The two heroes were bright and flat next to the muted NPCs. Both palettes are now desaturated (Ghost slate-blue, Echo burnt orange) so they sit inside the NovaCorp mood, while the cyan visor and gold goggles stay bright as the focal point. Ghost gains a collar trim, broader cape shoulders and a belt line; Echo gains a ponytail and a diagonal teal satchel strap. Same 16x16 grid, size and animation, so collision, courier outfit and every test are unchanged.
31. **The sofa becomes the visitor waiting area.** Pressing E at the sofa reads a line from the waiting list ("Visitors waiting: 212. Estimated wait: unknown.", and two more), so every Floor 1 prop now has a job. Text only. 1 new test; full suite 1838 passed.
30. **Floor 1 props with a purpose: manifests, cooler talk and staff banter.** The two filing cabinets are now the intake manifests: pressing E at one reads the next chute rule (int, str, float, bool in turn) in that type's colour, and says the manifest is sealed when hints are off, so they teach without changing score or security. The water cooler gives a line of office gossip, and when the guard patrols past the reception desk he and the receptionist swap a line (22 s cooldown) so the lobby feels staffed. Display and text only, no rule changes. 3 new tests; full suite 1837 passed.
29. **Floor 1 playtest polish: a queue, a phone and visitor badges.** After playing Floor 1 start to finish, three things looked like decoration without a reason. (1) The hidden "chips" were floating teal discs; they are now lost visitor badges (a clipped white card with a teal stripe, a photo and text lines, swaying on a lanyard), which explains why a courier picks them up for points. (2) The dashed WAIT HERE line had nothing on it; it is now a visitor queue with four brass posts and two sagging red ropes that funnel people to a gap in front of the desk (the posts and ropes are solid, the gap and both sides stay open, and all parcels, chips and the exit are still reachable). (3) The receptionist only stood there; the desk now has a phone that rings every 31 seconds (first at 12 s) with a new `phone` sound (two quick electronic trills), shakes and shows ring arcs, and after about two seconds she answers in character ("NovaCorp reception.", "Yes. No. Please hold.", "He is not in. Nobody is.", "All calls are recorded."). 19 new tests; the prop-count test now counts the queue.

## 34.4 Testing

The suite has 61 test files and 889 passing tests (a few platform-dependent tests are skipped). The work followed one routine:

1. Write the test first, including the awkward cases (empty input, out-of-range values, a missing audio device).
2. Write the code until the tests pass.
3. Break the code on purpose, one line at a time, and confirm a test fails. A test that still passes when the code is broken proves nothing, and several tests were rewritten for exactly that reason.
4. Take a screenshot of anything visual (the game runs headless in tests, so the picture is saved and looked at) and fix overlaps that only show up on screen.

A GitHub Actions workflow (`.github/workflows/tests.yml`) runs the whole suite on every pull request, and a change is merged only when it is green. All work goes through one working branch and one pull request at a time.

## 34.5 Running and controls

| Action | How |
| --- | --- |
| Start the game | `python main.py` |
| Play the original Level 1 instead of Floor 1 | `set MEMORY_HEIST_OLD_LEVEL1=1`, then `python main.py` (Windows) |
| Play the original Level 5 screen instead of the server hall | `set MEMORY_HEIST_OLD_LEVEL5=1`, then `python main.py` (Windows) |
| Play the original Final Vault screen instead of the Master Vault | `set MEMORY_HEIST_OLD_FINAL_VAULT=1`, then `python main.py` (Windows) |
| Run all tests | `python -m pytest tests -q` |
| Pause | ESC while playing |
| Settings | S on the menu, or S on the pause screen |
| Fullscreen | F11 (the game starts full-screen and remembers the choice) |
| Use another settings file | set `MEMORY_HEIST_SETTINGS` to a file path |

## 34.6 Known limits and next steps

- Levels 1 to 5 and the Final Vault still use their original screen layouts. They share the HUD, transitions and sound, but only Floor 1 has the full new look.
- Known layout problems in teammates' levels (overlapping labels, text drawing into the HUD bar) and one Final Vault input bug are listed per owner in the team plan document.
- The music is deliberately simple; recorded tracks could replace it later through the same stem interface.
- There is no gamepad support, and the game assumes a 960 by 640 window (scaled when fullscreen).

---

# FINAL PROJECT SUMMARY

**Project Name:** Memory Heist

**Subtitle:** An Interactive Python Learning Game

**Type:** 2D Puzzle and Adventure Game

**Programming Language:** Python

**Framework:** Pygame

**Team Size:** 5 Members

**Project Level:** Intermediate

**Development Target:** Good College-Project Version

**Expected Development Time:** 2–3 Weeks

**Main Python Topics:**

1. Variables and Data Types
2. Operators and Conditional Logic
3. Loops
4. Lists and Dictionaries
5. Functions and Exception Handling
6. Combined Final Challenge

**Main Learning Principle:**

**Learn Python by playing and applying concepts rather than only memorizing or answering questions.**

**Core Gameplay:**

**Explore → Interact → Solve → Learn → Progress → Escape**