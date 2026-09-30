# Data readiness for success-endpoint experiment

Date: 2026-09-29. This is a support and packaging report for issue #14, not a training result or a claim that the scientific question is settled.

## Frozen evidence and source check

The source audit used the read-only project history at commit `058f351eb6ed4f5819aacba2ab8fbdc371a57a18`. The research manifest is `configs/hal_research_manifest.json` (SHA-256 `d66db6fb76bfe5bb5e5e2aca1902944d6e1ce1b32b071d4e20b88db97d373842`). All six ScienceAgentBench archives were checked against manifest byte counts and SHA-256. The nine frozen derived files match `protocol_summary.json`; their data fingerprint is `ca3e0e65865b4b7cf8198bddfcf3078822c7e9a91f426827b36d88cd5876bf68`. The linked `initial_inputs.internal.jsonl` SHA-256 is `5efcbe3385119666dd3263e67205914c1967ee24163289d82a873b3118fcdf9b`.

For source-call provenance, the documented reader is `research_plan/src/haldata.py` (Git blob `04074105ebcf1fc0c770cfd773c0b3f3ec088f16` at the fixed history), and the source-selection/duplicate and initial-input rules are `tools/hal_pipeline.py` (Git blob `44bf33bc6af308050f4854c343e2b336a33c53e2`, identical to the local file). In-memory rechecking confirmed the source-call ID, first retained actor-primary ordering, initial status, allowed roles, and exact extracted text for 612/612 ScienceAgentBench records. No prompt text was emitted in reports or logs. This evidence establishes consistency with the visible archive stream; it does not rule out interactions missing from that stream.

## Cohort and support

ScienceAgentBench contributes 612 recorded runs, 134 source-scored successes, 56 successful task groups, and six configurations. Applying the issue's success-only criteria yields all 134 as eligible observed labels: 102 training labels (43 task groups; 19 family groups) and 32 held-out labels (13 task groups; six family groups). The fixed family fold 0 also carries 186 unlabeled/feature-only held-out rows across 31 task groups and six family groups. All six configurations are represented in both outer partitions. The task-only split was not selected because it has cross-partition family overlap; fold 0 of the pre-existing family split has no task or family overlap.

The current package is a **review-ready candidate**, not permission to train. The trainer directory contains 102 training labels and 102 matching feature rows, 186 test-feature rows without target/outcome fields, and three filtered inner family splits. Its sibling evaluator directory holds the 186 held-out facts, with only the 32 eligible success labels populated; the other held-out targets are null. File hashes and separation are recorded in the private package manifest in the controlled output location.

## Scope and limitations

Only ScienceAgentBench is prepared for this initial pass. Other benchmarks are not silently pooled: their previously recorded input visibility, usage completeness, and support differ, and they were not included in the source-call recheck for this package. The supported estimand is conditional on a recorded successful run with complete logged actor usage and verified observed initial input. It says nothing about failed-run potential success costs, missing actor usage, or unlogged calls. One fixed family fold and 13 eligible held-out task groups provide a narrow first evaluation; small support limits uncertainty and generalization claims. Existing development exposure also remains a source-level limitation.

No agent run, benchmark judgment, trace execution, model fitting, training, or new trajectory generation was performed. No raw trace, task text, token label, or answer is committed. Public aggregate support is in `reports/success_endpoint/aggregate.json`; sensitive row-level material remains only in the out-of-repository controlled package.
