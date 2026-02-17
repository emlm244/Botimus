from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from harness.models import CarState, EvaluationResult, MatchState, RecommendedAction, Scenario, Vec3
from tools.bot_settings import BotSettings, default_settings


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _direction_2d(source: Vec3, target: Vec3) -> Vec3:
    delta = target - source
    norm = max(delta.norm_xy(), 1e-6)
    return Vec3(delta.x / norm, delta.y / norm, 0.0)


def _dot2(a: Vec3, b: Vec3) -> float:
    return a.x * b.x + a.y * b.y


def estimate_intercept_time(car: CarState, ball_pos: Vec3) -> float:
    distance_to_ball = max(0.0, car.position.distance_xy(ball_pos) - 120.0)
    base_speed = max(420.0, car.speed_xy())
    speed_bonus = car.boost * 7.5
    effective_speed = min(2300.0, base_speed + speed_bonus)
    return distance_to_ball / max(effective_speed, 1.0)


@dataclass(frozen=True)
class TeamContext:
    intercept_times: Dict[int, float]
    ordered_roles: list[int]
    attacker_id: int
    danger: float
    opponent_fastest_intercept: float


def build_team_context(state: MatchState) -> TeamContext:
    teammates = state.teammates()
    if not teammates:
        raise ValueError("MatchState must include at least one non-demolished teammate")

    intercept_times = {car.car_id: estimate_intercept_time(car, state.ball.position) for car in teammates}
    attacker = min(teammates, key=lambda car: intercept_times[car.car_id])
    ordered_ids = [attacker.car_id]

    remaining = [car for car in teammates if car.car_id != attacker.car_id]
    if len(remaining) == 1:
        ordered_ids.append(remaining[0].car_id)
    elif len(remaining) >= 2:
        third_man = min(remaining, key=lambda car: car.position.distance_xy(state.my_goal))
        second_candidates = [car for car in remaining if car.car_id != third_man.car_id]
        second_candidates.sort(key=lambda car: intercept_times[car.car_id])
        ordered_ids.extend([car.car_id for car in second_candidates])
        ordered_ids.append(third_man.car_id)

    opponents = state.opponents()
    if opponents:
        opponent_fastest = min(estimate_intercept_time(car, state.ball.position) for car in opponents)
    else:
        opponent_fastest = 9.99

    goal_pressure = clamp01((4200.0 - state.ball.position.distance_xy(state.my_goal)) / 4200.0)
    to_goal = _direction_2d(state.ball.position, state.my_goal)
    velocity_pressure = clamp01((_dot2(state.ball.velocity, to_goal) + 200.0) / 1800.0)
    attacker_pressure = clamp01((intercept_times[attacker.car_id] - opponent_fastest + 0.25) / 1.2)
    danger = clamp01(goal_pressure * 0.45 + velocity_pressure * 0.25 + attacker_pressure * 0.30)

    return TeamContext(
        intercept_times=intercept_times,
        ordered_roles=ordered_ids,
        attacker_id=attacker.car_id,
        danger=danger,
        opponent_fastest_intercept=opponent_fastest,
    )


def choose_action_for_bot(state: MatchState, bot_car_id: int, settings: BotSettings) -> tuple[RecommendedAction, int, int, float, bool]:
    context = build_team_context(state)
    if bot_car_id not in context.ordered_roles:
        raise ValueError(f"bot car {bot_car_id} is missing from active teammate list")

    role = context.ordered_roles.index(bot_car_id)
    last_role = len(context.ordered_roles) - 1
    my_intercept = context.intercept_times[bot_car_id]
    attacker_intercept = context.intercept_times[context.attacker_id]

    decision_quality = settings.skill.decision_making * (0.7 + 0.3 * settings.skill.overall)
    awareness = settings.skill.teammate_awareness
    commit_window = (
        settings.teamplay.double_commit_window
        + (1.0 - decision_quality) * 0.20
        + (1.0 - awareness) * 0.16
    )

    time_buffer = context.opponent_fastest_intercept - my_intercept
    risk = settings.teamplay.boost_detour_risk * settings.skill.decision_making
    boost_safe = time_buffer > (0.25 + (1.0 - risk) * 0.60 + context.danger * 0.40)

    double_commit_risk = 0.0
    if role > 0:
        delta = my_intercept - attacker_intercept
        double_commit_risk = clamp01(1.0 - (delta + commit_window) / max(commit_window + 0.30, 0.01))

    if role == 0:
        ball_to_goal = state.ball.position.distance_xy(state.my_goal)
        emergency_defend = (
            context.danger > 0.50
            and ball_to_goal < 2600.0
            and my_intercept >= context.opponent_fastest_intercept + 0.10
        )
        action: RecommendedAction = "defend" if emergency_defend else "attack"
    else:
        if role == last_role and settings.teamplay.conservative_last_man and context.danger > 0.40:
            action = "defend"
        elif role >= 2 and context.danger > 0.74 and my_intercept < attacker_intercept + commit_window:
            action = "defend"
        else:
            action = "support"

        bot_car = next(car for car in state.teammates() if car.car_id == bot_car_id)
        low_boost_threshold = int(16 + (1.0 - settings.skill.overall) * 16)
        risky_margin = max(-0.05, (1.0 - settings.teamplay.boost_detour_risk) * -0.12)
        if (
            bot_car.boost < low_boost_threshold
            and context.danger < 0.82
            and (
                boost_safe
                or time_buffer > risky_margin
                or my_intercept >= attacker_intercept + 2.0
            )
        ):
            action = "boost"

    last_man_violation = role == last_role and action == "attack"
    return action, role, context.attacker_id, double_commit_risk, last_man_violation


def evaluate_scenario(scenario: Scenario, settings: BotSettings | None = None) -> EvaluationResult:
    active_settings = settings or default_settings()
    action, role, attacker_id, double_commit_risk, last_man_violation = choose_action_for_bot(
        scenario.state,
        scenario.bot_car_id,
        active_settings,
    )

    expected = scenario.expectation
    passed = True
    reasons: list[str] = []

    if action != expected.action:
        passed = False
        reasons.append(f"expected action '{expected.action}', got '{action}'")
    if expected.role is not None and role != expected.role:
        passed = False
        reasons.append(f"expected role {expected.role}, got {role}")
    if double_commit_risk > expected.max_double_commit_risk:
        passed = False
        reasons.append(
            f"double_commit_risk {double_commit_risk:.3f} exceeded max {expected.max_double_commit_risk:.3f}"
        )
    if last_man_violation and not expected.allow_last_man_attack:
        passed = False
        reasons.append("last-man violation: attack selected while being final backline role")

    message = "; ".join(reasons) if reasons else "ok"
    return EvaluationResult(
        scenario_id=scenario.scenario_id,
        passed=passed,
        action=action,
        role=role,
        attacker_id=attacker_id,
        double_commit_risk=double_commit_risk,
        last_man_violation=last_man_violation,
        message=message,
    )
