# Success-endpoint prediction: frozen first-experiment protocol

The broader research goal is to predict tokens required to complete a task successfully. This first experiment operationalizes a narrow observable target: recorded actor-token usage through the endpoint of a source-scored successful run.

Protocol for [GitHub issue #15](https://github.com/shuo19mo/prediciton-token/issues/15). Code and data-preparation version: [`480e548f340f12d854064bbf8208d90b008893ef`](https://github.com/shuo19mo/prediciton-token/commit/480e548f340f12d854064bbf8208d90b008893ef). The [#14 Astra acceptance](https://github.com/shuo19mo/prediciton-token/issues/14#issuecomment-5901809512) is a data-admission PASS only. Package state remains `review_ready / training_approved=false` until the mentor actually confirms the target, package fingerprints, allowed inputs, hidden test truth, protocol, and runtime environment.

## Target and scope

Predict `actor_total_tokens_observed`: actor-token usage recorded through the endpoint of a run the source benchmark evaluator marks successful. A label is eligible only when the source-scored success is explicit, the recorded actor usage is complete and positive, task and configuration links are reliable, the initial prompt is verified, there are no recorded quality flags, and the source archive matches the frozen manifest's byte count and SHA-256. These are the unchanged #14 eligibility rules at [`480e548`](https://github.com/shuo19mo/prediciton-token/commit/480e548f340f12d854064bbf8208d90b008893ef); see [the accepted data-readiness evidence](https://github.com/shuo19mo/prediciton-token/issues/14#issuecomment-5901809512). This is observed successful-run cost. It is not a minimum sufficient budget, a guarantee of success, or the latent cost of continuing a failed run. Failures and unknown outcomes remain source facts, but are not labels and are not treated as censored observations.

Use ScienceAgentBench and the existing family-group outer fold 0. There are 102 eligible training labels across 43 tasks and 19 families; all 102 are used for preprocessing and final fit. The trainer receives 186 feature-only evaluation rows. The evaluator privately holds 32 eligible success labels across 13 tasks and six families; the other 154 evaluation rows are unlabeled for this target. Six configurations occur on both sides, and no task or family crosses the outer split. The three supplied inner family splits are retained in the handoff, but are not used in this experiment. This is one fixed fold with 13 eligible evaluation tasks and prior development exposure; it does not establish new-family, benchmark, or agent generalization.

The controlled `trainer_release` consists of exactly six files: `README.md`, `feature_whitelist.json`, `train_features.jsonl`, `train_labels.jsonl`, `test_features.jsonl`, and `validation_splits.json`. Do not expose its parent directory, `evaluator_private`, raw archives, or full facts to the training environment. Keep the controlled package outside Git and do not upload it to the public issue.

## Allowed inputs and preprocessing

Allowed features are verified initial system/user task text, deterministic Unicode character count, `model`, `scaffold`, `reasoning_effort`, and recorded limits `max_tokens_per_call` and `max_steps`. `episode_id` is linkage only. `config_id` is used only for the configuration-median baseline and is not included in either regression.

Exclude success/result, observed token fields, stop reason, call count, later messages, agent output, evaluator content, reference answers, task/family identifiers, and every diagnostic derived after the run. Test text must not influence vocabulary, imputation, scaling, feature selection, or model choice.

- Numeric fields: `task_text_chars`, `max_tokens_per_call`, `max_steps`. Drop any numeric feature that is entirely missing in training; `max_steps` is all missing in this package and must be dropped rather than filled with a fabricated default. Impute other missing numeric values with training medians. Add missingness indicators for numeric columns that have training missingness. Fit scaling statistics on training data only; do not center the combined sparse matrix.
- Categorical fields: `model`, `scaffold`, `reasoning_effort`. Replace null with the fixed category `__MISSING__`; fit one-hot encoding on training only and ignore unknown test categories.
- Record Python and dependency versions, preprocessing implementation, and reproducible command before training.

## Three fixed models

No parameter search, model selection, fold selection, or test-driven changes are allowed.

1. **Configuration median:** median eligible training token label for each `config_id`; fall back to the overall eligible-training median if that configuration has no training label.
2. **Metadata Ridge:** allowed numeric and categorical metadata, including character count, with Ridge `alpha=1.0`, `fit_intercept=True`, `solver="lsqr"`, and `tol=1e-6`. Predict raw token counts.
3. **TF-IDF plus metadata Ridge:** model 2 plus task-text `TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000, lowercase=True, sublinear_tf=True)`. Other vectorizer defaults are bound to the recorded library version. Use the same Ridge parameters as model 2 and predict raw token counts.

Clip negative predictions from both Ridge models to zero. Do not transform the target with log, tune parameters, or add models. Resolve an implementation defect before viewing any outer labels or scores, record the correction, and freeze implementation and predictions before evaluation.

## Predictions and independent evaluation

Return three prediction files, one per model. Each must contain exactly one row for every one of the 186 `test_features` episode IDs, with no missing or extra IDs and no duplicates. Values must be finite and nonnegative. Return implementation/version details, dependency versions, command, package fingerprints, preprocessing/parameter record, execution status, and any repair history. Freeze hashes of the implementation and all predictions before the evaluator reads private labels.

Evaluate the fixed 32 eligible labels without changing eligibility based on predictions:

- Primary: task-equal token MAE, first averaging absolute error within each task, then averaging over the 13 eligible tasks.
- Auxiliary: task-equal mean absolute difference on `log1p(tokens)`.
- Report paired task-level loss differences for the text model against each baseline; a negative difference favors the text model.
- Descriptive 95% family-cluster bootstrap: seed 17; 2,000 resamples, drawing six families with replacement from the six observed families. Keep every eligible task in each sampled family and preserve multiplicity; compute the paired difference with tasks equally weighted. Report the 2.5th and 97.5th percentiles. With only six families, this interval describes uncertainty; it is not a significance or contribution gate.
- Report configuration support. Suppress any public cost/error cell with fewer than five distinct eligible tasks. Keep row-level predictions and truths private.

Do not tune against the outer fold, alter the split, or change metrics after seeing results. State the single-fold design, success-conditioned population, 13-task support, and prior development exposure. Do not describe the test as entirely unseen or untouched.

## Roles, acceptance, and limits

The mentor must genuinely confirm the target, package fingerprints, allowed data visibility, hidden test truth, protocol, and runtime before training. The mentor implements/trains/tunes. Luna checks the handoff interface and independently evaluates frozen predictions without training. Astra independently accepts the evidence and plans the next step. The primary agent manages GitHub and versions. A data-readiness PASS does not stand in for mentor confirmation.

Acceptance requires the real mentor confirmation, three fixed model implementations, complete frozen predictions, a format/interface check, independent reproduction of the fixed evaluation, and Astra's independent review. The text model need not win: a correctly executed negative or uncertain result is informative. Passing this experiment does not by itself establish a novel or useful contribution.

Keep `evaluator_private`, the trainer package, raw facts, row-level predictions, task text, vocabulary, and reference material outside Git and public issue comments. Publish only protocol, safe evaluation code, aggregate results, fingerprints, and limitations. Do not execute trace contents, generate trajectories, rerun the original benchmark evaluator, or draft a paper as part of this protocol. Independent evaluation of the three frozen model predictions is required.
