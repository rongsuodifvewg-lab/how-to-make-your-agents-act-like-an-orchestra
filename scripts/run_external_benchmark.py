from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.schema import ProtocolError, load_plan
from evals.benchmark import run_external


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the pinned real-repository benchmark with an evaluator adapter.")
    parser.add_argument("--manifest", type=Path, default=Path("benchmarks/real_manifest.json"))
    parser.add_argument("--adapter", nargs="+", help="Executable adapter; receives ORCHESTRA_TASK_FILE and related env vars.")
    parser.add_argument("--output", type=Path, default=Path("reports/external_benchmark.json"))
    args = parser.parse_args()
    plan = load_plan(args.manifest)
    if not plan.tasks:
        report = {
            "status": "NOT_RUN_EXTERNAL_TASK_MANIFEST_REQUIRED",
            "benchmark_id": plan.benchmark_id,
            "required_tasks": plan.minimum_tasks,
            "pinned_tasks": 0,
            "reason": "The public protocol is complete, but real task records and a model adapter must be supplied by the evaluator.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 2
    if not args.adapter:
        report = {
            "status": "NOT_RUN_MODEL_ADAPTER_REQUIRED",
            "benchmark_id": plan.benchmark_id,
            "required_tasks": plan.minimum_tasks,
            "pinned_tasks": len(plan.tasks),
            "reason": "The real task manifest is ready, but an evaluator-owned model adapter was not supplied.",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 2
    try:
        report = run_external(plan, args.adapter, args.output)
    except (ProtocolError, OSError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}))
        return 1
    print(json.dumps({"status": report["status"], "rows": len(report["rows"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

