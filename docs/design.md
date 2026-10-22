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

## Confirmatory Evaluation Protocol

The confirmatory claim is deliberately narrow: under the same model, tools, and
resource budget, adaptive orchestration should improve hidden-test success or
reduce cost at the same success rate on repository maintenance tasks. The
protocol in `benchmarks/protocol.json` requires at least 30 immutable tasks,
three seeds, and the three variants `single_agent`, `fixed_orchestra`, and
`adaptive_orchestra`.

Each task record pins a repository URL and base commit, keeps visible and hidden
test commands separate, and supplies the task statement without the hidden
acceptance implementation. An evaluator adapter is run in a clean workspace;
the runner passes only a task-record path and experiment metadata. It validates
the adapter's metric schema and rejects missing, negative, or non-finite values.

The analysis is paired by task and seed. `evals/statistics.py` reports success
and cost deltas with deterministic percentile bootstrap intervals. A result is
not considered confirmatory if runs are unpaired, safety violations increase,
or the independent evaluator cannot reproduce the raw traces. The checked-in
status is currently `PENDING_EXTERNAL_RUN`; this is an explicit evidence state,
not a performance result.
