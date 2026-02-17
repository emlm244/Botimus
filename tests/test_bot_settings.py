from __future__ import annotations

import os
from pathlib import Path

from tools.bot_settings import BotSettingsManager, default_settings, load_bot_settings


def test_load_bot_settings_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.ini"
    config_path.write_text(
        """
[General]
reload_interval = 0.5

[Object]
mode = puck
use_rlbot_prediction_for_puck = true

[Skill]
preset = diamond
aggression = 0.75

[Teamplay]
double_commit_window = 0.15
        """.strip(),
        encoding="utf-8",
    )

    settings = load_bot_settings(config_path)
    assert settings.object_mode.mode == "puck"
    assert settings.object_mode.use_rlbot_prediction_for_puck is True
    assert settings.skill.preset == "diamond"
    assert abs(settings.skill.aggression - 0.75) < 1e-9
    assert abs(settings.teamplay.double_commit_window - 0.15) < 1e-9
    assert abs(settings.reload_interval - 0.5) < 1e-9


def test_settings_manager_hot_reload(tmp_path: Path) -> None:
    settings_path = tmp_path / "botimus_settings.ini"
    settings_path.write_text(
        """
[General]
reload_interval = 0.2

[Object]
mode = ball

[Skill]
preset = champion
        """.strip(),
        encoding="utf-8",
    )

    manager = BotSettingsManager(settings_path)
    assert manager.settings.object_mode.mode == "ball"

    settings_path.write_text(
        """
[General]
reload_interval = 0.2

[Object]
mode = puck

[Skill]
preset = platinum
        """.strip(),
        encoding="utf-8",
    )
    mtime = settings_path.stat().st_mtime + 1.0
    os.utime(settings_path, (mtime, mtime))

    manager.maybe_reload(0.25)
    assert manager.settings.object_mode.mode == "puck"
    assert manager.settings.skill.preset == "platinum"


def test_default_settings_shape() -> None:
    settings = default_settings()
    assert settings.object_mode.mode == "auto"
    assert 0 <= settings.skill.overall <= 1
    assert 0 <= settings.skill.mechanics <= 1
