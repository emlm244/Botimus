from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True)
class SkillProfile:
    preset: str
    overall: float
    mechanics: float
    decision_making: float
    aggression: float
    rotation_discipline: float
    teammate_awareness: float
    consistency: float


@dataclass(frozen=True)
class ObjectModeSettings:
    mode: str
    use_rlbot_prediction_for_ball: bool
    use_rlbot_prediction_for_puck: bool
    ball_rest_height: float
    puck_rest_height: float
    ball_ground_cutoff: float
    puck_ground_cutoff: float
    ball_render_radius: float
    puck_render_radius: float


@dataclass(frozen=True)
class TeamplaySettings:
    follow_human_style: bool
    human_follow_strength: float
    support_distance_2v2: float
    support_distance_3v3_second: float
    support_distance_3v3_third: float
    double_commit_window: float
    conservative_last_man: bool
    boost_detour_risk: float


@dataclass(frozen=True)
class BotSettings:
    reload_interval: float
    skill: SkillProfile
    object_mode: ObjectModeSettings
    teamplay: TeamplaySettings


_SKILL_PRESETS: Dict[str, SkillProfile] = {
    "bronze": SkillProfile("bronze", 0.20, 0.18, 0.22, 0.40, 0.55, 0.45, 0.30),
    "silver": SkillProfile("silver", 0.32, 0.30, 0.35, 0.45, 0.58, 0.52, 0.38),
    "gold": SkillProfile("gold", 0.45, 0.45, 0.48, 0.52, 0.62, 0.60, 0.48),
    "platinum": SkillProfile("platinum", 0.58, 0.58, 0.60, 0.58, 0.68, 0.68, 0.58),
    "diamond": SkillProfile("diamond", 0.70, 0.72, 0.72, 0.62, 0.74, 0.76, 0.70),
    "champion": SkillProfile("champion", 0.82, 0.84, 0.84, 0.67, 0.80, 0.84, 0.82),
    "grand_champion": SkillProfile("grand_champion", 0.92, 0.94, 0.94, 0.70, 0.86, 0.90, 0.92),
}

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "botimus_settings.ini"


def _get_float(parser: configparser.ConfigParser, section: str, option: str, fallback: float) -> float:
    try:
        return parser.getfloat(section, option, fallback=fallback)
    except (ValueError, configparser.Error):
        return fallback


def _get_bool(parser: configparser.ConfigParser, section: str, option: str, fallback: bool) -> bool:
    try:
        return parser.getboolean(section, option, fallback=fallback)
    except (ValueError, configparser.Error):
        return fallback


def _get_str(parser: configparser.ConfigParser, section: str, option: str, fallback: str) -> str:
    try:
        return parser.get(section, option, fallback=fallback)
    except (ValueError, configparser.Error):
        return fallback


def _resolve_skill(parser: configparser.ConfigParser) -> SkillProfile:
    preset = _get_str(parser, "Skill", "preset", "champion").strip().lower()
    if preset not in _SKILL_PRESETS:
        preset = "champion"

    base = _SKILL_PRESETS[preset]

    def override(option: str, default: float) -> float:
        raw = _get_str(parser, "Skill", option, "auto").strip().lower()
        if raw == "auto":
            return default
        try:
            return _clamp01(float(raw))
        except ValueError:
            return default

    return SkillProfile(
        preset=preset,
        overall=override("overall", base.overall),
        mechanics=override("mechanics", base.mechanics),
        decision_making=override("decision_making", base.decision_making),
        aggression=override("aggression", base.aggression),
        rotation_discipline=override("rotation_discipline", base.rotation_discipline),
        teammate_awareness=override("teammate_awareness", base.teammate_awareness),
        consistency=override("consistency", base.consistency),
    )


def default_settings() -> BotSettings:
    return BotSettings(
        reload_interval=1.0,
        skill=_SKILL_PRESETS["champion"],
        object_mode=ObjectModeSettings(
            mode="auto",
            use_rlbot_prediction_for_ball=False,
            use_rlbot_prediction_for_puck=True,
            ball_rest_height=93.0,
            puck_rest_height=60.0,
            ball_ground_cutoff=220.0,
            puck_ground_cutoff=140.0,
            ball_render_radius=92.75,
            puck_render_radius=105.0,
        ),
        teamplay=TeamplaySettings(
            follow_human_style=True,
            human_follow_strength=0.7,
            support_distance_2v2=4300.0,
            support_distance_3v3_second=3900.0,
            support_distance_3v3_third=6700.0,
            double_commit_window=0.22,
            conservative_last_man=True,
            boost_detour_risk=0.35,
        ),
    )


