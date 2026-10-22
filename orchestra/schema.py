"""Typed contracts for the orchestra project.

The runtime passes claims and evidence references instead of unstructured
agent-to-agent transcripts. All contracts are stdlib dataclasses so the
fixture is reproducible without a model SDK.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


def _finite(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


@dataclass(frozen=True)
class Budget:
    token_limit: int = 1800
    cost_limit: float = 1.0
    latency_limit_ms: int = 5000
    call_limit: int = 8
    depth_limit: int = 4

    def __post_init__(self) -> None:
        if self.token_limit <= 0 or self.cost_limit <= 0 or self.latency_limit_ms <= 0:
            raise ValueError("budget limits must be positive")
        if self.call_limit < 1 or self.depth_limit < 1:
            raise ValueError("call and depth limits must be positive")


@dataclass(frozen=True)
class TaskNode:
    node_id: str
    goal: str
    preconditions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    family: str
    description: str
    acceptance: tuple[str, ...]
    nodes: tuple[TaskNode, ...]
    snapshot_version: str
    hidden_case_id: str

    def validate_dag(self) -> None:
        ids = {node.node_id for node in self.nodes}
        if len(ids) != len(self.nodes):
            raise ValueError("task node IDs must be unique")
        for node in self.nodes:
            if node.node_id in node.depends_on or not set(node.depends_on) <= ids:
                raise ValueError("task DAG has invalid dependency")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ValueError("task DAG contains a cycle")
            if node_id in visited:
                return
            visiting.add(node_id)
            node = next(n for n in self.nodes if n.node_id == node_id)
            for parent in node.depends_on:
                visit(parent)
            visiting.remove(node_id)
            visited.add(node_id)

        for node in self.nodes:
            visit(node.node_id)


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    role: str
    capabilities: tuple[str, ...]
    cost: float
    latency_ms: int
    tool_permissions: tuple[str, ...]
    reliability: float = 1.0

    def __post_init__(self) -> None:
        if self.cost <= 0 or self.latency_ms <= 0 or not 0 < self.reliability <= 1:
            raise ValueError("invalid agent resource or reliability value")


@dataclass(frozen=True)
class TypedMessage:
    task_id: str
    parent_task_id: str | None
    agent_id: str
    claim: str
    evidence_ids: tuple[str, ...]
    confidence: float
    next_action: str
    expires_at: int
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def __post_init__(self) -> None:
        if not self.task_id or not self.agent_id or not self.claim:
            raise ValueError("message identity and claim are required")
        if not self.evidence_ids:
            raise ValueError("claims require at least one evidence reference")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")
        if self.expires_at <= 0:
            raise ValueError("message expiration must be positive")

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "agent_id": self.agent_id,
            "claim": self.claim,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "next_action": self.next_action,
            "expires_at": self.expires_at,
            "message_id": self.message_id,
        }


@dataclass(frozen=True)
class TraceEvent:
    event_type: str
    task_id: str
    decision: str
    payload: Mapping[str, Any]
    sequence: int
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    previous_hash: str = ""

    def digest(self) -> str:
        body = {
            "event_type": self.event_type,
            "task_id": self.task_id,
            "decision": self.decision,
            "payload": self.payload,
            "sequence": self.sequence,
            "timestamp_ms": self.timestamp_ms,
            "previous_hash": self.previous_hash,
        }
        return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class RunResult:
    task_id: str
    success: bool
    safety_violations: int
    calls: int
    tokens: int
    cost: float
    latency_ms: int
    failure_reason: str | None
    trace_hash: str

