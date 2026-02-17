# Botimus

Botimus is a mechanics-heavy Rocket League bot with:

- Ball and hockey-puck object compatibility.
- Configurable skill/performance presets.
- Teamplay-specialized behavior for 2v2 and 3v3.
- Deterministic offline scenario harness for regression checks.

## Quick Start

1. Install dependencies for quality checks:

```bash
python -m pip install -r requirements-dev.txt
```

2. Run static checks:

```bash
ruff check .
mypy .
pytest
```

3. Run deterministic scenario harness:

```bash
python -m harness.runner --mode ball --report artifacts/ball_report.json
python -m harness.runner --mode puck --report artifacts/puck_report.json
```

4. Run local smoke script:

```bash
python local_checks/run_rlbot_smoke.py --mode ball
python local_checks/run_rlbot_smoke.py --mode puck
```

## Settings

Edit `botimus_settings.ini` to tune behavior:

- Object mode (`auto`, `ball`, `puck`)
- Skill preset and per-axis overrides
- Teamplay behavior and support/commit windows

Changes hot-reload while running.

