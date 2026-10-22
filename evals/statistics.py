"""Dependency-free statistics for paired benchmark results."""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Any, Iterable


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def bootstrap_mean(values: list[float], *, seed: int = 0, samples: int = 2000) -> tuple[float, float]:
    """Return a deterministic percentile bootstrap 95% interval."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    draws = [_mean([values[rng.randrange(len(values))] for _ in values]) for _ in range(samples)]
    return (_percentile(draws, 0.025), _percentile(draws, 0.975))


def paired_summary(rows: Iterable[dict[str, Any]], *, treatment: str, control: str) -> dict[str, Any]:
    """Compare two variants on the same task and seed, failing closed on gaps."""
    paired: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = (str(row["task_id"]), int(row["seed"]))
        paired[key][str(row["variant"])] = row
    pairs = [pair for pair in paired.values() if treatment in pair and control in pair]
    success_deltas = [float(pair[treatment]["success"]) - float(pair[control]["success"]) for pair in pairs]
    cost_deltas = [float(pair[treatment]["cost"]) - float(pair[control]["cost"]) for pair in pairs]
    if not pairs:
        return {"status": "INSUFFICIENT_PAIRED_RUNS", "pairs": 0, "treatment": treatment, "control": control}
    success_ci = bootstrap_mean(success_deltas, seed=17)
    cost_ci = bootstrap_mean(cost_deltas, seed=23)
    return {
        "status": "READY" if len(pairs) >= 2 else "INSUFFICIENT_PAIRED_RUNS",
        "pairs": len(pairs),
        "treatment": treatment,
        "control": control,
        "treatment_success_rate": _mean([float(pair[treatment]["success"]) for pair in pairs]),
        "control_success_rate": _mean([float(pair[control]["success"]) for pair in pairs]),
        "success_delta": _mean(success_deltas),
        "success_delta_ci95": list(success_ci),
        "cost_delta": _mean(cost_deltas),
        "cost_delta_ci95": list(cost_ci),
        "safety_violations_treatment": sum(int(pair[treatment].get("safety_violations", 0)) for pair in pairs),
        "safety_violations_control": sum(int(pair[control].get("safety_violations", 0)) for pair in pairs),
    }

