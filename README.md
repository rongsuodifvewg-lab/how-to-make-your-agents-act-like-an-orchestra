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
python scripts/check_benchmark_protocol.py
python scripts/analyze_benchmark.py
```

The fixture experiment compares a fixed role sequence with the adaptive router.
It is a mechanism demonstration, not evidence of real repository-level FDE
improvement.

## Evidence Package

The repository now contains a model-provider-independent protocol for a real
repository benchmark:

- `benchmarks/protocol.json` fixes the claim, controls, seeds, repetitions,
  minimum task count, and independent-evaluator requirements.
- `benchmarks/real_manifest.json` pins 30 public SWE-bench Lite task records,
  including issue text and base commits; it contains no gold patches or hidden
  test implementations.
- `benchmarks/schema.py` rejects unpinned commits, duplicate tasks, missing
  hidden-test commands, and incomplete control groups.
- `evals/benchmark.py` runs a supplied evaluator adapter with identical
  environment variables for every variant and records raw metrics.
- `evals/statistics.py` computes paired deltas and deterministic bootstrap
  intervals, failing closed when runs are not paired.
- `benchmarks/ablation_matrix.json` fixes the component removals that must be
  run against the full adaptive variant.
- `scripts/analyze_benchmark.py` generates comparisons directly from raw JSON;
  it cannot turn a pending or incomplete run into a capability claim.
- `scripts/run_external_benchmark.py` is the entry point for a populated task
  manifest; it refuses to claim results when no real tasks are present.
- `reports/external_evaluation_status.json` records the current evidence state.

The intended comparison is `single_agent`, `fixed_orchestra`, and
`adaptive_orchestra`, using the same model, tools, budgets, seeds, and hidden
evaluator. The protocol requires at least 30 pinned repository tasks, three
seeds, raw traces, ablations, and an independent clean-checkout reproduction.

## Claim Boundary

`MECHANISM_READY_REAL_BENCHMARK_NOT_RUN`.

The current fixture proves protocol mechanics only. A capability claim remains
blocked until the external task manifest is pinned, all three variants are run,
paired confidence intervals and component ablations are reported, and an
independent evaluator reproduces the result. Historical traces can initialize
the policy but cannot serve as counterfactual evidence.

The checked-in manifest is from Hugging Face dataset revision
`6ec7bb89b9342f664a54a6e0a6ea6501d3437cc2`; its SHA-256 is recorded in
`reports/external_evaluation_status.json`. The current status is
`PENDING_EXTERNAL_RUN`, because no evaluator-owned model adapter or hidden-test
custody was available in this execution environment.

To run a real evaluation after supplying the pinned task manifest and adapter:

```powershell
python scripts/run_external_benchmark.py --manifest benchmarks/real_manifest.json --adapter python adapters/run_agent.py
```

The adapter must read `ORCHESTRA_TASK_FILE`, use `ORCHESTRA_VARIANT`,
`ORCHESTRA_SEED`, and `ORCHESTRA_REPETITION`, then print one JSON object with
`success`, `cost`, `latency_ms`, `calls`, `tokens`, and `safety_violations`.

To refresh the public task manifest at its recorded dataset revision:

```powershell
python scripts/fetch_swebench_manifest.py
```

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
| External benchmark contract | `benchmarks/` and `evals/benchmark.py` |
| Paired statistics | `evals/statistics.py` |
| Release validation | `scripts/validate_project.py` |
