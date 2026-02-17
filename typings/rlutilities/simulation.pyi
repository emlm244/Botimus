from typing import Any


class Input:
    throttle: float
    steer: float
    pitch: float
    yaw: float
    roll: float
    jump: bool
    boost: bool
    handbrake: bool
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


class BoostPadType:
    Full: int
    Partial: int


class BoostPadState:
    Available: int
    Unavailable: int


class BoostPad:
    timer: float
    state: Any
    type: Any
    position: Any
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...


class Ball:
    time: float
    position: Any
    velocity: Any
    angular_velocity: Any
    radius: float
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def step(self, dt: float) -> None: ...


class Car:
    id: int
    team: int
    boost: float
    time: float
    on_ground: bool
    demolished: bool
    position: Any
    velocity: Any
    angular_velocity: Any
    orientation: Any
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def forward(self) -> Any: ...
    def up(self) -> Any: ...
    def step(self, controls: Any, dt: float) -> None: ...


class Goal:
    center: Any


class Game:
    gravity: Any
    ball: Ball
    cars: list[Car]
    pads: list[BoostPad]
    goals: list[Goal]
    time: float
    time_delta: float
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    @staticmethod
    def set_mode(mode: str) -> None: ...
    def read_field_info(self, field_info: Any) -> None: ...
    def read_packet(self, packet: Any) -> None: ...


class ray:
    direction: Any
    start: Any


class sphere:
    def __init__(self, center: Any, radius: float) -> None: ...


class Field:
    @staticmethod
    def collide(value: Any) -> ray: ...

