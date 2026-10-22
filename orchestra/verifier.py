"""Verifier gates for messages, permissions, budgets, and task completion."""
from __future__ import annotations

import math

from .schema import AgentSpec, Budget, TaskSpec, TypedMessage


class VerificationError(ValueError):
    pass


class Verifier:
    def validate_message(self, message: TypedMessage, task: TaskSpec, now: int) -> None:
        if message.task_id != task.task_id or message.expires_at < now:
            raise VerificationError("message task or expiration mismatch")
        if not message.evidence_ids:
            raise VerificationError("claims require evidence references")
        if not math.isfinite(message.confidence):
            raise VerificationError("confidence must be finite")

    def authorize(self, agent: AgentSpec, tool: str, budget: Budget, calls: int) -> None:
        if tool not in agent.tool_permissions:
            raise VerificationError("tool permission denied")
        if calls >= budget.call_limit:
            raise VerificationError("call budget exceeded")

    def accept(self, task: TaskSpec, state: dict[str, object], safety_violations: int) -> tuple[bool, str | None]:
        if safety_violations:
            return False, "safety_violation"
        if state.get("tests_passed") is not True:
            return False, "hidden_acceptance_failed"
        if not state.get("patch_applied"):
            return False, "no_patch"
        return True, None
