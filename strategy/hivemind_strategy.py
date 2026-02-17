from typing import List, Optional, Dict

from maneuvers.general_defense import GeneralDefense
from maneuvers.kickoffs.drive_backwards_to_goal import DriveBackwardsToGoal
from maneuvers.kickoffs.half_flip_pickup import HalfFlipPickup
from maneuvers.recovery import Recovery
from maneuvers.pickup_boostpad import PickupBoostPad
from rlutilities.linear_algebra import norm
from rlutilities.simulation import BoostPad
from strategy import offense, defense, kickoffs
from strategy.boost_management import choose_boostpad_to_pickup
from strategy.teamplay_context import (
    build_context,
    is_safe_to_detour_for_boost,
    support_distance_for_role,
    support_face_target,
)
from tools.drawing import DrawingTool
from tools.drone import Drone
from tools.game_info import GameInfo
from tools.vector_math import align, ground, ground_distance, distance


class HivemindStrategy:
    def __init__(self, info: GameInfo, logger):
        self.info: GameInfo = info
        self.logger = logger

        # the drone that is currently committed to hitting the ball
        self.drone_going_for_ball: Optional[Drone] = None
        self.defending_drone: Optional[Drone] = None

        self.boost_reservations: Dict[Drone, BoostPad] = dict()
        self.roles_by_index: Dict[int, int] = dict()

    def set_kickoff_maneuvers(self, drones: List[Drone]):
        skill = self.info.settings.skill
        mechanics = skill.mechanics * (0.7 + 0.3 * skill.overall)
        nearest_drone = min(drones, key=lambda drone: ground_distance(drone.car, self.info.ball))
        nearest_drone.maneuver = kickoffs.choose_kickoff(self.info, nearest_drone.car)
        self.drone_going_for_ball = nearest_drone

        self.roles_by_index = {nearest_drone.index: 0}
        self.boost_reservations.clear()
        corner_drones = [drone for drone in drones if abs(drone.car.position[0]) > 2000]
        if len(corner_drones) > 1:
            other_corner_drone = next(drone for drone in corner_drones if drone is not nearest_drone)
            nearest_pad = min(self.info.large_boost_pads, key=lambda pad: distance(other_corner_drone.car, pad))
            if mechanics > 0.6:
                other_corner_drone.maneuver = HalfFlipPickup(other_corner_drone.car, nearest_pad)
            else:
                other_corner_drone.maneuver = PickupBoostPad(other_corner_drone.car, nearest_pad)
            self.boost_reservations[other_corner_drone] = nearest_pad
            self.roles_by_index[other_corner_drone.index] = 1

        self.defending_drone = max(drones, key=lambda drone: ground_distance(drone.car, self.info.ball))
        self.defending_drone.maneuver = DriveBackwardsToGoal(self.defending_drone.car, self.info)
        self.roles_by_index[self.defending_drone.index] = len(drones) - 1

        for drone in drones:
            if drone not in corner_drones + [self.defending_drone] + [self.drone_going_for_ball]:
                self.send_drone_for_boost(drone)
                self.roles_by_index[drone.index] = max(1, len(drones) - 2)

    def send_drone_for_boost(self, drone: Drone):
        reserved_pads = set(self.boost_reservations.values())
        best_boostpad = choose_boostpad_to_pickup(self.info, drone.car, forbidden_pads=reserved_pads)
        if best_boostpad is None:
            return
        drone.maneuver = PickupBoostPad(drone.car, best_boostpad)
        self.boost_reservations[drone] = best_boostpad  # reserve chosen boost pad

    def set_maneuvers(self, drones: List[Drone]):
        info = self.info
        their_goal = ground(info.their_goal.center)
        our_goal = ground(info.my_goal.center)
        skill = info.settings.skill
        mechanics = skill.mechanics * (0.7 + 0.3 * skill.overall)
        decision_quality = skill.decision_making * (0.7 + 0.3 * skill.overall)
        awareness = skill.teammate_awareness
        commit_window = (
            info.settings.teamplay.double_commit_window
            + (1.0 - decision_quality) * 0.20
            + (1.0 - awareness) * 0.16
        )
        low_boost_threshold = int(18 + (1.0 - skill.overall) * 16)

        if self.drone_going_for_ball is not None and self.drone_going_for_ball.maneuver is None:
            self.drone_going_for_ball = None

        if self.defending_drone is not None and self.defending_drone.maneuver is None:
            self.defending_drone = None

        for drone in drones:
            if drone.maneuver is None and not drone.car.on_ground:
                drone.maneuver = Recovery(drone.car)

        active_cars = [drone.car for drone in drones if not drone.car.demolished]
        if not active_cars:
            return

        context = build_context(info, active_cars)
        drone_by_car_id = {drone.car.id: drone for drone in drones}
        self.roles_by_index.clear()
        for drone in drones:
            role = context.role_by_id.get(drone.car.id, len(active_cars))
            self.roles_by_index[drone.index] = role

        self.drone_going_for_ball = drone_by_car_id.get(context.attacker_id)
        farthest_role = max(self.roles_by_index.items(), key=lambda pair: pair[1], default=(None, None))[0]
        self.defending_drone = next((drone for drone in drones if drone.index == farthest_role), None)

        for drone in drones:
            if not isinstance(drone.maneuver, PickupBoostPad) and drone in self.boost_reservations:
                del self.boost_reservations[drone]

        for drone in drones:
            role = context.role_by_id.get(drone.car.id, len(active_cars))
            intercept = context.intercepts_by_id.get(drone.car.id)
            can_assign = drone.maneuver is None or drone.maneuver.interruptible()
            if not can_assign or intercept is None:
                continue

            if context.danger > 0.86 and role <= 1 and ground_distance(intercept, our_goal) < 4600:
                drone.maneuver = defense.any_clear(info, drone.car)
                continue

            if role == 0:
                attack_alignment = align(intercept.car.position, intercept.ball, their_goal)
                if (
                    attack_alignment > -0.25 + skill.aggression * 0.35
                    or ground_distance(intercept, our_goal) > 5800
                    or context.time_advantage > 0.20
                ):
                    drone.maneuver = offense.any_shot(
                        info,
                        intercept.car,
                        their_goal,
                        intercept,
                        allow_dribble=not info.is_puck and mechanics > 0.58,
                    )
                else:
                    drone.maneuver = defense.any_clear(info, drone.car)
                continue

            if (
                drone.car.boost < low_boost_threshold
                and is_safe_to_detour_for_boost(info, context, drone.car)
            ):
                self.send_drone_for_boost(drone)
                if drone.maneuver is not None:
                    continue

            if (
                role >= 2
                and context.danger > 0.74
                and intercept.time < context.attacker_intercept.time + commit_window
            ):
                drone.maneuver = defense.any_clear(info, drone.car)
                continue

            face_target = support_face_target(info, context, drone.car)
            distance_from_target = support_distance_for_role(info, context, drone.car, role)
            force_nearest = (
                role >= len(active_cars) - 1
                and info.settings.teamplay.conservative_last_man
                and context.danger > 0.4
            )
            drone.maneuver = GeneralDefense(drone.car, info, face_target, distance_from_target, force_nearest=force_nearest)

    def avoid_demos_and_team_bumps(self, drones: List[Drone]):
        collisions = self.info.detect_collisions(time_limit=0.2, dt=1 / 60)
        drones_by_index: Dict[int, Drone] = {drone.index: drone for drone in drones}

        for collision in collisions:
            index1, index2, time = collision
            self.logger.debug(f"Collision: {index1} ->*<- {index2} in {time:.2f} seconds.")

            # avoid team bumps
            if index1 in drones_by_index and index2 in drones_by_index:
                role1 = self.roles_by_index.get(index1, 99)
                role2 = self.roles_by_index.get(index2, 99)

                if role1 == role2:
                    speed1 = norm(drones_by_index[index1].car.velocity)
                    speed2 = norm(drones_by_index[index2].car.velocity)
                    jumper = index1 if speed1 < speed2 else index2
                else:
                    jumper = index1 if role1 > role2 else index2

                drones_by_index[jumper].controls.jump = drones_by_index[jumper].car.on_ground

            # dodge demolitions
            elif index1 in drones_by_index:
                opponent = self.info.cars[index2]
                if norm(opponent.velocity) > 1900 and time < 0.18:
                    drones_by_index[index1].controls.jump = drones_by_index[index1].car.on_ground

            elif index2 in drones_by_index:
                opponent = self.info.cars[index1]
                if norm(opponent.velocity) > 1900 and time < 0.18:
                    drones_by_index[index2].controls.jump = drones_by_index[index2].car.on_ground

    def render(self, draw: DrawingTool):
        pass
