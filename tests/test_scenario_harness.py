from __future__ import annotations

import json
from pathlib import Path

from harness.policy import evaluate_scenario
from harness.runner import run
from harness.scenarios import get_scenarios
from tools.bot_settings import default_settings


def test_scenario_catalog_size_and_uniqueness() -> None:
    scenarios = get_scenarios()
    assert len(scenarios) >= 12
    assert len({scenario.scenario_id for scenario in scenarios}) == len(scenarios)


def test_scenario_evaluations_pass_defaults() -> None:
    settings = default_settings()
    results = [evaluate_scenario(scenario, settings=settings) for scenario in get_scenarios()]
    failures = [result for result in results if not result.passed]
    assert not failures, f"Scenario failures: {[failure.scenario_id for failure in failures]}"


def test_runner_writes_report(tmp_path: Path) -> None:
    report_path = tmp_path / "harness_report.json"
    exit_code = run(mode="all", report_path=str(report_path))
    assert exit_code == 0
    assert report_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["summary"]["failed"] == 0
    assert payload["summary"]["total"] >= 12
    assert len(payload["results"]) == payload["summary"]["total"]

