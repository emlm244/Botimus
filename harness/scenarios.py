from __future__ import annotations

from harness.models import BallState, CarState, MatchState, Scenario, ScenarioExpectation, Vec3


def _car(
    car_id: int,
    team: int,
    x: float,
    y: float,
    vx: float,
    vy: float,
    boost: float,
    *,
    is_human: bool = False,
) -> CarState:
    return CarState(
        car_id=car_id,
        team=team,
        position=Vec3(x, y, 17.0),
        velocity=Vec3(vx, vy, 0.0),
        boost=boost,
        is_human=is_human,
    )


def get_scenarios() -> list[Scenario]:
    scenarios: list[Scenario] = []

    scenarios.append(
        Scenario(
            scenario_id="2v2_attack_first_man",
            description="Bot is fastest challenge in 2v2 and should take first-man attack.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(0, 1200, 95), velocity=Vec3(0, 400, 0)),
                cars=[
                    _car(1, 0, -200, 100, 300, 700, 44, is_human=False),
                    _car(2, 0, -1800, -900, 100, 350, 52, is_human=True),
                    _car(21, 1, 900, 1600, 0, -300, 35),
                    _car(22, 1, -700, 2100, 0, -200, 62),
                ],
            ),
            expectation=ScenarioExpectation(action="attack", role=0),
            tags=("2v2", "offense"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="2v2_support_second_man",
            description="Bot is second man and should support behind first-man teammate.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(300, 1700, 100), velocity=Vec3(-150, 250, 0)),
                cars=[
                    _car(1, 0, -1200, 200, 200, 500, 58),
                    _car(2, 0, 200, 900, 350, 850, 41, is_human=True),
                    _car(21, 1, 800, 1500, 0, -500, 28),
                    _car(22, 1, -900, 2200, 50, -400, 36),
                ],
            ),
            expectation=ScenarioExpectation(action="support", role=1, max_double_commit_risk=0.85),
            tags=("2v2", "support"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="2v2_safe_boost_detour",
            description="Second-man bot with low boost and safe time buffer should choose boost.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(-400, 2300, 93), velocity=Vec3(0, 120, 0)),
                cars=[
                    _car(1, 0, -2100, -300, 100, 300, 6),
                    _car(2, 0, -300, 1100, 550, 950, 56, is_human=True),
                    _car(21, 1, 2000, 2600, -200, -150, 50),
                    _car(22, 1, -1700, 2800, 100, -250, 47),
                ],
            ),
            expectation=ScenarioExpectation(action="boost", role=1),
            tags=("2v2", "boost"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="3v3_last_man_defend",
            description="Bot is third man in 3v3 with pressure and must defend.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(200, -2800, 120), velocity=Vec3(120, -900, 0)),
                cars=[
                    _car(1, 0, -300, -4200, 200, 150, 36),
                    _car(2, 0, 500, -900, 450, 800, 52, is_human=True),
                    _car(3, 0, -800, -1200, 350, 700, 61),
                    _car(21, 1, -200, -2100, 100, -800, 48),
                    _car(22, 1, 900, -1700, -100, -700, 59),
                    _car(23, 1, -1200, -1200, 0, -750, 63),
                ],
            ),
            expectation=ScenarioExpectation(action="defend", role=2),
            tags=("3v3", "last_man"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="3v3_second_man_support",
            description="Bot is second man in balanced 3v3 and should support.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(400, 700, 110), velocity=Vec3(0, 600, 0)),
                cars=[
                    _car(1, 0, -500, -600, 350, 650, 42),
                    _car(2, 0, 100, 300, 450, 900, 48, is_human=True),
                    _car(3, 0, -1100, -2600, 200, 320, 70),
                    _car(21, 1, 700, 1200, -150, -650, 45),
                    _car(22, 1, -600, 1800, 100, -500, 55),
                    _car(23, 1, 1000, 2200, -50, -400, 49),
                ],
            ),
            expectation=ScenarioExpectation(action="support", role=1, max_double_commit_risk=0.90),
            tags=("3v3", "rotation"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="3v3_emergency_clear",
            description="High danger and close intercept should force defensive action.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(-300, -3200, 90), velocity=Vec3(20, -1000, 0)),
                cars=[
                    _car(1, 0, -700, -2700, 350, -350, 52),
                    _car(2, 0, 600, -1400, 350, 400, 46, is_human=True),
                    _car(3, 0, -1200, -4300, 100, 180, 62),
                    _car(21, 1, -200, -2800, 0, -700, 54),
                    _car(22, 1, 900, -2500, -100, -650, 58),
                    _car(23, 1, -900, -2300, 40, -600, 45),
                ],
            ),
            expectation=ScenarioExpectation(action="defend", max_double_commit_risk=0.95),
            tags=("3v3", "defense"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="3v3_anti_double_commit_support",
            description="Bot should avoid over-committing when attacker has similar timing.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(0, 1400, 100), velocity=Vec3(0, 100, 0)),
                cars=[
                    _car(1, 0, -200, 300, 350, 650, 38),
                    _car(2, 0, 100, 520, 340, 700, 41, is_human=True),
                    _car(3, 0, -800, -2100, 250, 350, 59),
                    _car(21, 1, 400, 1700, 0, -450, 60),
                    _car(22, 1, -500, 1900, 50, -420, 52),
                    _car(23, 1, 1200, 2200, 0, -380, 49),
                ],
            ),
            expectation=ScenarioExpectation(action="support", role=1, max_double_commit_risk=1.0),
            tags=("3v3", "anti_double_commit"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="2v2_human_follow_balance",
            description="Human teammate pushes first; bot should fill support lane.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="ball",
                ball=BallState(position=Vec3(350, 1850, 95), velocity=Vec3(20, 300, 0)),
                cars=[
                    _car(1, 0, -1400, 0, 200, 430, 47),
                    _car(2, 0, 120, 980, 520, 880, 43, is_human=True),
                    _car(21, 1, 700, 1700, 0, -450, 41),
                    _car(22, 1, -800, 2000, 30, -300, 38),
                ],
            ),
            expectation=ScenarioExpectation(action="support", role=1),
            tags=("2v2", "human_follow"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="puck_kickoff_lane_attack",
            description="Puck mode kickoff lane where bot should still challenge as first man.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="puck",
                ball=BallState(position=Vec3(0, 0, 60), velocity=Vec3(0, 0, 0)),
                cars=[
                    _car(1, 0, 0, -1900, 0, 1150, 34),
                    _car(2, 0, -2300, -2600, 0, 900, 50, is_human=True),
                    _car(21, 1, 0, 1900, 0, -1050, 37),
                    _car(22, 1, 2300, 2600, 0, -900, 55),
                ],
            ),
            expectation=ScenarioExpectation(action="attack", role=0),
            tags=("puck", "kickoff"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="puck_corner_support",
            description="Puck in corner with teammate close; bot should support not over-commit.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="puck",
                ball=BallState(position=Vec3(3400, 2600, 65), velocity=Vec3(-500, 120, 0)),
                cars=[
                    _car(1, 0, 1400, 1200, 250, 500, 33),
                    _car(2, 0, 2700, 2300, 450, 550, 40, is_human=True),
                    _car(21, 1, 3100, 2400, -300, -250, 48),
                    _car(22, 1, 1500, 1800, 0, -350, 42),
                ],
            ),
            expectation=ScenarioExpectation(action="support", role=1),
            tags=("puck", "support"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="puck_last_man_hold",
            description="3v3 puck transition where bot is last back and should defend.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="puck",
                ball=BallState(position=Vec3(-200, -2500, 62), velocity=Vec3(100, -750, 0)),
                cars=[
                    _car(1, 0, -700, -4200, 200, 200, 45),
                    _car(2, 0, 500, -1200, 420, 620, 52, is_human=True),
                    _car(3, 0, -1200, -1800, 300, 560, 48),
                    _car(21, 1, 300, -1900, -50, -650, 59),
                    _car(22, 1, -600, -1700, 0, -700, 54),
                    _car(23, 1, 900, -1500, -80, -640, 46),
                ],
            ),
            expectation=ScenarioExpectation(action="defend", role=2),
            tags=("puck", "3v3", "last_man"),
        )
    )

    scenarios.append(
        Scenario(
            scenario_id="puck_safe_boost_window",
            description="Low boost support bot in puck mode takes safe boost detour.",
            bot_car_id=1,
            state=MatchState(
                our_team=0,
                object_mode="puck",
                ball=BallState(position=Vec3(200, 2100, 60), velocity=Vec3(-80, 160, 0)),
                cars=[
                    _car(1, 0, -2000, -700, 100, 280, 5),
                    _car(2, 0, -200, 1100, 500, 820, 52, is_human=True),
                    _car(21, 1, 1700, 2500, -180, -170, 49),
                    _car(22, 1, -1500, 2400, 70, -260, 51),
                ],
            ),
            expectation=ScenarioExpectation(action="boost", role=1),
            tags=("puck", "boost"),
        )
    )

    return scenarios

