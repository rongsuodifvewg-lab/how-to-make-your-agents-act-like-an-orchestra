"""Contracts for the external evaluation protocol.

The protocol is deliberately independent of a model provider. An evaluator
provides a pinned task manifest and an adapter command; the runner records the
same fields for every baseline and treatment.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ProtocolError(ValueError):
    """Raised when a benchmark manifest cannot support a fair comparison."""


@dataclass(frozen=True)
class BenchmarkTask:
    task_id: str
    family: str
    repo_url: str
    base_commit: str
    task_statement: str
    visible_test_command: str
    hidden_test_command: str

    def validate(self) -> None:
        fields = {
            "task_id": self.task_id,
            "family": self.family,
            "repo_url": self.repo_url,
            "base_commit": self.base_commit,
            "task_statement": self.task_statement,
            "visible_test_command": self.visible_test_command,
            "hidden_test_command": self.hidden_test_command,
        }
        if any(not str(value).strip() for value in fields.values()):
            raise ProtocolError(f"task has an empty field: {fields}")
        if any(token in self.base_commit.lower() for token in ("latest", "head", "todo", "replace")):
            raise ProtocolError(f"task {self.task_id} must pin an immutable base commit")
        if self.visible_test_command == self.hidden_test_command:
            raise ProtocolError(f"task {self.task_id} must keep hidden tests distinct")

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BenchmarkTask":
        task = cls(
            task_id=str(raw["task_id"]),
            family=str(raw["family"]),
            repo_url=str(raw["repo_url"]),
            base_commit=str(raw["base_commit"]),
            task_statement=str(raw["task_statement"]),
            visible_test_command=str(raw["visible_test_command"]),
            hidden_test_command=str(raw["hidden_test_command"]),
        )
        task.validate()
        return task


@dataclass(frozen=True)
class BenchmarkPlan:
    benchmark_id: str
    claim: str
    source: str
    dataset_revision: str
    minimum_tasks: int
    repetitions: int
    seeds: tuple[int, ...]
    variants: tuple[str, ...]
    tasks: tuple[BenchmarkTask, ...]
    status: str
    evaluator_requirements: tuple[str, ...]

    def validate(self, *, require_tasks: bool = False) -> None:
        if not self.benchmark_id or not self.claim or not self.source or not self.dataset_revision:
            raise ProtocolError("benchmark identity, claim, source, and dataset revision are required")
        if self.minimum_tasks < 1 or self.repetitions < 1 or not self.seeds:
            raise ProtocolError("minimum task count, repetitions, and seeds must be positive")
        if len(set(self.variants)) < 2 or "single_agent" not in self.variants:
            raise ProtocolError("the plan must contain a single-agent control and at least one treatment")
        if require_tasks and len(self.tasks) < self.minimum_tasks:
            raise ProtocolError(
                f"external run needs {self.minimum_tasks} pinned tasks; manifest contains {len(self.tasks)}"
            )
        if self.status not in {"protocol_only", "ready", "complete"}:
            raise ProtocolError(f"unsupported benchmark status: {self.status}")
        for task in self.tasks:
            task.validate()
        if len({task.task_id for task in self.tasks}) != len(self.tasks):
            raise ProtocolError("task IDs must be unique")
        if not self.evaluator_requirements:
            raise ProtocolError("independent evaluator requirements must be documented")


def load_plan(path: str | Path) -> BenchmarkPlan:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    plan = BenchmarkPlan(
        benchmark_id=str(raw["benchmark_id"]),
        claim=str(raw["claim"]),
        source=str(raw["source"]),
        dataset_revision=str(raw["dataset_revision"]),
        minimum_tasks=int(raw["minimum_tasks"]),
        repetitions=int(raw["repetitions"]),
        seeds=tuple(int(seed) for seed in raw["seeds"]),
        variants=tuple(str(variant) for variant in raw["variants"]),
        tasks=tuple(BenchmarkTask.from_dict(task) for task in raw.get("tasks", [])),
        status=str(raw.get("status", "protocol_only")),
        evaluator_requirements=tuple(str(item) for item in raw["evaluator_requirements"]),
    )
    plan.validate()
    return plan

