# Experimental Protocol

This protocol turns the Orchestra prototype into a falsifiable capability
evaluation. It is deliberately narrow: the experiment evaluates one class of
software-maintenance tasks rather than making a claim about every agent task.

## Primary Claim

With the same model, tool permissions, and hard resource budget, an adaptive
Orchestra policy has a higher hidden-test task success rate than a single-agent
policy on repository-level maintenance tasks that require planning, patching,
and verification. If the success-rate difference is not positive, the
secondary claim is that Orchestra achieves the same success rate at lower
cost. A safety violation is a disqualifying regression regardless of task
success.

The deterministic fixture is a mechanism test. Its results must not be pooled
with this capability evaluation or used as evidence for the primary claim.

## Task Set and Unit of Analysis

Use one pinned public software-maintenance task set, such as a declared subset
of SWE-bench Lite or an equivalent set of GitHub issues. The repository must
record a manifest containing, for every task:

- task ID, repository URL, commit SHA, issue text, and license;
- the task family (bug fix, validation, serialization, retry, or similar);
- the exact setup command and timeout;
- the evaluator-owned hidden test command and expected exit status;
- a SHA-256 digest of the manifest and the evaluator package.

The initial confirmatory run must contain at least 30 tasks spanning at least
three task families. The unit of analysis is one `(task_id, seed, variant)`
run. Every task is reset to its pinned commit before each run; no worktree or
memory is shared between variants.

## Pre-registered Variants

Run these three variants for every task and seed:

1. `single_agent`: one agent receives the task and the same tool envelope.
2. `fixed_orchestra`: the fixed planner, retriever, implementer, tester, and
   reviewer sequence in this repository.
3. `adaptive_orchestra`: the Orchestra router, evidence memory, typed messages,
   verifier, budget manager, and ledger enabled.

Use the same model snapshot, system prompt, maximum context, tool permissions,
maximum calls, token budget, cost budget, latency timeout, and random seeds in
all three variants. The only independent variable is the orchestration policy.
Do not tune a variant on the confirmatory tasks. Any tuning must use a separate
development split and be recorded before the test split is opened.

## Measurements

The evaluator emits one immutable JSON record per run containing:

- `success`: hidden tests pass and the patch applies cleanly;
- `safety_violations`: unauthorized tool, evaluator access, or policy violation;
- `cost_usd`, `input_tokens`, `output_tokens`, `latency_ms`, and `agent_calls`;
- `retries`, `rollback_count`, and `communication_messages`;
- `failure_reason`, `trace_hash`, model ID, seed, task ID, and variant.

The primary metric is task success rate. Secondary metrics are paired cost and
latency among successful runs, call count, recovery rate after an injected
tool failure, and communication overhead. Report safety violations separately;
they must never be hidden inside an average score.

## Statistical Analysis

Before running the test split, register the task manifest, variants, seeds,
budgets, metrics, and analysis script. Use at least three seeds per task. For
each task, compute the paired success difference between `adaptive_orchestra`
and `single_agent`; aggregate with a task-clustered bootstrap (10,000
resamples, fixed analysis seed) and report the 95% confidence interval.

The claim is supported only if the lower bound of the primary success-rate
difference is above zero, the safety-violation rate is not higher, and the
raw per-task records are available. If the primary interval includes zero,
report the result as inconclusive. For the cost claim, compare only paired
successful runs and report the success-rate constraint alongside the cost
difference. Do not replace missing or timed-out runs with successes.

## Ablations

Run the same task and seed assignments with exactly one component disabled at
a time: adaptive routing, evidence memory, typed messages, verifier gates, and
the budget manager. The full adaptive variant is the reference. An ablation
result is meaningful only when its configuration, budget, and evaluator are
identical to the reference and its raw trace is retained.

## Failure Injection and Replay

At least one fixed task split must inject a denied tool, a malformed message,
and a transient test failure. The expected behavior is rollback and freeze,
with a ledger event containing the error type, task ID, sandbox version, and
previous hash. Replaying the same manifest, seed, and model snapshot must
reproduce the same decision sequence and trace hash, aside from explicitly
marked wall-clock telemetry.

## Evidence Boundary

Passing unit tests, a deterministic fixture, or a favorable average on a
public development split proves only that the implementation runs. A
capability claim requires the pinned real-task manifest, hidden evaluator,
paired baselines, pre-registered analysis, raw traces, and an independent
replication described in `docs/external_evaluation.md`.
