"""Verifier-gated orchestra runtime over a resettable task sandbox."""
from __future__ import annotations

import time

from .ledger import Ledger
from .memory import EvidenceMemory
from .router import AdaptiveRouter
from .schema import AgentSpec, Budget, RunResult, TaskSpec, TypedMessage
from .verifier import VerificationError, Verifier


class OrchestraRuntime:
    def __init__(self, sandbox, *, adaptive: bool = True, budget: Budget | None = None) -> None:
        self.sandbox = sandbox
        self.budget = budget or Budget()
        self.ledger = Ledger()
        self.memory = EvidenceMemory()
        self.verifier = Verifier()
        agents = (
            AgentSpec("planner", "planner", ("decompose",), 0.08, 120, ("read_task",)),
            AgentSpec("retriever", "retriever", ("retrieve",), 0.06, 100, ("read_task",)),
            AgentSpec("implementer", "implementer", ("patch",), 0.18, 240, ("read_task", "write_patch"), 0.95),
            AgentSpec("tester", "tester", ("test",), 0.10, 180, ("read_task", "run_tests"), 0.98),
            AgentSpec("reviewer", "reviewer", ("review",), 0.09, 160, ("read_task", "run_tests"), 0.97),
        )
        self.router = AdaptiveRouter(agents) if adaptive else None
        self.agents = {agent.role: agent for agent in agents}

    def _message(self, task: TaskSpec, agent: AgentSpec, claim: str, evidence: tuple[str, ...], action: str) -> TypedMessage:
        message = TypedMessage(task.task_id, None, agent.agent_id, claim, evidence, 0.95, action, int(time.time()) + 3600)
        self.verifier.validate_message(message, task, int(time.time()))
        self.ledger.record_message(message)
        return message

    def run(self, task: TaskSpec) -> RunResult:
        task.validate_dag()
        self.sandbox.reset(task)
        state: dict[str, object] = {}
        safety = 0
        calls = 0
        tokens = 0
        cost = 0.0
        start = time.monotonic()
        failure: str | None = None
        for role, action in (("planner", "decompose"), ("retriever", "retrieve"), ("implementer", "patch"), ("tester", "test"), ("reviewer", "review")):
            agent = self.router.choose(role, self.budget, self.budget.call_limit - calls) if self.router else self.agents[role]
            if agent is None:
                failure = "routing_budget_exhausted"
                self.ledger.append("decision", task.task_id, "stop", {"role": role, "reason": failure})
                break
            tool = "write_patch" if role == "implementer" else ("run_tests" if role in {"tester", "reviewer"} else "read_task")
            try:
                self.verifier.authorize(agent, tool, self.budget, calls)
                observation = self.sandbox.execute(task, role, action)
                calls += 1
                tokens += int(observation.get("tokens", 100))
                cost += agent.cost
                safety += int(observation.get("safety_violations", 0))
                state.update(observation.get("state", {}))
                evidence = tuple(observation.get("evidence_ids", (f"{role}:observation",)))
                self._message(task, agent, str(observation.get("claim", f"{role} completed")), evidence, action)
                for evidence_id in evidence:
                    self.memory.add(str(observation.get("claim", role)), evidence_id, scope=role)
                if self.router:
                    self.router.update(agent.agent_id, bool(observation.get("state", {}).get("tests_passed")), agent.cost, agent.latency_ms, safety > 0)
            except (VerificationError, ValueError) as error:
                safety += 1
                failure = type(error).__name__
                self.ledger.append("decision", task.task_id, "rollback_and_freeze", {"role": role, "error": str(error)})
                break
            if tokens > self.budget.token_limit:
                failure = "token_budget_exhausted"
                break
        success, acceptance_failure = self.verifier.accept(task, state, safety)
        failure = failure or acceptance_failure
        self.ledger.append("evaluation", task.task_id, "success" if success else "failure", {"state": state, "failure": failure})
        return RunResult(task.task_id, success, safety, calls, tokens, cost, int((time.monotonic() - start) * 1000), failure, self.ledger.last_hash)
