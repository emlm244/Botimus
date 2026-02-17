from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal

from harness.policy import evaluate_scenario
from harness.report import build_summary, write_json_report
from harness.scenarios import get_scenarios
from tools.bot_settings import default_settings

RunMode = Literal["all", "ball", "puck"]


def run(mode: RunMode = "all", report_path: str | None = None) -> int:
    all_scenarios = get_scenarios()
    if mode == "all":
        scenarios = all_scenarios
    else:
        scenarios = [scenario for scenario in all_scenarios if scenario.state.object_mode == mode]

    settings = default_settings()
    results = [evaluate_scenario(scenario, settings=settings) for scenario in scenarios]
    summary = build_summary(results)

    print(
        f"Scenarios: {summary.total} | passed: {summary.passed} | failed: {summary.failed} "
        f"| avg_double_commit_risk: {summary.average_double_commit_risk:.3f}"
    )

    for result in results:
        state = "PASS" if result.passed else "FAIL"
        print(f"[{state}] {result.scenario_id}: {result.message}")

    if report_path:
        write_json_report(report_path, results)
        print(f"Report written to {Path(report_path).resolve()}")

    return 1 if summary.failed else 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic Botimus scenario harness")
    parser.add_argument(
        "--mode",
        choices=["all", "ball", "puck"],
        default="all",
        help="Scenario mode filter",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Optional output JSON report path",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()
    return run(mode=args.mode, report_path=args.report)


if __name__ == "__main__":
    raise SystemExit(main())

