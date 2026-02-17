# AGENTS.md - Persistent Memory for Botimus

Last updated: 2026-02-17
Scope: `RLBotPack/Botimus` folder

## Purpose
This file is the persistent context for future sessions working on this bot.
Use it as the first-stop navigator before reading code.

Goals:
- Preserve project understanding across chat resets.
- Point directly to where behavior lives.
- Capture current constraints and highest-value next work.

## Session Bootstrap (Read First)
1. Confirm this folder is the Botimus package root.
2. Read `agent.py` first (this local install is Botimus Prime only).
3. Use the file map below to jump to the relevant strategy or maneuver.
4. Check "Known Constraints" before changing behavior.
5. If planning major work, start from "Prioritized Opportunities".

## What This Bot Is
- `Botimus Prime`: single-process agent for 1v1/standard play (`botimus.cfg` -> `agent.py`).
- Local status: Bumblebee/hivemind files were removed from this install on 2026-02-17.
- Core style: hardcoded tactical bot with physics prediction, maneuver selection, and modular mechanics.

## Runtime Entry Points
- `agent.py`
  - Class: `BotimusPrime(BaseAgent)`
  - Main loop:
    - Read packet into `GameInfo`.
    - Reset/cancel maneuvers on kickoff and opponent touches.
    - Choose maneuver via `strategy.solo_strategy` or `strategy.teamplay_strategy`.
    - Step maneuver, render debug, return controls.
- Config files:
  - `botimus.cfg` (single bot)

## High-Level Decision Model
- Recovery-first:
  - If airborne, prefer `Recovery`.
- Kickoff handling:
  - Ball at `(0,0)` triggers kickoff logic.
  - Single bot chooses kickoff by spawn position.
  - Teamplay strategy assigns roles by nearest-to-ball and defensive needs.
- Ball touch invalidation:
  - On new opponent touch, interruptible maneuvers are cleared.
- Intercept-driven planning:
  - Strategies call `info.predict_ball()`, create `Intercept`, and choose offense/defense/boost.

## Navigator Map (Where to Read for What)

### Strategy and assignment
- `strategy/solo_strategy.py`
  - 1v1 policy: recovery, kickoff, danger clears, shot windows, boost grabs, fallback defense.
- `strategy/teamplay_strategy.py`
  - Multi-teammate non-hivemind policy: nearest-player kickoff and role-by-intercept decisions.
- `strategy/teamplay_context.py`
  - Shared role/context model for 2v2 and 3v3 positioning and support logic.
- `strategy/offense.py`
  - Shot selection entry points (`direct_shot`, `any_shot`).
- `strategy/defense.py`
  - Clear selection (`any_clear`).
- `strategy/kickoffs.py`
  - Kickoff variant chooser.
- `strategy/boost_management.py`
  - Large pad selection with timing and position heuristics.

### Maneuver framework
- `maneuvers/maneuver.py`
  - Base contract: `step`, `interruptible`, `finished`, `controls`.
- Core movement:
  - `maneuvers/driving/drive.py` (steer/speed/throttle/boost control)
  - `maneuvers/driving/travel.py` (fast traversal + dodge/wavedash/half-flip triggers)
  - `maneuvers/driving/arrive.py` (time-constrained arrival with optional target direction)
- Core state maneuvers:
  - `maneuvers/recovery.py`
  - `maneuvers/general_defense.py`
  - `maneuvers/pickup_boostpad.py`
- Kickoff maneuvers:
  - `maneuvers/kickoffs/*`
- Strikes:
  - `maneuvers/strikes/strike.py` (base intercept update + arrive flow)
  - `dodge_strike.py`, `ground_strike.py`, `aerial_strike.py`, `double_jump_strike.py`
  - `double_touch.py`, `mirror_strike.py`, `close_shot.py`, `clears.py`
- Dribbling:
  - `maneuvers/dribbling/carry.py`
  - `maneuvers/dribbling/carry_and_flick.py`

