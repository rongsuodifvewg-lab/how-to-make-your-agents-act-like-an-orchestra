# Orchestra Design

## Controlled Object

The optimized object is the orchestrator policy. At each step it observes the
current task node, evidence, previous failures, and remaining resource budget.
It can decompose, route, retrieve, request verification, or stop. Child agents
cannot change permissions, acceptance tests, or the evaluator.

## Communication

Agents exchange typed claims rather than opaque transcripts:

```text
task_id, parent_task_id, agent_id, claim, evidence_ids,
confidence, next_action, expires_at, message_id
```

The ledger records each message and chains it to the prior event hash.

## Routing

`AdaptiveRouter` uses an interpretable UCB score:

```text
mean_reward
+ exploration * sqrt(log(total_pulls + 1) / max(1, pulls))
+ reliability_bias
```

Reward includes verified success, cost, latency, and a hard safety penalty.
The router is offline and bounded; it cannot self-modify permissions or tests.

## Evidence Standard

The fixture establishes reset semantics, typed communication, budget gating,
permission checks, hidden acceptance state, and reproducible traces. A real
claim requires independent hidden tasks, paired baselines, task-family clustered
intervals, full raw traces, and an external evaluator.
