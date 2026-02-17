from maneuvers.general_defense import GeneralDefense
from maneuvers.recovery import Recovery
from maneuvers.pickup_boostpad import PickupBoostPad
from rlutilities.simulation import Car
from strategy import offense, kickoffs, defense
from strategy.boost_management import choose_boostpad_to_pickup
from strategy.teamplay_context import (
    adaptive_aggression,
    build_context,
    is_safe_to_detour_for_boost,
    should_take_over_attack,
    support_distance_for_role,
    support_face_target,
)
from tools.game_info import GameInfo
from tools.vector_math import align, ground, distance, ground_distance


def choose_maneuver(info: GameInfo, my_car: Car):
    ball = info.ball
    teammates = info.get_teammates(my_car)
    my_team = [my_car] + teammates
    their_goal = ground(info.their_goal.center)
    my_goal = ground(info.my_goal.center)

    # recovery
    if not my_car.on_ground:
        return Recovery(my_car)

    # kickoff
    if ball.position[0] == 0 and ball.position[1] == 0:

        # if I'm nearest (or tied) to the ball, go for kickoff
        if distance(my_car, ball) == min(distance(car, ball) for car in my_team):
            return kickoffs.choose_kickoff(info, my_car)

    skill = info.settings.skill
    mechanics = skill.mechanics * (0.7 + 0.3 * skill.overall)
    decision_quality = skill.decision_making * (0.7 + 0.3 * skill.overall)
    aggression = adaptive_aggression(info, my_car)
    awareness = skill.teammate_awareness

    context = build_context(info, my_team)
    my_intercept = context.intercepts_by_id[my_car.id]
    my_role = context.role_by_id.get(my_car.id, len(my_team) - 1)
    commit_window = (
        info.settings.teamplay.double_commit_window
        + (1.0 - decision_quality) * 0.20
        + (1.0 - awareness) * 0.16
    )

    low_boost_threshold = int(16 + (1.0 - skill.overall) * 16)
    if (
        my_car.boost < low_boost_threshold
        and my_role > 0
        and is_safe_to_detour_for_boost(info, context, my_car)
    ):
        best_boostpad = choose_boostpad_to_pickup(info, my_car)
        if best_boostpad is not None:
            return PickupBoostPad(my_car, best_boostpad)

    if context.danger > 0.86 and ground_distance(my_intercept, my_goal) < 4600:
        if my_role <= 1 or my_intercept.time <= context.attacker_intercept.time + 0.10:
            return defense.any_clear(info, my_car)

    should_attack = should_take_over_attack(info, context, my_car, commit_window)
    if should_attack:
        attack_alignment = align(my_intercept.car.position, my_intercept.ball, their_goal)
        if (
            attack_alignment > -0.25 + aggression * 0.40
            or ground_distance(my_intercept, my_goal) > 5800
            or context.time_advantage > 0.25
        ):
            return offense.any_shot(
                info,
                my_intercept.car,
                their_goal,
                my_intercept,
                allow_dribble=not info.is_puck and mechanics > 0.58,
            )
        return defense.any_clear(info, my_intercept.car)

    # Support / off-ball behavior.
    if (
        my_role >= 2
        and context.danger > 0.74
        and my_intercept.time < context.attacker_intercept.time + commit_window
    ):
        return defense.any_clear(info, my_car)

    if (
        my_role == 1
        and my_car.boost < 35
        and context.danger < 0.45
        and is_safe_to_detour_for_boost(info, context, my_car)
    ):
        best_boostpad = choose_boostpad_to_pickup(info, my_car)
        if best_boostpad is not None:
            return PickupBoostPad(my_car, best_boostpad)

    face_target = support_face_target(info, context, my_car)
    support_distance = support_distance_for_role(info, context, my_car, my_role)
    force_nearest = (
        my_role >= len(my_team) - 1
        and info.settings.teamplay.conservative_last_man
        and context.danger > 0.40
    )
    return GeneralDefense(my_car, info, face_target, support_distance, force_nearest=force_nearest)
