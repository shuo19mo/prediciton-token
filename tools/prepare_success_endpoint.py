#!/usr/bin/env python3
"""Prepare a review-only success-endpoint package from frozen HAL records.

This script reads frozen derived records and verifies source archive fingerprints;
it never executes trace content, decrypts archives, trains models, or writes to
the source tree. Private package output must be outside this repository.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path


FROZEN = {
    "runs.jsonl": "0117bf11dce813db1c800a1d539d22fabdee073f2f02abf18eb4f865455cbc37",
    "label_candidates.jsonl": "65062d1fc02fc357a3bfd562e13ce4eed0bffe3e57f51ecb487765f677c793f4",
    "features.internal.jsonl": "7acb5c9fa795d7b93266b37a6283ad2ec1b65f6903d9b44a7294e99f711a9339",
    "agent_configs.json": "fdc8cc38699e2eff00d58706ec9f02145c69648440941b6b1f177dc37445f8a7",
    "feature_whitelist.json": "e91289626aa368490c9a295b087879afc1d37513a41fd176e7d86f9248885cda",
    "split_manifest.json": "ae9f86fe1ce7ede0cdab8658ca3c942f185ab5871528ef0d46aaf649f7e1f8df",
    "groups.csv": "e574ad76c62a74c7a4299c4da596b3ec69262afa2183ddb7d71d2df5c8c9384b",
    "generalization_splits.json": "da0bf63cc695c626becce489435c82b5681f865058fdb7c187423e28475e0426",
    "family_map_provenance.json": "efcbad08e2e0a387fe7949f71c35572e9edc633cada7e647039ca57ec2a03ef6",
}
SOURCE_MANIFEST_SHA256 = "d66db6fb76bfe5bb5e5e2aca1902944d6e1ce1b32b071d4e20b88db97d373842"
INITIAL_INPUTS_SHA256 = "5efcbe3385119666dd3263e67205914c1967ee24163289d82a873b3118fcdf9b"
HAL_PIPELINE_GIT_BLOB = "44bf33bc6af308050f4854c343e2b336a33c53e2"
HALDATA_GIT_BLOB = "04074105ebcf1fc0c770cfd773c0b3f3ec088f16"
ALLOWED_FEATURES = ("task_text", "task_text_chars", "scaffold", "model",
                    "reasoning_effort", "max_tokens_per_call", "max_steps")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def qualify_run(run: dict, initial: dict, feature: dict, config: dict,
                archive_hashes: set[str]) -> list[str]:
    reasons: list[str] = []
    if run.get("success") is not True or run.get("outcome_status") != "scored":
        reasons.append("not_source_success")
    usage = run.get("actor_total_tokens_observed")
    if not isinstance(usage, int) or isinstance(usage, bool) or usage <= 0:
        reasons.append("invalid_actor_total")
    if run.get("usage_complete_in_logged_calls") is not True:
        reasons.append("incomplete_actor_usage")
    if run.get("quality_flags"):
        reasons.append("quality_flags_present")
    if run.get("initial_input_status") != "observed_initial" or initial.get("initial_input_status") != "observed_initial":
        reasons.append("unverified_initial_input")
    if not initial.get("task_text") or not initial.get("source_call_id"):
        reasons.append("missing_initial_input_evidence")
    for key in ("episode_id", "benchmark", "canonical_task_id", "config_id"):
        if initial.get(key) != run.get(key):
            reasons.append("initial_identity_mismatch")
            break
    if feature.get("episode_id") != run.get("episode_id") or feature.get("benchmark") != run.get("benchmark") or feature.get("config_id") != run.get("config_id"):
        reasons.append("feature_identity_mismatch")
    if feature.get("task_text") != initial.get("task_text"):
        reasons.append("initial_feature_text_mismatch")
    if config.get("benchmark") not in (None, run.get("benchmark")):
        reasons.append("config_benchmark_mismatch")
    if run.get("archive_sha256") not in archive_hashes:
        reasons.append("source_archive_unverified")
    return sorted(set(reasons))


def _model_features(feature: dict, include_group: bool = False) -> dict:
    keys = ["episode_id", "config_id", *ALLOWED_FEATURES]
    result = {key: feature.get(key) for key in keys}
    if include_group:
        result["task_group"] = feature.get("task_group")
    return result


def build_fold_payload(benchmark: str, runs: list[dict], inputs: dict[str, dict],
                       features: dict[str, dict], configs: dict[str, dict],
                       groups: dict[str, dict], fold: dict) -> dict:
    by_id = {r["episode_id"]: r for r in runs if r.get("benchmark") == benchmark}
    train_ids, test_ids = set(fold["train_ids"]), set(fold["test_ids"])
    if train_ids & test_ids or (train_ids | test_ids) != set(by_id):
        raise ValueError("outer split must partition all benchmark run IDs")
    for ids in (train_ids, test_ids):
        if not {groups[i]["family_group"] for i in ids}:
            raise ValueError("missing family group assignment")
    tr_tasks = {groups[i]["task_group"] for i in train_ids}
    te_tasks = {groups[i]["task_group"] for i in test_ids}
    tr_families = {groups[i]["family_group"] for i in train_ids}
    te_families = {groups[i]["family_group"] for i in test_ids}
    if tr_tasks & te_tasks or tr_families & te_families:
        raise ValueError("task/family leakage across outer split")

    archive_hashes = {r.get("archive_sha256") for r in by_id.values()}
    eligible: dict[str, list[str]] = {}
    for episode_id, run in by_id.items():
        initial = inputs.get(episode_id, {})
        feature = features.get(episode_id, {})
        config = configs.get(run.get("config_id"), {})
        eligible[episode_id] = qualify_run(run, initial, feature, config, archive_hashes)
    labels = [
        {"episode_id": i, "actor_total_tokens_observed": by_id[i]["actor_total_tokens_observed"]}
        for i in fold["train_ids"] if not eligible[i]
    ]
    train_features = [_model_features(features[i]) for i in fold["train_ids"] if not eligible[i]]
    test_features = [_model_features(features[i]) for i in fold["test_ids"]]
    evaluator = []
    for i in fold["test_ids"]:
        run = by_id[i]
        evaluator.append({
            "episode_id": i,
            "canonical_task_id": run.get("canonical_task_id"),
            "task_group": groups[i].get("task_group"),
            "family_group": groups[i].get("family_group"),
            "config_id": run.get("config_id"),
            "source_run_id": run.get("source_run_id"),
            "source_archive_sha256": run.get("archive_sha256"),
            "success": run.get("success"),
            "outcome_status": run.get("outcome_status"),
            "actor_total_tokens_observed": run.get("actor_total_tokens_observed") if not eligible[i] else None,
            "eligible_success_label": not bool(eligible[i]),
            "exclusion_reasons": eligible[i],
        })
    inner = []
    for part in fold["inner"]:
        tr = [i for i in part["train_ids"] if i in train_ids and i in set(x["episode_id"] for x in labels)]
        va = [i for i in part["validation_ids"] if i in train_ids and i in set(x["episode_id"] for x in labels)]
        inner.append({"inner_fold": part["inner_fold"], "train_ids": tr, "validation_ids": va})
    return {"train_features": train_features, "train_labels": labels,
            "test_features": test_features, "evaluator_facts": evaluator,
            "inner_splits": inner, "eligibility_reasons": eligible}


def _sha_map(root: Path) -> dict[str, str]:
    return {name: sha256(root / name) for name in FROZEN}


def _verify_inputs(project: Path) -> tuple[dict, dict]:
    root = project / "data/derived/existing_runs"
    for name, expected in FROZEN.items():
        actual = sha256(root / name)
        if actual != expected:
            raise ValueError(f"frozen input fingerprint mismatch: {name}")
    summary = json.loads((root / "protocol_summary.json").read_text())
    if summary["frozen_files"] != FROZEN:
        raise ValueError("protocol summary frozen-file map differs")
    computed = hashlib.sha256(json.dumps(FROZEN, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if summary.get("data_fingerprint") != computed:
        raise ValueError("protocol data fingerprint mismatch")
    return root, summary


def _read_groups(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return {r["episode_id"]: r for r in rows}


def _source_hashes(project: Path, only_benchmark: str) -> set[str]:
    manifest_path = project / "configs/hal_research_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    expected_manifest = SOURCE_MANIFEST_SHA256
    if expected_manifest and sha256(manifest_path) != expected_manifest:
        raise ValueError("source manifest fingerprint mismatch")
    result = set()
    for row in manifest["files"]:
        if "scienceagentbench" not in row["filename"]:
            continue
        path = project / row["local_path"]
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise ValueError("SAB source archive fingerprint mismatch")
        result.add(row["sha256"])
    if not result:
        raise ValueError("no SAB source archives verified")
    return result


def _verify_initial_call_provenance(project: Path, root: Path, runs: list[dict],
                                    inputs: dict[str, dict]) -> dict:
    """Recheck frozen SAB initial text against earliest raw actor-primary call.

    Uses the repository's documented read-only archive reader in memory. No raw
    message text is returned or written, and no trace code is executed.
    """
    import sys
    for relative, expected_blob in (("tools/hal_pipeline.py", HAL_PIPELINE_GIT_BLOB),
                                    ("research_plan/src/haldata.py", HALDATA_GIT_BLOB)):
        content = (project / relative).read_bytes()
        git_blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        if git_blob != expected_blob:
            raise ValueError(f"fixed source-reader/extractor version mismatch: {relative}")
    sys.path.insert(0, str(project / "research_plan/src"))
    sys.path.insert(0, str(project / "tools"))
    from haldata import read_archive
    from hal_pipeline import deduplicate_calls, initial_input, model_key

    source_manifest_path = project / "configs/hal_research_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text())
    sab_runs = [r for r in runs if r.get("benchmark") == "scienceagentbench"]
    by_key = {(r.get("archive_sha256"), str(r.get("task_id"))): r for r in sab_runs}
    by_input = inputs
    counts = {"archives_read": 0, "rows_checked": 0, "exact_matches": 0,
              "missing_primary_call": 0, "source_call_id_mismatch": 0,
              "role_or_text_mismatch": 0}
    for source in source_manifest["files"]:
        if "scienceagentbench" not in source["filename"]:
            continue
        path = project / source["local_path"]
        if path.stat().st_size != source["bytes"] or sha256(path) != source["sha256"]:
            raise ValueError("SAB source hash/size mismatch during input provenance check")
        archive = read_archive(path)
        counts["archives_read"] += 1
        args = archive["config"].get("agent_args", {})
        main_model = str(args.get("model_name", args.get("agent.model.name")) or "").lower().split("/")[-1]
        calls = deduplicate_calls(archive["raw_logging_results"])
        role_models = {model_key(k): v for k, v in source.get("role_models", {}).items()}
        per_task = {}
        for call in calls:
            task_id = call.get("task_id")
            if task_id is None:
                continue
            models = {model_key(call.get("input_model")), model_key(call.get("output_model"))} - {""}
            role = "actor_primary" if model_key(main_model) in models else next(
                (role_models[m] for m in models if m in role_models), "unknown")
            call["role"] = role
            per_task.setdefault(task_id, []).append(call)
        for task_id, task_calls in per_task.items():
            run = by_key.get((source["sha256"], task_id))
            if run is None:
                continue
            counts["rows_checked"] += 1
            primary = [c for c in task_calls if c["included"] and c["role"] == "actor_primary"]
            result = initial_input(archive["raw_logging_results"],
                                   [c["source_index"] for c in primary], "scienceagentbench")
            frozen = by_input[run["episode_id"]]
            if frozen.get("source_call_id") != result.get("source_call_id"):
                counts["source_call_id_mismatch"] += 1
                continue
            if (frozen.get("initial_input_status") != result.get("status") or
                    frozen.get("initial_input_status") != "observed_initial" or
                    not result.get("text") or frozen.get("task_text") != result.get("text")):
                counts["role_or_text_mismatch"] += 1
                continue
            counts["exact_matches"] += 1
    expected = len(sab_runs)
    counts["missing_primary_call"] = expected - counts["rows_checked"]
    if counts["rows_checked"] != expected or counts["exact_matches"] != expected:
        raise ValueError("SAB initial-call provenance check did not match every frozen row")
    return counts


def _validate_linkage(runs, inputs, features, groups):
    ids = [r["episode_id"] for r in runs]
    if len(ids) != len(set(ids)) or set(ids) != set(inputs) or set(ids) != set(features) or set(ids) != set(groups):
        raise ValueError("episode identity linkage is not one-to-one")
    for r in runs:
        i = r["episode_id"]
        if (inputs[i].get("canonical_task_id") != r.get("canonical_task_id") or
                inputs[i].get("benchmark") != r.get("benchmark") or
                inputs[i].get("config_id") != r.get("config_id") or
                features[i].get("benchmark") != r.get("benchmark") or
                features[i].get("config_id") != r.get("config_id") or
                groups[i].get("benchmark") != r.get("benchmark")):
            raise ValueError("run/input/feature/group identity mismatch")
        if features[i].get("task_text") != inputs[i].get("task_text"):
            raise ValueError("initial text linkage mismatch")


def prepare(project: Path, repo: Path, output: Path) -> dict:
    project, repo, output = project.resolve(), repo.resolve(), output.resolve()
    if output == project or output == repo or project in output.parents or repo in output.parents:
        raise ValueError("private output must be outside source and repository trees")
    if output.exists():
        raise FileExistsError("refusing to overwrite an existing controlled output")
    root, summary = _verify_inputs(project)
    if sha256(root / "initial_inputs.internal.jsonl") != INITIAL_INPUTS_SHA256:
        raise ValueError("initial-input linkage file fingerprint mismatch")
    runs = read_jsonl(root / "runs.jsonl")
    features_list = read_jsonl(root / "features.internal.jsonl")
    inputs_list = read_jsonl(root / "initial_inputs.internal.jsonl")
    features = {x["episode_id"]: x for x in features_list}
    inputs = {x["episode_id"]: x for x in inputs_list}
    groups = _read_groups(root / "groups.csv")
    _validate_linkage(runs, inputs, features, groups)
    raw_archive_hashes = _source_hashes(project, "scienceagentbench")
    initial_provenance = _verify_initial_call_provenance(project, root, runs, inputs)
    configs = json.loads((root / "agent_configs.json").read_text())
    splits = json.loads((root / "split_manifest.json").read_text())
    fold = splits["partitions"]["scienceagentbench"]["family"]["folds"][0]
    sab_runs = [r for r in runs if r.get("benchmark") == "scienceagentbench"]
    sab_inputs = {k: v for k, v in inputs.items() if v.get("benchmark") == "scienceagentbench"}
    sab_features = {k: v for k, v in features.items() if v.get("benchmark") == "scienceagentbench"}
    sab_groups = {k: v for k, v in groups.items() if v.get("benchmark") == "scienceagentbench"}
    # Episode-level references must resolve to the verified source archives.
    for run in sab_runs:
        if run.get("archive_sha256") not in raw_archive_hashes:
            raise ValueError("SAB run references an unverified archive")
    payload = build_fold_payload("scienceagentbench", sab_runs, sab_inputs,
                                 sab_features, configs, sab_groups, fold)
    stage = output.with_name(output.name + ".staging")
    if stage.exists():
        raise FileExistsError("staging directory already exists")
    trainer, evaluator = stage / "trainer_release", stage / "evaluator_private"
    trainer.mkdir(parents=True, mode=0o700)
    evaluator.mkdir(mode=0o700)
    write_jsonl(trainer / "train_features.jsonl", payload["train_features"])
    write_jsonl(trainer / "train_labels.jsonl", payload["train_labels"])
    write_jsonl(trainer / "test_features.jsonl", payload["test_features"])
    (trainer / "validation_splits.json").write_text(json.dumps(payload["inner_splits"], indent=2) + "\n")
    (trainer / "feature_whitelist.json").write_text(json.dumps({
        "model_input_features": list(ALLOWED_FEATURES),
        "linkage_only": ["episode_id", "config_id"],
        "excluded": ["success", "outcome_status", "actor_total_tokens_observed",
                     "stop_reason", "call_count", "task_group", "family_group",
                     "agent_output", "evaluator_content", "reference_answer"]
    }, indent=2) + "\n")
    (trainer / "README.md").write_text(
        "Review-only trainer candidate. Contains eligible training features/labels, "
        "unlabeled outer-test features, and fixed inner split IDs. Do not merge with "
        "the sibling evaluator package. This directory is not training authorization.\n")
    write_jsonl(evaluator / "test_facts.jsonl", payload["evaluator_facts"])
    (evaluator / "README.md").write_text(
        "Restricted evaluator facts for one fixed outer family fold. Keep this directory "
        "physically separate from trainer_release; do not distribute its labels with model inputs.\n")
    manifest = {
        "status": "review_ready",
        "training_approved": False,
        "source_data_fingerprint": summary["data_fingerprint"],
        "source_file_sha256": _sha_map(root),
        "source_archive_sha256": sorted(raw_archive_hashes),
        "initial_call_provenance": initial_provenance,
        "split": "scienceagentbench family outer_fold=0; fixed existing split",
        "trainer_release_contains_test_targets": False,
        "evaluator_private_is_separate_sibling": True,
        "eligibility_counts": {"train": len(payload["train_labels"]),
                                "test": sum(x["eligible_success_label"] for x in payload["evaluator_facts"])},
        "private_file_sha256": {},
    }
    for sub in (trainer, evaluator):
        for p in sorted(sub.rglob("*")):
            if p.is_file():
                os.chmod(p, 0o600)
                manifest["private_file_sha256"][str(p.relative_to(stage))] = sha256(p)
    for sub in (trainer, evaluator):
        os.chmod(sub, 0o700)
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.chmod(stage / "manifest.json", 0o600)
    os.chmod(stage, 0o700)
    os.replace(stage, output)
    return {"manifest": manifest, "payload": payload, "runs": sab_runs,
            "groups": sab_groups, "inputs": sab_inputs, "features": sab_features,
            "fold": fold}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.project_root, args.repo_root, args.output_root)
    print(json.dumps({"status": result["manifest"]["status"],
                      "train_eligible": result["manifest"]["eligibility_counts"]["train"],
                      "test_eligible": result["manifest"]["eligibility_counts"]["test"]}, sort_keys=True))


if __name__ == "__main__":
    main()
