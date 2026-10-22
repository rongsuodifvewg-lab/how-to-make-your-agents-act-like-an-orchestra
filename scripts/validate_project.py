from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    checks: list[dict[str, object]] = []
    def check(name: str, value: bool, detail: str = "") -> None:
        checks.append({"check": name, "status": "PASS" if value else "FAIL", "detail": detail})
    check("readme_exists", (ROOT / "README.md").exists())
    check("typed_schema", (ROOT / "orchestra" / "schema.py").exists())
    check("verifier_gate", (ROOT / "orchestra" / "verifier.py").exists())
    check("adaptive_router", (ROOT / "orchestra" / "router.py").exists())
    check("resettable_fixture", (ROOT / "sandbox" / "fixture.py").exists())
    check("experiment_runner", (ROOT / "evals" / "runner.py").exists())
    check("claim_boundary_documented", "real benchmark" in (ROOT / "README.md").read_text(encoding="utf-8"))
    test = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=ROOT, capture_output=True, text=True)
    check("unit_tests", test.returncode == 0, (test.stdout + test.stderr)[-1000:])
    report = {"gate": "ORCHESTRA-RELEASE", "status": "PASS" if all(x["status"] == "PASS" for x in checks) else "FAIL", "checks": checks, "claim_boundary": "fixture mechanism evidence only; external hidden benchmark required"}
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": report["gate"], "status": report["status"], "checks": len(checks)}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