def load_bot_settings(path: Path | str = DEFAULT_SETTINGS_PATH) -> BotSettings:
    parser = configparser.ConfigParser()
    parser.read(path)

    defaults = default_settings()
    skill = _resolve_skill(parser)

    mode = _get_str(parser, "Object", "mode", defaults.object_mode.mode).strip().lower()
    if mode not in {"auto", "ball", "puck"}:
        mode = defaults.object_mode.mode

    object_mode = ObjectModeSettings(
        mode=mode,
        use_rlbot_prediction_for_ball=_get_bool(
            parser,
            "Object",
            "use_rlbot_prediction_for_ball",
            defaults.object_mode.use_rlbot_prediction_for_ball,
        ),
        use_rlbot_prediction_for_puck=_get_bool(
            parser,
            "Object",
            "use_rlbot_prediction_for_puck",
            defaults.object_mode.use_rlbot_prediction_for_puck,
        ),
        ball_rest_height=_get_float(parser, "Object", "ball_rest_height", defaults.object_mode.ball_rest_height),
        puck_rest_height=_get_float(parser, "Object", "puck_rest_height", defaults.object_mode.puck_rest_height),
        ball_ground_cutoff=_get_float(
            parser, "Object", "ball_ground_cutoff", defaults.object_mode.ball_ground_cutoff
        ),
        puck_ground_cutoff=_get_float(
            parser, "Object", "puck_ground_cutoff", defaults.object_mode.puck_ground_cutoff
        ),
        ball_render_radius=_get_float(
            parser, "Object", "ball_render_radius", defaults.object_mode.ball_render_radius
        ),
        puck_render_radius=_get_float(
            parser, "Object", "puck_render_radius", defaults.object_mode.puck_render_radius
        ),
    )

    teamplay = TeamplaySettings(
        follow_human_style=_get_bool(
            parser, "Teamplay", "follow_human_style", defaults.teamplay.follow_human_style
        ),
        human_follow_strength=_clamp01(
            _get_float(parser, "Teamplay", "human_follow_strength", defaults.teamplay.human_follow_strength)
        ),
        support_distance_2v2=_get_float(
            parser, "Teamplay", "support_distance_2v2", defaults.teamplay.support_distance_2v2
        ),
        support_distance_3v3_second=_get_float(
            parser, "Teamplay", "support_distance_3v3_second", defaults.teamplay.support_distance_3v3_second
        ),
        support_distance_3v3_third=_get_float(
            parser, "Teamplay", "support_distance_3v3_third", defaults.teamplay.support_distance_3v3_third
        ),
        double_commit_window=_clamp01(
            _get_float(parser, "Teamplay", "double_commit_window", defaults.teamplay.double_commit_window)
        ),
        conservative_last_man=_get_bool(
            parser, "Teamplay", "conservative_last_man", defaults.teamplay.conservative_last_man
        ),
        boost_detour_risk=_clamp01(_get_float(parser, "Teamplay", "boost_detour_risk", defaults.teamplay.boost_detour_risk)),
    )

    reload_interval = _get_float(parser, "General", "reload_interval", defaults.reload_interval)
    reload_interval = max(0.2, reload_interval)

    return BotSettings(
        reload_interval=reload_interval,
        skill=skill,
        object_mode=object_mode,
        teamplay=teamplay,
    )


DEFAULT_SETTINGS_FILE_CONTENT = """; Botimus Settings
; Edit values and save while the bot is running. Settings hot-reload automatically.
; 0.0 = very low, 1.0 = very high.
;
; Skill presets:
; bronze, silver, gold, platinum, diamond, champion, grand_champion

[General]
reload_interval = 1.0

[Object]
; mode: auto | ball | puck
mode = auto

; For puck this should usually stay true.
use_rlbot_prediction_for_puck = true
; Optional. Usually false unless you want game prediction for normal ball too.
use_rlbot_prediction_for_ball = false

; Object shape tuning for decisions/rendering.
ball_rest_height = 93
puck_rest_height = 60
ball_ground_cutoff = 220
puck_ground_cutoff = 140
ball_render_radius = 92.75
puck_render_radius = 105

[Skill]
; Main rank-like preset controlling overall bot performance.
preset = champion

; Set each to auto or a number from 0.0 to 1.0.
overall = auto
mechanics = auto
decision_making = auto
aggression = auto
rotation_discipline = auto
teammate_awareness = auto
consistency = auto

[Teamplay]
follow_human_style = true
human_follow_strength = 0.7

; Backline spacing (uu) for off-ball behavior.
support_distance_2v2 = 4300
support_distance_3v3_second = 3900
support_distance_3v3_third = 6700

; Lower means fewer double commits.
double_commit_window = 0.22
conservative_last_man = true

; Lower means safer boost choices, higher means greedier boost choices.
boost_detour_risk = 0.35
"""


def ensure_settings_file(path: Path | str = DEFAULT_SETTINGS_PATH) -> None:
    path = Path(path)
    if path.exists():
        return
    path.write_text(DEFAULT_SETTINGS_FILE_CONTENT, encoding="utf-8")


class BotSettingsManager:
    def __init__(self, path: Path | str = DEFAULT_SETTINGS_PATH):
        self.path = Path(path)
        ensure_settings_file(self.path)
        self.settings = load_bot_settings(self.path)
        self._last_mtime = self._read_mtime()
        self._next_check_time = 0.0

    def _read_mtime(self) -> float:
        try:
            return self.path.stat().st_mtime
        except OSError:
            return -1.0

    def maybe_reload(self, game_time: float) -> BotSettings:
        if game_time < self._next_check_time:
            return self.settings

        self._next_check_time = game_time + self.settings.reload_interval
        mtime = self._read_mtime()
        if mtime != self._last_mtime:
            self._last_mtime = mtime
            self.settings = load_bot_settings(self.path)
        return self.settings
