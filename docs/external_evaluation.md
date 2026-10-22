# External Evaluation and Reproduction

This document defines how someone other than the author can verify the
Orchestra claim. The goal is independent custody of the acceptance tests and
independent execution, not a second reading of the README.

## Roles and Custody

The author publishes the code, public task manifest, configuration schema,
analysis script, and a lock file containing source and evaluator digests. An
independent evaluator keeps the hidden tests, expected outcomes, and model
credentials outside the public repository. The evaluator must not give the
agent access to hidden test files, gold patches, or labels during a run.

The evaluator records the repository commit, manifest digest, evaluator
package digest, model identifier, and execution environment before starting.
Changing any of these values creates a new evaluation, not a continuation of
the old one.

## Clean-room Procedure

1. Clone the repository at the declared commit in a fresh environment.
2. Install only the locked dependencies and verify the published file hashes.
3. Download or materialize each pinned repository snapshot in a disposable
   worktree. Check that its commit SHA matches the manifest.
4. Inject the evaluator-owned hidden tests through the evaluator process, never
   into the agent-visible worktree or prompt.
5. Run the registered variants, seeds, budgets, and failure-injection cases.
6. Export one JSON record and one hash-chained ledger per run. Keep failed and
   timed-out runs; do not rerun selectively after seeing outcomes.
7. Run the preregistered analysis script on the complete set of records.
8. Publish the signed summary, raw-record digest, and any deviations from the
   protocol.

The evaluator may publish aggregate results and per-task status, but should
withhold hidden test contents and gold patches until the evaluation window is
closed. A second evaluator should be able to repeat the process from the same
commit without author assistance.

## Required Independent Checks

The evaluator must verify all of the following:

- the three variants use the same model snapshot, permissions, and budgets;
- every task starts from the same pinned commit and a clean worktree;
- hidden tests are not readable through the agent tools or messages;
- safety violations cause a failed run even if the patch passes tests;
- the ledger chain verifies from `GENESIS` through the evaluation event;
- the analysis output is generated from raw records, not hand-entered values;
- the reported confidence intervals and exclusions match the preregistered
  analysis code.

## Reproduction Result Classes

Report one of these explicit outcomes:

- `REPRODUCED`: all registered checks pass and the primary interval supports
  the claim;
- `MECHANISM_ONLY`: implementation and safety checks pass, but the primary
  capability comparison is not run or is inconclusive;
- `FAILED_REPRODUCTION`: a protocol, custody, hash, or safety check fails.

Do not convert `MECHANISM_ONLY` into a capability claim. A failed or
inconclusive result is still useful evidence when the raw records and cause
are preserved.

## What Counts as External Evidence

An outside person merely viewing the GitHub repository is not an experiment.
External evidence requires a clean-clone run by an independent evaluator with
custody of hidden acceptance tests and a report that includes the commit,
manifest, evaluator digest, raw-record digest, and deviations. A second
independent reproduction strengthens the claim but cannot be replaced by more
fixture examples.
