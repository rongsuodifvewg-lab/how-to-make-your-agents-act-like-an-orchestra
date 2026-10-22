from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.statistics import paired_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze raw paired benchmark records without hand-entered values.")
    parser.add_argument("--input", type=Path, default=Path("reports/external_benchmark.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/benchmark_analysis.json"))
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8"))
    if raw.get("status") != "COMPLETE":
        report = {"status": "INCONCLUSIVE_EXTERNAL_RUN_REQUIRED", "source_status": raw.get("status", "UNKNOWN")}
    else:
        rows = raw.get("rows", [])
        report = {
            "status": "COMPLETE",
            "benchmark_id": raw.get("benchmark_id"),
            "source_rows": len(rows),
            "adaptive_vs_single": paired_summary(rows, treatment="adaptive_orchestra", control="single_agent"),
            "fixed_vs_single": paired_summary(rows, treatment="fixed_orchestra", control="single_agent"),
            "adaptive_vs_fixed": paired_summary(rows, treatment="adaptive_orchestra", control="fixed_orchestra"),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
