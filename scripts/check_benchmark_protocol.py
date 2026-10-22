from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks.schema import ProtocolError, load_plan


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "benchmarks" / "real_manifest.json"
    try:
        plan = load_plan(path)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}))
        return 1
    print(json.dumps({
        "status": "PASS",
        "benchmark_id": plan.benchmark_id,
        "state": plan.status,
        "minimum_tasks": plan.minimum_tasks,
        "pinned_tasks": len(plan.tasks),
        "variants": list(plan.variants),
        "external_run": "PENDING_TASK_MANIFEST" if not plan.tasks else "READY",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