### Simulation and utility layer
- `tools/game_info.py`
  - Shared game wrapper, goals, ball prediction, simple car trajectory and collision prediction.
- `tools/intercept.py`
  - Intercept search and drive-time estimate using LUT acceleration.
- `tools/vector_math.py`, `tools/math.py`
  - Math helpers used nearly everywhere.
- `tools/drawing.py`
  - Rendering helper with grouping and draw-item limits.
- `tools/arena.py`
  - Arena clamp and bounds checks.
- `tools/jump_sim.py`
  - Local jump sim utility (mostly analysis tooling).

### Data / physics LUT
- `data/acceleration_lut.py`
  - Drive acceleration lookup from CSV.
- `data/lookup_table.py`
  - CSV reader + bisect lookup.
- `data/acceleration/boost.csv`
- `data/acceleration/throttle.csv`

### External dependency wrapper
- `rlutilities/__init__.py`
  - Initializes RLUtilities binary module and assets.

## Key Tunables and Levers
Use these first when behavior changes are needed:

- Intercept and strike timing:
  - `maneuvers/strikes/strike.py`: `update_interval`, `stop_updating`, `max_additional_time`.
- Shot type decision:
  - `strategy/offense.py` thresholds for dribble eligibility and aerial preference.
- Defensive spacing:
  - `maneuvers/general_defense.py`: `DURATION`, shadow distances, side-shift values.
- Boost behavior:
  - `strategy/*_strategy.py` low-boost thresholds and pickup conditions.
  - `strategy/boost_management.py` candidate scoring model.
- Travel mechanics:
  - `maneuvers/driving/travel.py` dodge/wavedash/halfflip gating constants.
- Recovery aggressiveness:
  - `maneuvers/recovery.py` landing simulation window and boost logic.

## Known Constraints and Risks
- Environment:
  - This folder is not currently a git repo root (no local `.git` seen here).
- Ball prediction cost:
  - Many paths call `predict_ball`; expensive retuning can affect frame budget.
- Collision avoidance simplicity:
  - Team bump/demo avoidance is still heuristic and can produce false positives/late jumps.
- Strike viability:
  - Some strike classes are sensitive to narrow timing windows and orientation assumptions.
- Legacy TODOs in code:
  - Multiple `TODO` markers indicate areas intentionally incomplete (clears targeting, aerial options, duplication).

## Fast Debug Playbook

### "Why did it choose this maneuver?"
1. Start at `agent.py`.
2. Check reset conditions (kickoff/touch/demo).
3. Trace into strategy chooser (`solo_strategy.py` or `teamplay_strategy.py`).
4. Inspect resulting maneuver's `interruptible()` and `finished` behavior.

### "Why did it miss the ball?"
1. Inspect intercept source (`tools/intercept.py` + strike class `intercept_predicate`).
2. Confirm `predict_ball` horizon and update timing.
3. Check `Arrive` target-direction shift and speed target behavior.
4. Review dodge/jump trigger conditions in specific strike.

### "Why is team coordination weak?"
1. Inspect `strategy/teamplay_context.py` role assignment outputs.
2. Check `strategy/teamplay_strategy.py` takeover/commit gating and support positioning.
3. Review teammate spacing and bump avoidance checks in teamplay decisions.

## Rocket League Bot Context (Practical)
- This codebase is a hardcoded/mechanics-heavy bot architecture (not an end-to-end ML policy runtime).
- RLBot ecosystem is transitioning from v4-era config/runtime patterns toward v5 pre-release patterns.
- For long-term maintainability, design decisions should consider:
  - v5 config/process model (`bot.toml`, `run_command`, built-in hivemind flag).
  - clearer eval harnesses (repeatable scenarios and KPIs).
  - optional ML augmentation via RLGym/RocketSim for specific sub-problems, not necessarily full replacement.

## Prioritized Opportunities (for the bigger goal)

