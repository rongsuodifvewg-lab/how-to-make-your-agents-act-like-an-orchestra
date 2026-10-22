# How to Make Your Agents Act Like an Orchestra

Verifier-gated adaptive multi-agent orchestration under fixed budgets.

The project asks one falsifiable question: **can an orchestrator decide when to
decompose a task, which agents to call, what evidence to pass, and when to stop,
while staying inside fixed token, cost, latency, and safety constraints?**

The system is intentionally narrower than a collection of prompt tricks. It
studies the orchestrator policy as the controlled object.

## Architecture

- `TaskSpec` and `TaskNode` define a typed task DAG with dependencies, tools, and
  acceptance conditions.
- `TypedMessage` forces every claim to carry evidence IDs, confidence, next
  action, and an expiration time.
- `AdaptiveRouter` uses an interpretable UCB policy behind hard budget and
  permission gates.
- `EvidenceMemory` performs budgeted retrieval and records provenance.
- `Verifier` rejects expired claims, missing evidence, unauthorized tools, and
  failed acceptance state.
- `Ledger` stores an append-only hash chain for replay and audit.
- `FixtureSandbox` resets each run and keeps the expected patch hidden from the
  agents; only verifier state exposes whether acceptance tests pass.

## Run

```powershell
python -m unittest discover -s tests -q
python scripts/run_experiment.py
python scripts/validate_project.py
```

The fixture experiment compares a fixed role sequence with the adaptive router.
It is a mechanism demonstration, not evidence of real repository-level FDE
improvement.

## Claim Boundary

`MECHANISM_READY_EXTERNAL_BENCHMARK_PENDING`.

A confirmatory capability claim requires a real benchmark with pinned repository tasks, hidden
acceptance tests, independent custody, raw call and cost traces, pre-registered
baselines, and an evaluator that cannot see the hidden tests. Historical traces
can initialize the policy but cannot serve as counterfactual evidence.

## Repository Map

| Layer | Artifact |
|---|---|
| Typed state and messages | `orchestra/schema.py` |
| Adaptive routing | `orchestra/router.py` |
| Evidence memory | `orchestra/memory.py` |
| Verification gates | `orchestra/verifier.py` |
| Audit ledger | `orchestra/ledger.py` |
| Runtime | `orchestra/runtime.py` |
| Resettable fixture | `sandbox/fixture.py` |
| Paired evaluation | `evals/runner.py` |
| Release validation | `scripts/validate_project.py` |
