# Success-endpoint prediction: first fixed-fold protocol

Version: 2026-09-29. Status: **review-ready candidate; training is not approved**.

This handoff defines a first observable target: for a recorded run whose source evaluator reports success, predict its recorded actor-token total from information available at the verified initial actor call. The label is `actor_total_tokens_observed`; it is not a latent cost of a failed run, a censoring estimate, or a claim about every possible execution. Only source-scored successes with a positive complete logged actor total, no recorded quality flags, a linked configuration and task, a verified initial prompt, and a source archive whose size and SHA-256 match the frozen manifest enter the label set. Failure, unknown outcome, incomplete usage, and unresolved input/quality cases remain facts but are not labels.

## Fixed cohort and split

Use ScienceAgentBench only for this first pass. The frozen source has 612 recorded runs, including 134 source-scored successes across 56 task groups and six configurations. The existing family-group outer fold 0 is fixed: eligible training labels comprise 102 successful runs across 43 task groups and 19 family groups; the held-out side has 186 feature rows, of which 32 successful labels span 13 task groups and six family groups. The other 154 held-out rows remain unlabeled for this target. Six configurations occur on both sides. All test rows stay grouped by task and family; no task or family group crosses the outer split. Existing inner family splits are supplied for development only. Do not choose a fold or seed by model score.

This is a within-benchmark, within-supported-configuration evaluation. It is not a claim of new-task-family, benchmark, or agent generalization. The source records have prior development exposure. The held-out task/family groups reduce observed split overlap but do not erase that historical exposure.

## Inputs and exclusions

Permitted initial inputs are the verified system/user text at the first actor-primary call, its Unicode character count, configuration metadata (`model`, `scaffold`, `reasoning_effort`), and recorded limits (`max_tokens_per_call`, `max_steps`). Exclude the success/result, observed token fields, stop reason, call count, later messages, agent output, evaluator content, reference answers, task/family group identifiers, and any diagnostic derived after the run. The handoff feature file retains `episode_id` and `config_id` only for linkage and configuration-conditional baselines; task and family grouping is kept outside trainer features.

Initial text was rechecked in memory against all six ScienceAgentBench source archives using the documented read-only reader and the fixed extractor's duplicate-call and initial-input rules. The selected call ID, observed-initial status, absence of assistant/tool/function history, and extracted system/user text matched all 612 frozen rows. This confirms equality to the earliest retained actor-primary input visible in these archives; it cannot establish that no unlogged or out-of-archive interaction occurred.

## Predeclared baselines and scoring

Use three deterministic baselines, with no test-driven selection or hyperparameter search:

1. **Configuration median:** median of eligible training labels for that `config_id`; use the overall eligible-training median only if a configuration has no eligible training label.
2. **Metadata ridge:** Ridge regression with `alpha=1.0` over Unicode character count, one-hot model/scaffold/reasoning-effort, and numeric recorded limits. Fit all imputers, category vocabularies, and scaling on training rows only; ignore unknown categories at prediction time.
3. **Text-plus-metadata ridge:** word-level text representation via `TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20_000, lowercase=True, sublinear_tf=True)` plus the same metadata; Ridge `alpha=1.0`. Fit vocabulary and preprocessing on training rows only. Clip negative token predictions to zero.

Primary metric: task-equal MAE, computed by averaging absolute errors within each task group and then averaging across eligible test task groups. Auxiliary metric: task-equal mean absolute error on `log1p(tokens)`. Show task-group paired loss differences and a descriptive 95% cluster bootstrap interval from 2,000 resamples of test task groups with seed 17. This interval is descriptive with only 13 eligible held-out task groups; it is not a significance gate. Any optional per-configuration cost summary must suppress cells with fewer than five distinct eligible task groups. Do not tune on the outer test fold.

## Physical release boundary

`trainer_release` contains eligible training features and labels, unlabeled test features, and the fixed inner split IDs. `evaluator_private` is a separate sibling directory containing the held-out source facts and only eligible success labels; ineligible held-out target values are null. The preparation manifest fingerprints both private packages. Keep both directories outside Git and do not merge their contents. `review_ready` means packaging checks completed; it is not mentor approval, training authorization, or an M2 pass. No training, scoring, or model fitting was run for this handoff.

The preparation script rechecks frozen derived-file hashes, source archive byte counts and SHA-256, one-to-one identity/text linkage, source-call provenance, split grouping, and trainer/evaluator isolation. It reads trace payloads only through the documented archive reader; it does not execute trace code or save raw archives/messages into the package.