### 1) Improve decision quality around commitment and challenge timing
- Impact: High
- Effort: Medium
- Risk: Medium
- Primary files:
  - `strategy/solo_strategy.py`
  - `strategy/teamplay_strategy.py`
  - `tools/intercept.py`
  - `maneuvers/strikes/strike.py`
- First step:
  - Add explicit confidence scoring for candidate intercepts (time margin vs opponents, angle quality, recovery cost).

### 2) Strengthen 2v2/3v3 coordination and collision avoidance
- Impact: High (for teamplay reliability)
- Effort: Medium
- Risk: Medium
- Primary files:
  - `strategy/teamplay_strategy.py`
  - `strategy/teamplay_context.py`
  - `tools/game_info.py`
- First step:
  - Expand role-aware avoidance priorities and configurable safety envelopes.

### 3) Build a repeatable evaluation harness
- Impact: High (development speed, regression control)
- Effort: Medium
- Risk: Low
- Primary files:
  - New scripts + optional lightweight logging hooks in `agent.py`
- First step:
  - Define 5-10 canonical scenarios (kickoff, goal-line clear, wall read, boost starvation) and track success rates.

### 4) Prepare RLBot v5 migration track
- Impact: Medium/High (future compatibility)
- Effort: Medium
- Risk: Medium
- Primary files:
  - Config/runtime wrappers (`*.cfg` replacements, startup command plumbing)
- First step:
  - Create a migration checklist mapping current v4 assumptions to v5 equivalents.

### 5) Explore targeted ML augmentation (RLGym/RocketSim)
- Impact: Medium/High
- Effort: High
- Risk: Medium/High
- Primary files:
  - Likely new training pipeline + inference integration layer
- First step:
  - Pick one bounded mechanic (e.g., aerial takeoff timing or boost path scoring) for offline training experiment.

## Authoritative External Links (Compact)
- RLBot v5 overview:
  - https://wiki.rlbot.org/v5/
- RLBot v5 framework details and migration context:
  - https://wiki.rlbot.org/v5/framework/v5/
- RLBot v5 hiveminds:
  - https://wiki.rlbot.org/v5/botmaking/hiveminds/
- RLBot FAQ (community snapshot and bot tiers context):
  - https://rlbot.org/faq
- RLGym docs home:
  - https://rlgym.org/
- RLGym training guide:
  - https://rlgym.org/Rocket%20League/training_an_agent/

## Session Handoff Template (append for future sessions)
When major work is done, append a brief note:

- Date:
- Goal worked on:
- Files changed:
- Behavior changed:
- Validation performed:
- Open issues / next step:

### Session Note
- Date: 2026-02-17
- Goal worked on: Add configurable ball/puck support, editable performance tuning, and stronger 2v2/3v3 teamplay specialization.
- Files changed:
  - `botimus_settings.ini`
  - `tools/bot_settings.py`
  - `tools/game_info.py`
  - `agent.py`
  - `hivemind.py`
  - `strategy/teamplay_context.py`
  - `strategy/teamplay_strategy.py`
  - `strategy/hivemind_strategy.py`
  - `strategy/offense.py`
  - `strategy/defense.py`
  - `strategy/kickoffs.py`
  - `strategy/solo_strategy.py`
  - `maneuvers/strikes/dodge_strike.py`
  - `maneuvers/strikes/ground_strike.py`
  - `maneuvers/strikes/strike.py`
  - `maneuvers/kickoffs/simple_kickoff.py`
- Behavior changed:
  - Added hot-reload settings file controlling object mode (`auto/ball/puck`), skill preset/overrides, and teamplay spacing/commit behavior.
  - Added puck-aware object handling in `GameInfo` (mode detection, object heights/radius thresholds, optional RLBot external prediction use).
  - Added human teammate style tracking and team-level aggression adaptation hooks.
  - Reworked teamplay decision layer with dynamic role assignment (first/second/third man), safer takeover windows, conservative last-man logic, support follow behavior, and safer boost detours.
  - Reworked hivemind maneuver assignment to use role context + role-aware bump avoidance priorities.
  - Gated advanced mechanics (aerial/dribble/speedflip variants) by skill profile and puck mode.
