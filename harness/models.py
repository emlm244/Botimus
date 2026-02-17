from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Sequence

ObjectMode = Literal["ball", "puck"]
RecommendedAction = Literal["attack", "support", "defend", "boost"]


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float = 0.0

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def scale(self, factor: float) -> "Vec3":
        return Vec3(self.x * factor, self.y * factor, self.z * factor)

    def norm_xy(self) -> float:
        return float((self.x * self.x + self.y * self.y) ** 0.5)

    def distance_xy(self, other: "Vec3") -> float:
        return (self - other).norm_xy()


@dataclass(frozen=True)
class CarState:
    car_id: int
    team: int
    position: Vec3
    velocity: Vec3
    boost: float
    on_ground: bool = True
    demolished: bool = False
    is_human: bool = False

    def speed_xy(self) -> float:
        return self.velocity.norm_xy()


@dataclass(frozen=True)
class BallState:
    position: Vec3
    velocity: Vec3


@dataclass(frozen=True)
class MatchState:
    our_team: int
    object_mode: ObjectMode
    ball: BallState
    cars: Sequence[CarState]

    @property
    def my_goal(self) -> Vec3:
        return Vec3(0.0, -5120.0 if self.our_team == 0 else 5120.0, 0.0)

    @property
    def their_goal(self) -> Vec3:
        return Vec3(0.0, 5120.0 if self.our_team == 0 else -5120.0, 0.0)

    def teammates(self) -> list[CarState]:
        return [car for car in self.cars if car.team == self.our_team and not car.demolished]

    def opponents(self) -> list[CarState]:
        return [car for car in self.cars if car.team != self.our_team and not car.demolished]


@dataclass(frozen=True)
class ScenarioExpectation:
    action: RecommendedAction
    role: int | None = None
    max_double_commit_risk: float = 1.0
    allow_last_man_attack: bool = False


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    bot_car_id: int
    state: MatchState
    expectation: ScenarioExpectation
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EvaluationResult:
    scenario_id: str
    passed: bool
    action: RecommendedAction
    role: int
    attacker_id: int
    double_commit_risk: float
    last_man_violation: bool
    message: str
