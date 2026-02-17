from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from harness.models import EvaluationResult


@dataclass(frozen=True)
class HarnessSummary:
    total: int
    passed: int
    failed: int
    failure_rate: float
    average_double_commit_risk: float
    last_man_violations: int


def build_summary(results: Sequence[EvaluationResult]) -> HarnessSummary:
    total = len(results)
    passed = sum(1 for result in results if result.passed)
    failed = total - passed
    avg_commit = sum(result.double_commit_risk for result in results) / max(total, 1)
    last_man_violations = sum(1 for result in results if result.last_man_violation)
    return HarnessSummary(
        total=total,
        passed=passed,
        failed=failed,
        failure_rate=failed / max(total, 1),
        average_double_commit_risk=avg_commit,
        last_man_violations=last_man_violations,
    )


def write_json_report(path: str | Path, results: Sequence[EvaluationResult]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = build_summary(results)
    payload = {
        "summary": asdict(summary),
        "results": [asdict(result) for result in results],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

