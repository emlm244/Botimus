from __future__ import annotations

from harness.runner import run


def test_runner_ball_mode_passes() -> None:
    assert run(mode="ball") == 0


def test_runner_puck_mode_passes() -> None:
    assert run(mode="puck") == 0

