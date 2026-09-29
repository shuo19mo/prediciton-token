# HAL stopping evidence audit (v2, 2026-09-29)

## Scope and result

This is a read-only evidence inventory of the frozen HAL historical records. It does not establish a censoring mechanism, identify a successful continuation for failed runs, or qualify rows for training. The analysis is deliberately limited to archived records and commit-pinned source inspection; no agents, benchmark code, evaluators, scorers, or training were run.

The index covers 1,197 existing runs across 17 frozen archives. Exact task-key joins were available for all 1,197 records. The protocol-B failure subset contains 603 rows (SAB 478, CORE 48, SWE 77; SciCode and TAU 0). These counts reproduce the existing derived cohort; they are not estimates of censoring validity.

## What the archives show

- The only direct top-level task-output markers found are two `TIMEOUT` prefixes and one `ERROR:` prefix across all runs; both timeout markers are in the B subset. These strings establish observed output markers only, not why a task stopped or whether continuation was possible.
- Raw call logs contain finish reasons (12,297 observed; 32 absent; four without an exact task-call join). A call-level `length`/finish reason is not a task-level stop event.
- Evaluator diagnostics and membership records were kept separate from agent output. In the B subset, the `log_info` field is present on 460 rows and empty on 18 (478 field observations total); all runs have 593 present and 19 empty (612 total). SWE result-membership fields were observed for 77 B-subset rows. Call `finish_reason` has 12,297 present, 32 absent and four uninspected observations overall. These are coverage counts, not termination or censoring findings. SciCode evaluator timeout configuration is not evidence that the agent itself timed out.
- The archives contain configured per-call token caps, dollar budgets and step limits, but no verified whole-run token cap. Configuration alone does not show that a limit activated.
- For TAU, 99 of 100 archived runs have a `taken_actions` list (min 4, median 16, max 40). Three counts exceed 30 (31, 34, 40), and three equal 30. Both candidate TAU dependency pins (`807e348…` and `bef42de…`) expose `solve(..., max_num_steps=30)` and `env.step` appends each action; the HAL wrapper does not pass an override. The two archives' `config` only records agent name, benchmark, date, run command/id and model arguments; it contains no installed extra or dependency commit. Thus the actual package pin cannot be identified from these archives. This is a source/configuration discrepancy to review, not evidence that the default activated or that any of these runs were right-censored; per-run source/runtime consistency and censoring remain unknown.
- All 1,197 rows remain `unknown` for each required identification condition: `T > U`, same continuation, first-success visibility, and conditional independent censoring. No row is approved for training.

These findings do not support treating every failed run as a valid right-censored observation. The current target “tokens needed for successful completion” remains a hypothesis whose label and identification conditions are unresolved.

## Historical source audit

The source registry in `configs/hal_stopping_sources.json` binds every expected HAL source version to the exact raw `git_info.repository_url` string and commit found in its archive. It preserves the archive URL verbatim; normalization is used only for links. The registry contains 12 observed repository+commit pairs and 24 source records. Twenty-one source records have commit-pinned Git blob IDs; five HAL source files additionally match local receipt SHA-256 and byte counts. No source version was left unregistered.

Source files actually read at commit-pinned revisions:

- SAB agent control flow at `science_agent.py` for commits `23fc566…`, `eb094b…` and `edfe626…` (write-program, step and solve paths); `edfe626…` was checked against the existing local receipt.
- HAL Generalist `main.py` at `bc575cd…`, `8a0e293…` and `6a44aed…` (budget callback / step-limit paths).
- CORE `main.py` at `c7354eb…` and `7e56e66…` (budget and max-step paths).
- SciCode agent `main.py` and evaluator `hal/benchmarks/scicode.py` at `0ac45fa…`; evaluator timeout is specifically classified as evaluation-side.
- HAL TAU wrapper and `pyproject.toml` at `b64fc7c…`, plus both candidate TAU dependency versions `807e348…` and `bef42de…`, whose `tau_bench/agents/tool_calling_agent.py` and `tau_bench/envs/base.py` files were read at each commit. The corresponding file Git blob IDs are identical across these two revisions.
- SWE parent `.gitmodules` at `02a2500…` and `85513db…`, the corresponding parent gitlinks (`94f540c…` and `d872eb7…`), and the pinned SWE-agent `agents.py` and cost-limit configuration files at those submodule commits.

The source registry is not a claim that every source file was independently byte-verified. Exact historical bytes were verified only where the existing local receipt matched. For other source files, the immutable Git blob ID and commit-pinned URL are recorded, but raw-byte SHA-256 remains null because this pass did not acquire raw bytes. The TAU dependency pin is recorded as two candidates with separate commit URLs and blob IDs: `pyproject.toml` contains multiple pins and archive metadata does not resolve which extra was installed for each run. Runtime package resolution remains unknown. Likewise, a parent gitlink identifies the SWE-agent commit but does not itself establish the runtime checkout or execution path.

The registry captures source-level stopping mechanisms and relevant line ranges for review. It does not prove a mechanism was activated in any particular archived run. In particular, configured CORE step ceilings, evaluator timeout values and source branches must not be promoted to run-level stopping facts without corresponding execution evidence.

## Private examples and reproducibility

Private, task-key-locatable examples (not included in Git) are written to the controlled `data/derived/stopping_audit/review_examples.internal.json`: explicit timeout output, evaluation diagnostics, runs whose stopping reason remains unknown, source versions without a local raw-byte receipt, and the three TAU action counts above the candidate default of 30. The TAU examples are candidate discrepancies only; runtime pin and stopping mechanism remain unknown. Task IDs and raw excerpts stay in the private index.

From the repository root, synthetic checks run with:

```sh
python3 -m unittest discover -s checks -p 'test_stopping_evidence.py' -v
```

The real read-only index requires the project’s existing HAL-derived inputs and the reviewed archive reader environment (including `cryptography`):

```sh
python3 tools/audit_stopping_evidence.py \
  --data-root "/path/to/controlled-project" \
  --source-index configs/hal_stopping_sources.json \
  --private-output "/path/to/controlled-project/data/derived/stopping_audit" \
  --public-output reports/research_audit/stopping_evidence_summary.json
```

The real run must be performed only against the frozen local HAL records. The public JSON is aggregate-only; per-run facts, input paths, IDs and excerpts are private and ignored by Git. Passing these checks validates the indexing contract, not the scientific assumptions or contribution.
