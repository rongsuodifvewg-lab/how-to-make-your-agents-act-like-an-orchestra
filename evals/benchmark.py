"""Runner for externally supplied real-repository task adapters.

An adapter is an executable owned by the evaluator. It receives a task JSON
path and must print one JSON object with the required metrics. The runner does
not inspect hidden tests or allow an adapter to alter the task manifest.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Sequence

from benchmarks.schema import BenchmarkPlan, ProtocolError


REQUIRED_FIELDS = {"success", "cost", "latency_ms", "calls", "tokens", "safety_violations"}


def _validate_observation(raw: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_FIELDS - raw.keys()
    if missing:
        raise ProtocolError(f"adapter output is missing fields: {sorted(missing)}")
    result = dict(raw)
    result["success"] = bool(result["success"])
    for field in ("cost", "latency_ms", "calls", "tokens", "safety_violations"):
        value = float(result[field])
        if value < 0 or value != value or value == float("inf"):
            raise ProtocolError(f"adapter output has invalid {field}: {value}")
        result[field] = int(value) if field != "cost" else value
    return result


def run_external(plan: BenchmarkPlan, adapter: Sequence[str], output: str | Path, *, timeout_s: int = 1800) -> dict[str, Any]:
    plan.validate(require_tasks=True)
    rows: list[dict[str, Any]] = []
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for task in plan.tasks:
        task_payload = {
            "task_id": task.task_id,
            "family": task.family,
            "repo_url": task.repo_url,
            "base_commit": task.base_commit,
            "task_statement": task.task_statement,
            "visible_test_command": task.visible_test_command,
            "hidden_test_command": task.hidden_test_command,
        }
        task_path = output_path.parent / f".task-{task.task_id}.json"
        task_path.write_text(json.dumps(task_payload, indent=2) + "\n", encoding="utf-8")
        try:
            for seed in plan.seeds:
                for variant in plan.variants:
                    for repetition in range(plan.repetitions):
                        started = time.monotonic()
                        env = os.environ.copy()
                        env.update({
                            "ORCHESTRA_TASK_FILE": str(task_path),
                            "ORCHESTRA_VARIANT": variant,
                            "ORCHESTRA_SEED": str(seed),
                            "ORCHESTRA_REPETITION": str(repetition),
                        })
                        completed = subprocess.run(adapter, capture_output=True, text=True, timeout=timeout_s, env=env)
                        if completed.returncode:
                            raise ProtocolError(f"adapter failed for {task.task_id}/{variant}: {completed.stderr[-500:]}")
                        raw = json.loads(completed.stdout)
                        observation = _validate_observation(raw)
                        observation.update({
                            "task_id": task.task_id,
                            "seed": seed,
                            "variant": variant,
                            "repetition": repetition,
                            "wall_clock_ms": int((time.monotonic() - started) * 1000),
                        })
                        rows.append(observation)
        finally:
            task_path.unlink(missing_ok=True)
    report = {"status": "COMPLETE", "benchmark_id": plan.benchmark_id, "rows": rows}
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report

