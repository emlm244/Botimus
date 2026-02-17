from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Local smoke runner for Botimus")
    parser.add_argument("--mode", choices=["ball", "puck"], default="ball")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    print(f"Running local smoke checks in mode={args.mode}")

    compile_cmd = [sys.executable, "-m", "compileall", "agent.py", "hivemind.py", "strategy", "tools", "maneuvers"]
    result = subprocess.run(compile_cmd, cwd=root, check=False)
    if result.returncode != 0:
        return result.returncode

    harness_cmd = [sys.executable, "-m", "harness.runner", "--mode", args.mode]
    return subprocess.run(harness_cmd, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

