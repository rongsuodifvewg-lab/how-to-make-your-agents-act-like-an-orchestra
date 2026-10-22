import unittest

from orchestra.ledger import Ledger
from orchestra.runtime import OrchestraRuntime
from orchestra.schema import Budget, TypedMessage
from orchestra.verifier import VerificationError, Verifier
from sandbox.fixture import FixtureSandbox, make_tasks


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


if __name__ == "__main__":
    unittest.main()
