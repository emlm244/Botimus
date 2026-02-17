#!/usr/bin/env python
"""Summarize Botimus diagnostics sessions for quick offline tuning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _find_latest_session(root: Path) -> Path | None:
    sessions = [path for path in root.glob("session_*") if path.is_dir()]
    if not sessions:
        return None
    return max(sessions, key=lambda path: path.stat().st_mtime)


def _load_event(path: Path, line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def summarize_session(session_dir: Path) -> dict[str, Any]:
    tick_count = 0
    role_counts: dict[str, int] = {}
    maneuver_counts: dict[str, int] = {}
    quality_counts: dict[str, int] = {}
    takeover_windows_seen = 0
    takeover_windows_taken = 0
    takeover_windows_ignored = 0
    latest_summary: dict[str, Any] | None = None

    for file_path in sorted(session_dir.glob("match_*.jsonl")):
        with file_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                event = _load_event(file_path, line)
                if event is None:
                    continue

                event_type = event.get("event")
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    continue

                if event_type == "tick":
                    tick_count += 1
                    decision = payload.get("decision", {})
                    if isinstance(decision, dict):
                        maneuver = str(decision.get("maneuver", "unknown"))
                        maneuver_counts[maneuver] = maneuver_counts.get(maneuver, 0) + 1

                        trace = decision.get("teamplay_trace")
                        if isinstance(trace, dict):
                            role = str(trace.get("role_label", ""))
                            if role:
                                role_counts[role] = role_counts.get(role, 0) + 1

                            window = _safe_float(trace.get("open_attack_window"), -1.0)
                            threshold = _safe_float(trace.get("takeover_threshold"), 1.0)
                            should_attack = bool(trace.get("should_attack", False))
                            if window >= threshold >= 0.0:
                                takeover_windows_seen += 1
                                if should_attack:
                                    takeover_windows_taken += 1
                                else:
                                    takeover_windows_ignored += 1

                    quality_flags = payload.get("quality_flags")
                    if isinstance(quality_flags, dict):
                        for key, value in quality_flags.items():
                            if bool(value):
                                quality_counts[key] = quality_counts.get(key, 0) + 1

                elif event_type == "match_summary":
                    latest_summary = payload

    top_maneuvers = sorted(maneuver_counts.items(), key=lambda item: item[1], reverse=True)[:8]
    top_quality_flags = sorted(quality_counts.items(), key=lambda item: item[1], reverse=True)[:8]

    return {
        "session_dir": str(session_dir),
        "ticks": tick_count,
        "roles": role_counts,
        "takeover_windows_seen": takeover_windows_seen,
        "takeover_windows_taken": takeover_windows_taken,
        "takeover_windows_ignored": takeover_windows_ignored,
        "takeover_conversion": (
            takeover_windows_taken / takeover_windows_seen if takeover_windows_seen > 0 else None
        ),
        "top_maneuvers": top_maneuvers,
        "top_quality_flags": top_quality_flags,
        "latest_match_summary": latest_summary,
    }


def _print_summary(summary: dict[str, Any]) -> None:
    print(f"Session: {summary['session_dir']}")
    print(f"Ticks: {summary['ticks']}")
    print("Role occupancy:")
    ordered_roles = ["first_man", "second_man", "third_man"]
    dynamic_roles = sorted(role for role in summary["roles"].keys() if role not in ordered_roles)
    for role in ordered_roles + dynamic_roles:
        print(f"  {role}: {summary['roles'].get(role, 0)}")
    print("Takeover windows:")
    print(f"  seen: {summary['takeover_windows_seen']}")
    print(f"  taken: {summary['takeover_windows_taken']}")
    print(f"  ignored: {summary['takeover_windows_ignored']}")
    conversion = summary["takeover_conversion"]
    print(f"  conversion: {conversion:.3f}" if conversion is not None else "  conversion: n/a")
    print("Top maneuvers:")
    for name, count in summary["top_maneuvers"]:
        print(f"  {name}: {count}")
    print("Top quality flags:")
    for name, count in summary["top_quality_flags"]:
        print(f"  {name}: {count}")
    latest = summary["latest_match_summary"]
    if latest:
        print("Latest match summary counters:")
        counters = latest.get("counters")
        if isinstance(counters, dict):
            for key in sorted(counters.keys()):
                print(f"  {key}: {counters[key]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default="logs/diagnostics",
        help="Root diagnostics directory (default: logs/diagnostics)",
    )
    parser.add_argument(
        "--session",
        default=None,
        help="Optional explicit session directory. If omitted, uses latest session_*.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if args.session:
        session_dir = Path(args.session)
    else:
        session_dir = _find_latest_session(root)

    if session_dir is None or not session_dir.exists():
        print("No diagnostics session found.")
        return 1

    summary = summarize_session(session_dir)
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
