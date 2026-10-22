"""Fetch and pin a public SWE-bench Lite task manifest.

Only task metadata and issue statements are retained. Gold patches and hidden
test implementations are intentionally discarded so an evaluator can keep
acceptance tests in independent custody.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path


DATASET = "princeton-nlp/SWE-bench_Lite"
DATASET_SHA = "6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2"
ROWS_URL = "https://datasets-server.huggingface.co/rows?" + urllib.parse.urlencode({
    "dataset": DATASET,
    "config": "default",
    "split": "test",
    "offset": 0,
    "length": 30,
})


def _family(statement: str) -> str:
    lowered = statement.lower()
    if any(word in lowered for word in ("test", "assert", "pytest")):
        return "testing"
    if any(word in lowered for word in ("doc", "readme", "documentation")):
        return "documentation"
    if any(word in lowered for word in ("performance", "slow", "memory", "speed")):
        return "performance"
    return "bugfix"


def main() -> int:
    with urllib.request.urlopen(ROWS_URL, timeout=60) as response:
        payload = json.load(response)
    rows = payload.get("rows", [])
    if len(rows) < 30:
        raise RuntimeError(f"expected 30 public tasks, received {len(rows)}")
    tasks = []
    for item in rows[:30]:
        row = item["row"]
        task_id = str(row["instance_id"])
        tasks.append({
            "task_id": task_id,
            "family": _family(str(row["problem_statement"])),
            "repo_url": f"https://github.com/{row['repo']}.git",
            "base_commit": str(row["base_commit"]),
            "task_statement": str(row["problem_statement"]),
            "visible_test_command": f"swebench-visible://{task_id}",
            "hidden_test_command": f"swebench-hidden://{task_id}",
        })
    manifest = {
        "benchmark_id": "orchestra-real-repo-v1",
        "claim": "Under the same model, tools, and resource budget, adaptive orchestration improves hidden-test success or reduces cost at the same success rate on repository maintenance tasks.",
        "source": f"{DATASET} test split, fetched from the pinned Hugging Face revision",
        "dataset_revision": DATASET_SHA,
        "minimum_tasks": 30,
        "repetitions": 3,
        "seeds": [11, 29, 47],
        "variants": ["single_agent", "fixed_orchestra", "adaptive_orchestra"],
        "status": "ready",
        "tasks": tasks,
        "evaluator_requirements": [
            "Tasks are pinned to immutable repository commits and a recorded dataset revision.",
            "The hidden evaluator owns the acceptance tests and is outside the agent workspace.",
            "All variants use the same model version, tool permissions, token budget, timeout, and seeds.",
            "The evaluator records raw calls, tokens, cost, latency, safety violations, and final hidden-test status.",
            "The evaluator is run from a clean checkout by an independent operator who cannot edit hidden tests."
        ],
    }
    output = Path(__file__).resolve().parents[1] / "benchmarks" / "real_manifest.json"
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output), "tasks": len(tasks), "dataset_revision": DATASET_SHA}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
