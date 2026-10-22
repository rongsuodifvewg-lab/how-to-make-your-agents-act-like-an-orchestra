"""Safe, interpretable contextual routing under hard budgets."""
from __future__ import annotations

import math
from dataclasses import dataclass

from .schema import AgentSpec, Budget


@dataclass
class ArmStats:
    pulls: int = 0
    mean_reward: float = 0.0

    def update(self, reward: float) -> None:
        self.pulls += 1
        self.mean_reward += (reward - self.mean_reward) / self.pulls


class AdaptiveRouter:
    """Select an eligible role implementation using UCB plus safety gates."""

    def __init__(self, agents: tuple[AgentSpec, ...], exploration: float = 0.25) -> None:
        if exploration < 0:
            raise ValueError("exploration must be non-negative")
        self.agents = {agent.agent_id: agent for agent in agents}
        self.stats = {agent.agent_id: ArmStats() for agent in agents}
        self.exploration = float(exploration)

    def choose(self, role: str, budget: Budget, remaining_calls: int) -> AgentSpec | None:
        if remaining_calls <= 0:
            return None
        eligible = [
            agent for agent in self.agents.values()
            if agent.role == role
            and agent.cost <= budget.cost_limit
            and agent.latency_ms <= budget.latency_limit_ms
        ]
        if not eligible:
            return None
        total_pulls = sum(stat.pulls for stat in self.stats.values()) + 1

        def score(agent: AgentSpec) -> float:
            stat = self.stats[agent.agent_id]
            bonus = self.exploration * math.sqrt(math.log(total_pulls) / max(1, stat.pulls))
            return stat.mean_reward + bonus + 0.05 * agent.reliability

        return max(eligible, key=score)

    def update(self, agent_id: str, success: bool, cost: float, latency_ms: int, safety_violation: bool = False) -> float:
        if agent_id not in self.stats:
            raise KeyError(agent_id)
        reward = -10.0 if safety_violation else (1.0 if success else 0.0) - 0.1 * cost - 0.00001 * latency_ms
        self.stats[agent_id].update(reward)
        return reward
