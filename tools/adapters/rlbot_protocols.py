from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable


@runtime_checkable
class Vector3Like(Protocol):
    x: float
    y: float
    z: float


@runtime_checkable
class PhysicsLike(Protocol):
    location: Vector3Like
    velocity: Vector3Like
    angular_velocity: Vector3Like


@runtime_checkable
class BallPredictionSliceLike(Protocol):
    game_seconds: float
    physics: PhysicsLike


@runtime_checkable
class BallPredictionLike(Protocol):
    num_slices: int
    slices: Sequence[BallPredictionSliceLike]

