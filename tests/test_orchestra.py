import unittest
import sys
import tempfile
from pathlib import Path

from orchestra.ledger import Ledger
from orchestra.runtime import OrchestraRuntime
from orchestra.schema import Budget, TypedMessage
from orchestra.verifier import VerificationError, Verifier
from sandbox.fixture import FixtureSandbox, make_tasks
from benchmarks.schema import BenchmarkPlan, BenchmarkTask, load_plan
from evals.benchmark import run_external
from evals.statistics import paired_summary


class OrchestraTests(unittest.TestCase):
    def test_adaptive_runtime_completes_all_fixture_tasks(self):
        for task in make_tasks():
            result = OrchestraRuntime(FixtureSandbox()).run(task)
            self.assertTrue(result.success, result)
            self.assertEqual(result.safety_violations, 0)
            self.assertEqual(result.calls, 5)

    def test_fixed_budget_stops_before_unsafe_continuation(self):
        result = OrchestraRuntime(FixtureSandbox(), budget=Budget(call_limit=2)).run(make_tasks()[0])
        self.assertFalse(result.success)
        self.assertEqual(result.failure_reason, "routing_budget_exhausted")

    def test_message_requires_evidence(self):
        with self.assertRaises(ValueError):
            TypedMessage("fixture-1", None, "planner", "claim", (), 0.9, "next", 9999999999)

    def test_ledger_hash_chain(self):
        ledger = Ledger()
        ledger.append("decision", "t", "continue", {"x": 1})
        ledger.append("decision", "t", "stop", {"x": 2})
        self.assertTrue(ledger.verify_chain())

    def test_expired_message_is_rejected(self):
        message = TypedMessage("fixture-1", None, "planner", "claim", ("e1",), 0.9, "next", 1)
        with self.assertRaises(VerificationError):
            Verifier().validate_message(message, make_tasks()[0], 2)

    def test_unauthorized_tool_is_rejected(self):
        agent = OrchestraRuntime(FixtureSandbox()).agents["planner"]
        with self.assertRaises(VerificationError):
            Verifier().authorize(agent, "write_patch", Budget(), 0)

    def test_cyclic_task_dag_is_rejected(self):
        task = make_tasks()[0]
        from orchestra.schema import TaskNode, TaskSpec
        cyclic = TaskSpec(task.task_id, task.family, task.description, task.acceptance, (
            TaskNode("a", "a", depends_on=("b",)),
            TaskNode("b", "b", depends_on=("a",)),
        ), task.snapshot_version, task.hidden_case_id)
        with self.assertRaises(ValueError):
            cyclic.validate_dag()

    def test_external_protocol_is_explicitly_pending(self):
        root = Path(__file__).resolve().parents[1]
        plan = load_plan(root / "benchmarks" / "real_manifest.json")
        self.assertEqual(plan.status, "ready")
        self.assertEqual(len(plan.tasks), 30)
        self.assertGreaterEqual(plan.minimum_tasks, 30)
        self.assertIn("adaptive_orchestra", plan.variants)

    def test_statistics_fail_closed_without_pairs(self):
        summary = paired_summary([], treatment="adaptive_orchestra", control="single_agent")
        self.assertEqual(summary["status"], "INSUFFICIENT_PAIRED_RUNS")

    def test_statistics_compute_paired_delta(self):
        rows = [
            {"task_id": "a", "seed": 1, "variant": "single_agent", "success": False, "cost": 1.0, "safety_violations": 0},
            {"task_id": "a", "seed": 1, "variant": "adaptive_orchestra", "success": True, "cost": 0.8, "safety_violations": 0},
            {"task_id": "b", "seed": 1, "variant": "single_agent", "success": True, "cost": 1.0, "safety_violations": 0},
            {"task_id": "b", "seed": 1, "variant": "adaptive_orchestra", "success": True, "cost": 0.9, "safety_violations": 0},
        ]
        summary = paired_summary(rows, treatment="adaptive_orchestra", control="single_agent")
        self.assertEqual(summary["status"], "READY")
        self.assertEqual(summary["pairs"], 2)
        self.assertEqual(summary["success_delta"], 0.5)
        self.assertLess(summary["cost_delta"], 0)

    def test_external_runner_validates_adapter_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adapter = root / "adapter.py"
            adapter.write_text(
                "import json\n"
                "print(json.dumps({'success': True, 'cost': 0.1, 'latency_ms': 2, 'calls': 1, 'tokens': 3, 'safety_violations': 0}))\n",
                encoding="utf-8",
            )
            task = BenchmarkTask("t", "bugfix", "https://example.invalid/repo.git", "a" * 40, "fix", "visible", "hidden")
            plan = BenchmarkPlan(
                "test", "claim", "source", "revision", 1, 1, (1,), ("single_agent", "adaptive_orchestra"), (task,), "ready", ("independent evaluator",)
            )
            report = run_external(plan, (sys.executable, str(adapter)), root / "report.json", timeout_s=10)
            self.assertEqual(report["status"], "COMPLETE")
            self.assertEqual(len(report["rows"]), 2)
            self.assertTrue((root / "report.json").exists())


if __name__ == "__main__":
    unittest.main()
