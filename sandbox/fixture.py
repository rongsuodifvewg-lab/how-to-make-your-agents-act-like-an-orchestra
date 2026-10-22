"""Deterministic software-maintenance fixture with hidden acceptance state."""
from __future__ import annotations

from dataclasses import dataclass

from orchestra.schema import TaskNode, TaskSpec


@dataclass
class FixtureCase:
    task: TaskSpec
    expected_patch: str
    current_patch: str = ""
    test_runs: int = 0


def make_tasks() -> tuple[TaskSpec, ...]:
    tasks: list[TaskSpec] = []
    for index, (family, description, expected) in enumerate(
        (("validation", "reject an invalid status value", "status_guard"),
         ("serialization", "preserve a stable field order", "stable_order"),
         ("retry", "avoid retrying a confirmed success", "success_guard")),
        start=1,
    ):
        task_id = f"fixture-{index}"
        tasks.append(TaskSpec(task_id, family, description, ("patch_applied", "hidden_tests_pass"), (
            TaskNode("plan", "understand issue", allowed_tools=("read_task",)),
            TaskNode("patch", "apply minimal patch", ("planned",), ("issue:visible",), ("write_patch",), ("plan",)),
            TaskNode("verify", "run acceptance tests", ("patched",), (), ("run_tests",), ("patch",)),
        ), "fixture-v1", f"hidden-{expected}"))
    return tuple(tasks)


class FixtureSandbox:
    """Each run resets a fresh case; hidden expected_patch never enters messages."""

    def __init__(self) -> None:
        self.case: FixtureCase | None = None
        self.reset_count = 0

    def reset(self, task: TaskSpec) -> str:
        expected = {"fixture-1": "status_guard", "fixture-2": "stable_order", "fixture-3": "success_guard"}[task.task_id]
        self.case = FixtureCase(task, expected)
        self.reset_count += 1
        return f"reset-{self.reset_count}"

    def execute(self, task: TaskSpec, role: str, action: str) -> dict[str, object]:
        if self.case is None or self.case.task.task_id != task.task_id:
            raise ValueError("sandbox must be reset before execution")
        case = self.case
        if role == "planner":
            return {"claim": "task decomposed into plan, patch, and verify", "evidence_ids": ("issue:visible",), "state": {"planned": True}}
        if role == "retriever":
            return {"claim": "retrieved repository conventions", "evidence_ids": ("repo:convention",), "state": {"context_ready": True}}
        if role == "implementer":
            case.current_patch = case.expected_patch
            return {"claim": "minimal patch applied in sandbox", "evidence_ids": ("diff:sandbox",), "state": {"patch_applied": True}}
        if role == "tester":
            case.test_runs += 1
            return {"claim": "hidden acceptance tests passed", "evidence_ids": ("test:hidden_result",), "state": {"tests_passed": case.current_patch == case.expected_patch}}
        if role == "reviewer":
            return {"claim": "patch is minimal and reviewable", "evidence_ids": ("review:sandbox",), "state": {"review_passed": True}}
        raise ValueError(f"unknown role: {role}")
