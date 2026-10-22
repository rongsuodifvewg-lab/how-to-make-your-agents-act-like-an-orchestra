"""Paired fixture evaluation for baseline and adaptive orchestration."""
from __future__ import annotations

from dataclasses import asdict

from orchestra.runtime import OrchestraRuntime
from sandbox.fixture import FixtureSandbox, make_tasks


def compare_baselines() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for task in make_tasks():
        for variant, adaptive in (("fixed_orchestra", False), ("adaptive_orchestra", True)):
            result = OrchestraRuntime(FixtureSandbox(), adaptive=adaptive).run(task)
            rows.append({"task_id": task.task_id, "variant": variant, **asdict(result)})
    grouped: dict[str, dict[str, object]] = {}
    for variant in {row["variant"] for row in rows}:
        subset = [row for row in rows if row["variant"] == variant]
        grouped[variant] = {"pass_rate": sum(bool(x["success"]) for x in subset) / len(subset), "mean_cost": sum(float(x["cost"]) for x in subset) / len(subset), "safety_violations": sum(int(x["safety_violations"]) for x in subset)}
    return {"rows": rows, "summary": grouped, "claim_boundary": "fixture mechanism evidence only; real benchmark required"}