- Validation performed:
  - `python -m compileall agent.py hivemind.py strategy tools maneuvers`
- Open issues / next step:
  - In-game validation is still needed for true puck physics behavior and tuning of default puck thresholds.

### Session Note
- Date: 2026-02-17
- Goal worked on: Build deterministic backtesting/scenario harness, add CI quality gates (Ruff/MyPy/Pytest), and prepare PR-ready automation.
- Files changed:
  - `pyproject.toml`
  - `requirements-dev.txt`
  - `.github/workflows/ci.yml`
  - `README.md`
  - `harness/__init__.py`
  - `harness/models.py`
  - `harness/policy.py`
  - `harness/report.py`
  - `harness/runner.py`
  - `harness/scenarios.py`
  - `tests/conftest.py`
  - `tests/test_bot_settings.py`
  - `tests/test_runner_modes.py`
  - `tests/test_scenario_harness.py`
  - `local_checks/run_rlbot_smoke.py`
  - `tools/adapters/__init__.py`
  - `tools/adapters/rlbot_protocols.py`
  - `typings/rlutilities/__init__.pyi`
  - `typings/rlutilities/linear_algebra.pyi`
  - `typings/rlutilities/mechanics.pyi`
  - `typings/rlutilities/simulation.pyi`
  - `tools/game_info.py`
- Behavior changed:
  - Added deterministic offline scenario backtesting with canonical 2v2/3v3 and puck scenarios, including KPI outputs.
  - Added repeatable JSON harness reporting for CI artifact upload.
  - Added strict typed boundary adapters for runtime prediction objects and local stub typing surface for static checks.
  - Added local smoke command that chains compile + harness checks.
  - Added CI workflow running compile, Ruff, MyPy, Pytest, and ball/puck harness runs.
- Validation performed:
  - `ruff check .`
  - `mypy`
  - `pytest`
  - `python -m compileall agent.py hivemind.py strategy tools maneuvers harness tests`
  - `python -m harness.runner --mode ball --report artifacts/ball_report.json`
  - `python -m harness.runner --mode puck --report artifacts/puck_report.json`
- Open issues / next step:
  - Add optional replay-log based backtesting layer if future regression depth is needed beyond deterministic scenarios.

### Session Note
- Date: 2026-02-17
- Goal worked on: Disable/remove Bumblebee so RLBot GUI only exposes Botimus Prime.
- Files changed:
  - Deleted: `bumblebee.cfg`
  - Deleted: `bumblebee-appearance.cfg`
  - Deleted: `bumblebee-logo.png`
  - Deleted: `drone_agent.py`
  - Deleted: `hivemind.py`
  - Deleted: `goal_explosion_randomizer.py`
  - Deleted: `strategy/hivemind_strategy.py`
  - Deleted: `tools/drone.py`
  - Updated: `local_checks/run_rlbot_smoke.py`
  - Updated: `.github/workflows/ci.yml`
  - Updated: `AGENTS.md`
- Behavior changed:
  - This local package is now Botimus Prime only; Bumblebee/hivemind runtime path is removed.
  - RLBot GUI should no longer list Bumblebee from this folder.
- Validation performed:
  - `python -m compileall agent.py strategy tools maneuvers harness tests`
  - `ruff check .`
  - `mypy`
  - `pytest`
  - `python -m harness.runner --mode ball --report artifacts/ball_report.json`
  - `python -m harness.runner --mode puck --report artifacts/puck_report.json`
  - `rg -n "hivemind|drone_agent|bumblebee|goal_explosion_randomizer|hive_key|Beehive|hivemind_strategy|tools\.drone" -S --glob "!AGENTS.md" .` (no matches)
- Open issues / next step:
  - Restart/refresh RLBot GUI if Bumblebee is still cached in the UI.
