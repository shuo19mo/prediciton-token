#!/usr/bin/env python3
"""Read-only index of historical HAL stopping evidence.

This tool reads frozen derived facts and archived JSON only. It never imports,
executes, or evaluates code found inside an archive.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import zipfile
from urllib.parse import urlparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "hal-stopping-evidence-v1"
TOOL_VERSION = "0.1.0"
EXPECTED_COMMITS = {
    "23fc5665d6804fa72240f479e38f73fb53600002": ("sab_self_debug", ["write_program", "step", "solve_task"]),
    "eb094b928198c6e1029a8e0c247576c78a1fe9f7": ("sab_self_debug", ["write_program", "step", "solve_task"]),
    "edfe626b0e96fbf92fb8a41a705e31205d716e1e": ("sab_self_debug", ["write_program", "step", "solve_task"]),
    "bc575cd58bdb0a203c08952169df7e5d3330b8d8": ("hal_generalist", ["check_budget_exceeded", "max_steps", "solve_task"]),
    "c7354ebd3ce3d284e3c89150e1218836c42eccac": ("core_agent", ["max_steps", "budget"]),
    "7e56e6688e288e8db86b3612b551370330ae218d": ("core_agent", ["max_steps", "budget"]),
    "8a0e2933c7e2b6162c149810aff02a3d4cbcd48c": ("hal_generalist", ["max_steps", "check_budget_exceeded"]),
    "6a44aedf5ca8bfc81f9354658a4f66553eee730d": ("hal_generalist", ["max_steps", "check_budget_exceeded"]),
    "02a2500e9883ecc022b3eeae29bc5b557788b3c7": ("swe_agent", ["gitlink", "cost_limit", "autosubmit"]),
    "85513dbe3ac92d135c304cd9ef5920e5a78f436f": ("swe_agent", ["gitlink", "cost_limit", "autosubmit"]),
    "0ac45fa43a60658ec037b354b5039d3131317069": ("scicode", ["generation", "evaluation_timeout"]),
    "b64fc7cc5c0aa7ea2fbf197d835805460bcf2e7b": ("taubench", ["wrapper", "dependency_pin", "solve", "env.step"]),
}
# Preserve the exact archive origin string. These pairs were extracted from the
# frozen archive metadata; normalized URLs are only for constructing links.
EXPECTED_REPOSITORY_BY_COMMIT = {
    "23fc5665d6804fa72240f479e38f73fb53600002": "https://github.com/OSU-NLP-Group/hal-harness.git",
    "eb094b928198c6e1029a8e0c247576c78a1fe9f7": "https://github.com/OSU-NLP-Group/hal-harness.git",
    "edfe626b0e96fbf92fb8a41a705e31205d716e1e": "https://github.com/benediktstroebl/hal-harness.git",
    "bc575cd58bdb0a203c08952169df7e5d3330b8d8": "https://github.com/benediktstroebl/hal-harness.git",
    "c7354ebd3ce3d284e3c89150e1218836c42eccac": "https://github.com/princeton-pli/hal-harness.git",
    "7e56e6688e288e8db86b3612b551370330ae218d": "https://github.com/princeton-pli/hal-harness.git",
    "8a0e2933c7e2b6162c149810aff02a3d4cbcd48c": "https://github.com/benediktstroebl/hal-harness.git",
    "6a44aedf5ca8bfc81f9354658a4f66553eee730d": "https://github.com/benediktstroebl/hal-harness.git",
    "02a2500e9883ecc022b3eeae29bc5b557788b3c7": "git@github.com:boyiwei/hal-harness.git",
    "85513dbe3ac92d135c304cd9ef5920e5a78f436f": "git@github.com:boyiwei/hal-harness.git",
    "0ac45fa43a60658ec037b354b5039d3131317069": "https://github.com/peterkirgis/hal-harness.git",
    "b64fc7cc5c0aa7ea2fbf197d835805460bcf2e7b": "https://github.com/princeton-pli/hal-harness",
}


def _registered_source_pair(repository_url: str | None, commit: str | None) -> bool:
    """A commit is registered only with its archive's exact raw origin URL."""
    return bool(repository_url and commit in EXPECTED_REPOSITORY_BY_COMMIT
                and EXPECTED_REPOSITORY_BY_COMMIT[commit] == repository_url)
SOURCE_ARTIFACTS = {
    ("sab_self_debug", "agents/sab_example_agent/science_agent.py"): {"role": "agent_control_flow", "lines": [[94, 125], [166, 218], [220, 253]], "symbols": ["write_program", "step", "solve_task"]},
    ("hal_generalist", "agents/hal_generalist_agent/main.py"): {"role": "agent_control_flow", "lines": [], "symbols": ["check_budget_exceeded", "max_steps", "solve_task"]},
    ("core_agent", "agents/core_agent/main.py"): {"role": "agent_control_flow", "lines": [[89, 99], [505, 509], [725, 732]], "symbols": ["check_budget_exceeded", "max_steps", "budget"]},
    ("swe_agent", ".gitmodules"): {"role": "submodule_source_map", "lines": [], "symbols": ["agents/SWE-agent-v1.0"]},
    ("scicode", "agents/scicode_example_agent/main.py"): {"role": "agent_generation", "lines": [[108, 139]], "symbols": ["for i in range(steps)"]},
    ("scicode", "hal/benchmarks/scicode.py"): {"role": "evaluator_runtime", "lines": [[104, 109], [132, 138]], "symbols": ["timeout 60", "subprocess"]},
    ("taubench", "agents/taubench_tool_calling/tool_calling.py"): {"role": "agent_wrapper", "lines": [[37, 42]], "symbols": ["agent.solve", "taken_actions"]},
    ("taubench", "pyproject.toml"): {"role": "dependency_configuration", "lines": [[39, 40], [49, 50], [61, 62], [73, 74]], "symbols": ["tau-bench git dependency pins"]},
}
PINNED_EXTERNALS = {
    "swe": {
        "repo": "boyiwei/SWE-agent",
        "path": "sweagent/agent/agents.py",
        "commits": {"02a2500e9883ecc022b3eeae29bc5b557788b3c7": "94f540cd146775dc1c092251422167b776d3d0aa", "85513dbe3ac92d135c304cd9ef5920e5a78f436f": "d872eb743ef9db31b31c253a8d26b31eb4349ac0"},
    },
    "tau": {"repo": "benediktstroebl/tau-bench", "commit": "807e348b46a225242d5a045a8cecc690719e4b21", "candidate_commits": ["807e348b46a225242d5a045a8cecc690719e4b21", "bef42de85cdbfb5490e6f3bd19d8e053df977e08"], "paths": ["tau_bench/agents/tool_calling_agent.py", "tau_bench/envs/base.py"]},
}
GIT_BLOB_PINS = {
    ("23fc5665d6804fa72240f479e38f73fb53600002", "agents/sab_example_agent/science_agent.py"): "04abb4ea7729476f2221be2dc8ef10df9de60558",
    ("eb094b928198c6e1029a8e0c247576c78a1fe9f7", "agents/sab_example_agent/science_agent.py"): "04abb4ea7729476f2221be2dc8ef10df9de60558",
    ("bc575cd58bdb0a203c08952169df7e5d3330b8d8", "agents/hal_generalist_agent/main.py"): "8eacfaa33a981aafd85089d8b8e7b5143d342607",
    ("8a0e2933c7e2b6162c149810aff02a3d4cbcd48c", "agents/hal_generalist_agent/main.py"): "96b3d5c190761895d3059411c7f994e546655d87",
    ("6a44aedf5ca8bfc81f9354658a4f66553eee730d", "agents/hal_generalist_agent/main.py"): "8ef6e1c1699204d671aa51c728e83dc1dd516601",
    ("c7354ebd3ce3d284e3c89150e1218836c42eccac", "agents/core_agent/main.py"): "3839a0fa8b5a5e11926b5fd4a73099eda3781d4d",
    ("7e56e6688e288e8db86b3612b551370330ae218d", "agents/core_agent/main.py"): "3839a0fa8b5a5e11926b5fd4a73099eda3781d4d",
    ("0ac45fa43a60658ec037b354b5039d3131317069", "agents/scicode_example_agent/main.py"): "996971023aba816ebad3222289bcd5de21e35b93",
    ("0ac45fa43a60658ec037b354b5039d3131317069", "hal/benchmarks/scicode.py"): "9d295844af3f9f22b62529e0b66e943b96568a9e",
    ("b64fc7cc5c0aa7ea2fbf197d835805460bcf2e7b", "agents/taubench_tool_calling/tool_calling.py"): "e7076a2781d46c0e7c8b4935a2d25205a7bc1ddd",
    ("b64fc7cc5c0aa7ea2fbf197d835805460bcf2e7b", "pyproject.toml"): "eda0509441ce76eda8592fa41f5f238d34af15c9",
    ("02a2500e9883ecc022b3eeae29bc5b557788b3c7", ".gitmodules"): "b2993c2425f67418620bc8329cc395e7caafaab1",
    ("85513dbe3ac92d135c304cd9ef5920e5a78f436f", ".gitmodules"): "a7294c2574ac3635a7ca82df4ec1b4f41bcd4250",
}
EXTERNAL_GIT_BLOBS = {
    ("94f540cd146775dc1c092251422167b776d3d0aa", "sweagent/agent/agents.py"): "aff6195f23d63ab916d7ffccc845449cfbe9233d",
    ("d872eb743ef9db31b31c253a8d26b31eb4349ac0", "sweagent/agent/agents.py"): "a53cc29b14a8efbecbb6b37b67882c3dcd6d8c7d",
    ("94f540cd146775dc1c092251422167b776d3d0aa", "config/250225_anthropic_filemap_simple_review.yaml"): "c86c2f615ffa84b619485010952a098c79218deb",
    ("d872eb743ef9db31b31c253a8d26b31eb4349ac0", "config/benchmarks/250225_anthropic_filemap_simple_review.yaml"): "c86c2f615ffa84b619485010952a098c79218deb",
    ("807e348b46a225242d5a045a8cecc690719e4b21", "tau_bench/agents/tool_calling_agent.py"): "f270b9aaddebabd4cdc9a6b947f6a4507d6f958e",
    ("807e348b46a225242d5a045a8cecc690719e4b21", "tau_bench/envs/base.py"): "632f060c82c960cbc62b5dfe8a666815468d7d0d",
    ("bef42de85cdbfb5490e6f3bd19d8e053df977e08", "tau_bench/agents/tool_calling_agent.py"): "f270b9aaddebabd4cdc9a6b947f6a4507d6f958e",
    ("bef42de85cdbfb5490e6f3bd19d8e053df977e08", "tau_bench/envs/base.py"): "632f060c82c960cbc62b5dfe8a666815468d7d0d",
}


class AuditError(ValueError):
    """Invalid or inconsistent frozen input."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AuditError(f"invalid JSONL at line {line_no}") from exc
            if not isinstance(row, dict):
                raise AuditError(f"non-object JSONL row at line {line_no}")
            rows.append(row)
    return rows


def _presence(obj: dict[str, Any], key: str, inspected: bool = True) -> str:
    if not inspected:
        return "uninspected"
    if key not in obj:
        return "absent"
    return "empty" if obj[key] in (None, "", [], {}) else "present"


def _walk_named(value: Any, wanted: set[str], prefix: str = "") -> list[tuple[str, Any]]:
    """Return scalar fields with selected names without preserving unrelated text."""
    found: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            pointer = f"{prefix}/{_pointer_escape(str(key))}"
            if key in wanted and not isinstance(child, (dict, list)):
                found.append((pointer, child))
            elif isinstance(child, (dict, list)):
                found.extend(_walk_named(child, wanted, pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            if isinstance(child, (dict, list)):
                found.extend(_walk_named(child, wanted, f"{prefix}/{index}"))
    return found


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _archive_reader(data_root: Path):
    """Load only the reviewed HAL archive reader; no archived code is imported."""
    module_path = data_root / "research_plan/src/haldata.py"
    if not module_path.is_file():
        raise AuditError("missing reviewed reader: research_plan/src/haldata.py")
    spec = importlib.util.spec_from_file_location("haldata_readonly", module_path)
    if not spec or not spec.loader:
        raise AuditError("cannot load reviewed archive reader")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:
        raise AuditError(f"archive reader dependency unavailable: {exc.name}") from exc
    if not callable(getattr(module, "read_archive", None)):
        raise AuditError("reviewed archive reader lacks read_archive")
    return module.read_archive


def _archive_record_locator(archive: dict[str, Any], run: dict[str, Any]) -> tuple[str | None, Any, str]:
    """Join an existing episode to a raw result by exact task key only."""
    raw = archive.get("raw_eval_results")
    benchmark = run.get("benchmark")
    task = str(run.get("task_id")) if run.get("task_id") is not None else None
    if not isinstance(raw, dict) or task is None:
        return None, None, "raw_result_unavailable"
    candidate_maps = []
    if benchmark == "scienceagentbench":
        candidate_maps.extend((f"raw_eval_results/{name}", raw[name]) for name in ("agent_output", "eval_result") if isinstance(raw.get(name), dict))
    elif benchmark == "scicode":
        candidate_maps.extend((f"raw_eval_results/{name}", raw[name]) for name in ("agent_output", "eval_result", "details") if isinstance(raw.get(name), dict))
    elif benchmark == "taubench_airline":
        candidate_maps.append(("raw_eval_results", raw))
    elif benchmark == "corebench_hard":
        candidate_maps.append(("raw_eval_results", raw))
    elif benchmark == "swebench_verified_mini":
        result_fields = ("completed_ids", "incomplete_ids", "submitted_ids", "resolved_ids", "unresolved_ids", "empty_patch_ids", "error_ids")
        found = []
        for field in result_fields:
            values = raw.get(field)
            if isinstance(values, list):
                found.extend((field, i) for i, value in enumerate(values) if str(value) == task)
        if found:
            locators = [f"raw_eval_results/{field}/{index}" for field,index in found]
            return locators[0], {"membership_fields": sorted({field for field,_ in found})}, "exact_task_key"
    matches = [(name, values[task]) for name, values in candidate_maps if task in values]
    if matches:
        # agent_output is the task runtime output; eval_result is a separate evaluator layer.
        preferred = next((match for match in matches if match[0].endswith("/agent_output")), None)
        if preferred is None:
            preferred = next((match for match in matches if match[0].endswith("/details")), None)
        if preferred is None:
            preferred = next((match for match in matches if match[0] == "raw_eval_results"), None)
        if preferred is None:
            preferred = matches[0]
        return preferred[0] + "/" + _pointer_escape(task), preferred[1], "exact_task_key"
    return None, None, "task_key_not_found"


def _archive_task_evidence(archive: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    """Production task/evaluator association path, with conservative labels."""
    pointer, raw_record, join_status = _archive_record_locator(archive, run)
    observations = []
    if isinstance(raw_record, str) and raw_record.startswith("TIMEOUT"):
        observations.append({"layer": "task_runtime_marker", "code": "explicit_timeout_prefix", "source_ref": "archive", "field_pointer": f"/{pointer}", "presence": "present", "interpretation_scope": "top_level_agent_output_marker", "excerpt_internal": raw_record[:240]})
    elif isinstance(raw_record, str) and raw_record.startswith("ERROR:"):
        observations.append({"layer": "task_runtime_marker", "code": "explicit_error_prefix", "source_ref": "archive", "field_pointer": f"/{pointer}", "presence": "present", "interpretation_scope": "top_level_agent_output_marker", "excerpt_internal": raw_record[:240]})
    raw_eval = archive.get("raw_eval_results")
    task_key = str(run.get("task_id")) if run.get("task_id") is not None else None
    if task_key and isinstance(raw_eval, dict) and isinstance(raw_eval.get("eval_result"), dict):
        eval_map = raw_eval["eval_result"]
        if task_key in eval_map and isinstance(eval_map[task_key], dict):
            eval_record = eval_map[task_key]
            for key in ("log_info", "error", "exception"):
                if key in eval_record:
                    observations.append({"layer": "evaluation_diagnostic", "code": f"eval_{key}", "source_ref": "archive", "field_pointer": f"/raw_eval_results/eval_result/{_pointer_escape(task_key)}/{key}", "presence": _presence(eval_record, key), "interpretation_scope": "evaluation-only", "excerpt_internal": json.dumps(eval_record[key], ensure_ascii=False)[:400]})
    return {
        "raw_record_pointer": pointer,
        "raw_record": raw_record,
        "join_status": join_status,
        "observations": observations,
        "task_termination": {"status": "unknown"},
        "identification_assessment": _identification_unknown("Synthetic or archived output markers and evaluator diagnostics do not establish identification conditions."),
    }


def _validate_run_label_relations(runs: list[dict[str, Any]], labels: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    seen = set()
    by_episode = {}
    run_keys = set()
    for row in runs:
        eid = row.get("episode_id")
        if not eid or eid in seen:
            raise AuditError("missing or duplicate episode_id in runs.jsonl")
        seen.add(eid)
        run_keys.add((row.get("archive_sha256"), str(row.get("task_id"))))
        by_episode[eid] = row
    if len(run_keys) != len(runs):
        raise AuditError("duplicate archive/task identity in runs.jsonl")
    grouped_labels: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in labels:
        eid = row.get("episode_id")
        if eid not in seen:
            raise AuditError("candidate row refers to unknown episode_id")
        run = by_episode[eid]
        if row.get("benchmark") != run.get("benchmark") or row.get("config_id") != run.get("config_id"):
            raise AuditError("candidate benchmark/config association disagrees with run")
        grouped_labels[eid].append(row)
    if set(grouped_labels) != seen:
        raise AuditError("one or more episodes have no candidate rows")
    for rows_for_episode in grouped_labels.values():
        if Counter(row.get("protocol") for row in rows_for_episode) != Counter({"A": 1, "B": 1}):
            raise AuditError("episode must have exactly one A and one B candidate row")
    return by_episode, grouped_labels


def _verify_file_receipt(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> bool:
    if not path.is_file() or path.stat().st_size != expected_bytes or sha256_file(path) != expected_sha256:
        raise AuditError(f"{label} hash/size mismatch")
    return True


def _serialize_evidence_rows(rows: list[dict[str, Any]]) -> tuple[str, str]:
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    return payload, hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _aggregate_observation_presence(rows: list[dict[str, Any]], b_subset: bool = False) -> dict[str, dict[str, dict[str, int]]]:
    counts: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    for row in rows:
        if b_subset and not row.get("in_B_failure_subset"):
            continue
        for observation in row.get("observations", []):
            counts[observation.get("layer", "unknown")][observation.get("code", "unknown")][observation.get("presence", "unknown")] += 1
    return {layer: {code: dict(sorted(presence_counts.items())) for code, presence_counts in sorted(codes.items())} for layer, codes in sorted(counts.items())}


def _raw_call_evidence(archive: dict[str, Any], run: dict[str, Any]) -> list[dict[str, Any]]:
    logs = archive.get("raw_logging_results")
    if not isinstance(logs, list):
        return [{"layer": "call_finish_reason", "code": "call_logs_unavailable", "source_ref": "archive", "field_pointer": "/raw_logging_results", "presence": _presence(archive, "raw_logging_results"), "interpretation_scope": "call-level"}]
    task_id = str(run.get("task_id"))
    matching = []
    for i, row in enumerate(logs):
        if not isinstance(row, dict):
            continue
        attrs = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
        weave_task = row.get("weave_task_id", attrs.get("weave_task_id"))
        if weave_task is not None and str(weave_task) == task_id:
            matching.append((i, row))
    if not matching:
        return [{"layer": "call_finish_reason", "code": "no_exact_task_call_join", "source_ref": "archive", "field_pointer": "/raw_logging_results", "presence": "uninspected", "interpretation_scope": "call-level"}]
    out = []
    for index, call in matching:
        finishes = _walk_named(call, {"finish_reason", "stop_reason"})
        if not finishes:
            out.append({"layer": "call_finish_reason", "code": "finish_reason_not_recorded", "source_ref": "archive", "field_pointer": f"/raw_logging_results/{index}", "presence": "absent", "interpretation_scope": "call-level"})
        for pointer, value in finishes:
            out.append({"layer": "call_finish_reason", "code": "finish_reason_observed", "source_ref": "archive", "field_pointer": f"/raw_logging_results/{index}{pointer}", "presence": _presence({"v": value}, "v"), "interpretation_scope": "call-level", "value": value if isinstance(value, (str, int, float, bool)) else None})
    return out


def _rules(run: dict[str, Any]) -> list[dict[str, Any]]:
    restrictions = run.get("historical_restrictions")
    if not isinstance(restrictions, dict):
        return [{"name": "historical_restrictions", "scope": "unknown", "unit": "unknown", "value": None, "source": "derived_runs", "presence": "uninspected"}]
    rules = []
    for name, value in sorted(restrictions.items()):
        if name == "max_tokens":
            scope, unit = "per_call", "tokens"
        elif name == "max_steps":
            scope, unit = "run", "steps"
        elif name in {"budget", "agent.model.per_instance_cost_limit"}:
            scope, unit = "run", "USD_or_unspecified_currency"
        else:
            scope, unit = "unknown", "unknown"
        rules.append({"name": name, "scope": scope, "unit": unit, "value": value, "source": "derived_runs/historical_restrictions", "presence": _presence(restrictions, name)})
    if not any(rule["name"] == "whole_run_token_cap" for rule in rules):
        rules.append({"name": "whole_run_token_cap", "scope": "run", "unit": "tokens", "value": run.get("whole_run_token_cap"), "source": "derived_runs/whole_run_token_cap", "presence": "empty" if run.get("whole_run_token_cap") is None else "present"})
    return rules


def _identification_unknown(reason: str) -> dict[str, Any]:
    return {name: {"status": "unknown", "reason": reason, "evidence_refs": [], "judgment_source": "not_inferred_by_implementation"} for name in ("T_gt_U", "same_continuation", "first_success_visibility", "conditional_independence")}


def _b_failure_candidate(rows: list[dict[str, Any]], benchmark: str) -> bool:
    matches = [row for row in rows if row.get("protocol") == "B"]
    if len(matches) != 1:
        raise AuditError("episode does not have exactly one B protocol candidate")
    row = matches[0]
    if row.get("benchmark") != benchmark:
        raise AuditError("candidate/run benchmark mismatch")
    return row.get("included") is True and row.get("event") == 0


def _limit_consistency(declared_limit: int | float | None, observed_count: int | None) -> dict[str, Any]:
    """Compare like-named synthetic counts; never infer that a limit was triggered."""
    if declared_limit is None or observed_count is None:
        return {"status": "unknown", "reason": "limit or comparable observation is missing"}
    if observed_count > declared_limit:
        return {"status": "conflicting", "reason": "observed count exceeds the declared limit; unit/runtime mapping needs review"}
    return {"status": "unknown", "reason": "observation does not prove the limit triggered or did not trigger"}


def _validate_public_payload(value: Any, path: str = "") -> None:
    forbidden = {"episode_id", "task_id", "canonical_task_id", "prompt", "answer", "result_raw", "usage", "observed_tokens", "excerpt_internal", "raw_record_pointer", "local_path"}
    if isinstance(value, dict):
        bad = forbidden.intersection(value)
        if bad:
            raise AuditError(f"public output contains private fields at {path or '/'}")
        for key, child in value.items():
            _validate_public_payload(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_public_payload(child, f"{path}/{index}")
    elif isinstance(value, str):
        # Public URLs and RFC6901 field names are allowed, host-local paths are not.
        if re.match(r"^(?:/Users/|/private/|/tmp/|[A-Za-z]:\\)", value):
            raise AuditError(f"public output contains an absolute local path at {path or '/'}")


def _source_index(data_root: Path, runs: list[dict[str, Any]], index_path: Path, archive_values: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    receipts_paths = [
        data_root / "docs/evidence/hal_review_2026-09-28/historical_code_receipts.json",
        data_root / "docs/evidence/hal_implementation/historical_code/receipts.json",
    ]
    receipts = []
    for path in receipts_paths:
        if path.is_file():
            value = read_json(path)
            receipts.extend(value if isinstance(value, list) else [])
    def commit_path_key(url: str | None) -> tuple[str, str] | None:
        if not url:
            return None
        parsed = urlparse(url)
        pieces = parsed.path.strip("/").split("/")
        if parsed.netloc == "raw.githubusercontent.com" and len(pieces) >= 4:
            return pieces[2], "/".join(pieces[3:])
        if parsed.netloc == "github.com" and len(pieces) >= 5 and pieces[2] in {"blob", "tree"}:
            return pieces[3], "/".join(pieces[4:])
        return None
    receipts_by_key = {commit_path_key(item.get("url")): item for item in receipts if isinstance(item, dict) and commit_path_key(item.get("url"))}
    repo_by_commit: dict[str, set[str]] = defaultdict(set)
    for archive in archive_values.values():
        git = archive.get("git_info") if isinstance(archive.get("git_info"), dict) else {}
        if git.get("commit") and git.get("repository_url"):
            repo_by_commit[str(git["commit"])].add(str(git["repository_url"]))

    def normalize_repo(original: str) -> tuple[str | None, str | None]:
        match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", original)
        if match:
            full_name = match.group(1)
        elif re.fullmatch(r"[^/]+/[^/]+", original):
            # External pins are stored as owner/repository; this is only a
            # presentation URL normalization, not a change to archive origin.
            full_name = original
        else:
            return None, None
        return full_name, f"https://github.com/{full_name}"

    def file_record(repo: str, commit: str, path: str, role: str, lines: list[list[int]], symbols: list[str], source_kind: str) -> dict[str, Any]:
        repo_name, repo_url = normalize_repo(repo)
        url = f"{repo_url}/blob/{commit}/{path}" if repo_url else None
        receipt = receipts_by_key.get((commit, path))
        local_file = data_root / "docs/evidence/hal_review_2026-09-28" / (receipt.get("local", "") if receipt else "")
        if not local_file.is_file() and receipt:
            local_file = data_root / "docs/evidence/hal_implementation/historical_code" / receipt.get("filename", "")
        exists = bool(receipt and local_file.is_file())
        actual = sha256_file(local_file) if exists else None
        receipt_ok = bool(exists and actual == receipt.get("sha256") and local_file.stat().st_size == receipt.get("bytes"))
        if exists and not receipt_ok:
            raise AuditError(f"historical source receipt mismatch for {commit}:{path}")
        commit_for_blob = commit if source_kind == "hal" else commit
        git_blob = GIT_BLOB_PINS.get((commit_for_blob, path)) if source_kind == "hal" else EXTERNAL_GIT_BLOBS.get((commit_for_blob, path))
        return {
            "repository": repo_name, "commit": commit, "path": path, "url": url,
            "sha256": actual if receipt_ok else None,
            "verification_source_url": receipt.get("url") if receipt_ok else None,
            "git_blob_sha": git_blob,
            "bytes": local_file.stat().st_size if receipt_ok else None,
            "relevant_line_ranges": lines, "relevant_symbols": symbols, "role": role,
            "content_verification": "local_receipt_sha256_verified" if receipt_ok else ("immutable_git_blob_oid_recorded; raw-byte-sha256-unavailable" if git_blob else "unknown_content_hash"),
            "gap": None if receipt_ok else ("GitHub returned a commit-pinned readable source and git blob ID, but this run did not obtain raw bytes to verify SHA256." if git_blob else "Exact historical file bytes/hash not verified."),
        }

    entries = []
    for commit, (kind, topics) in sorted(EXPECTED_COMMITS.items()):
        repositories = sorted(repo_by_commit.get(commit, set()))
        expected_repository = EXPECTED_REPOSITORY_BY_COMMIT.get(commit)
        if len(repositories) != 1 or repositories[0] != expected_repository:
            original_repo = repositories
            normalized_repo = None
            repo_name = None
        else:
            original_repo = repositories[0]
            repo_name, normalized_repo = normalize_repo(original_repo)
        matching_runs = [r for r in runs if r.get("code_commit") == commit]
        relevant_artifacts = [item for item in SOURCE_ARTIFACTS.items() if item[0][0] == kind]
        files = []
        for (_, path), spec in relevant_artifacts:
            spec_lines = spec["lines"]
            if kind == "hal_generalist":
                spec_lines = {
                    "bc575cd58bdb0a203c08952169df7e5d3330b8d8": [[90, 99], [507, 509]],
                    "8a0e2933c7e2b6162c149810aff02a3d4cbcd48c": [[465, 465], [577, 577], [1073, 1073]],
                    "6a44aedf5ca8bfc81f9354658a4f66553eee730d": [[101, 108], [518, 520]],
                }.get(commit, [])
            item = file_record(original_repo if isinstance(original_repo, str) else "", commit, path, spec["role"], spec_lines, spec["symbols"], "hal")
            if item["git_blob_sha"] is None and (commit, path) == ("edfe626b0e96fbf92fb8a41a705e31205d716e1e", "agents/sab_example_agent/science_agent.py"):
                item["content_verification"] = "local_receipt_sha256_verified" if item["sha256"] else item["content_verification"]
            if kind == "taubench" and path == "pyproject.toml":
                item["dependency_pin_candidates"] = [
                    {"repository": PINNED_EXTERNALS["tau"]["repo"], "commit": PINNED_EXTERNALS["tau"]["commit"], "url": f"https://github.com/{PINNED_EXTERNALS['tau']['repo']}/tree/{PINNED_EXTERNALS['tau']['commit']}", "lines": [40, 50, 62], "resolved_for_each_run": "unknown"},
                    {"repository": PINNED_EXTERNALS["tau"]["repo"], "commit": "bef42de85cdbfb5490e6f3bd19d8e053df977e08", "url": f"https://github.com/{PINNED_EXTERNALS['tau']['repo']}/tree/bef42de85cdbfb5490e6f3bd19d8e053df977e08", "lines": [74], "resolved_for_each_run": "unknown"},
                ]
            files.append(item)
        if kind == "swe_agent":
            sub_commit = PINNED_EXTERNALS["swe"]["commits"][commit]
            files.append({"repository": "boyiwei/hal-harness", "commit": commit, "path": "agents/SWE-agent-v1.0", "url": f"https://github.com/boyiwei/hal-harness/tree/{commit}/agents/SWE-agent-v1.0", "gitlink_commit": sub_commit, "role": "gitlink", "git_blob_sha": None, "sha256": None, "content_verification": "parent_commit_tree_gitlink_verified", "gap": "A gitlink is a commit binding, not a file; its target sources are listed separately."})
            sub_repo = "https://github.com/boyiwei/SWE-agent"
            agent_lines = [[260, 380], [782, 858]] if commit.startswith("02a2500") else [[296, 417], [829, 905]]
            for path, line_ranges, symbols in [
                ("sweagent/agent/agents.py", agent_lines, ["cost_limit", "autosubmit", "error handling"]),
                (("config/250225_anthropic_filemap_simple_review.yaml" if commit.startswith("02a2500") else "config/benchmarks/250225_anthropic_filemap_simple_review.yaml"), [[71, 73]], ["per_instance_cost_limit", "total_cost_limit"]),
            ]:
                ext = file_record(sub_repo, sub_commit, path, "pinned_submodule_runtime", line_ranges, symbols, "external")
                files.append(ext)
        if kind == "taubench":
            pin = PINNED_EXTERNALS["tau"]
            for candidate_commit in pin["candidate_commits"]:
                for path, line_ranges, symbols in [
                    ("tau_bench/agents/tool_calling_agent.py", [[27, 40], [73, 73]], ["solve", "max_num_steps", "done"]),
                    ("tau_bench/envs/base.py", [[91, 120]], ["step", "actions.append", "done"]),
                ]:
                    ext = file_record(pin["repo"], candidate_commit, path, "candidate_tau_dependency_runtime", line_ranges, symbols, "external")
                    ext["resolved_for_each_run"] = "unknown"
                    files.append(ext)
        entries.append({
            "source_version_key": [original_repo, commit], "hal_commit": commit, "rule_scope": kind,
            "archive_repository_url_original": original_repo,
            "repository_normalized_for_links": normalized_repo,
            "bound_run_count": len(matching_runs), "run_commit_match": bool(matching_runs),
            "source_files": files,
        })
    # Check actual commit set. A new/unmapped code version is retained as unknown.
    observed = {(str(archive.get("git_info", {}).get("repository_url")) if isinstance(archive.get("git_info"), dict) else None, str(archive.get("git_info", {}).get("commit")) if isinstance(archive.get("git_info"), dict) else None) for archive in archive_values.values()}
    unregistered = sorted(([repo,commit] for repo,commit in observed if not _registered_source_pair(repo, commit)), key=lambda pair: (str(pair[0]),str(pair[1])))
    doc = {"schema_version": "hal-stopping-sources-v2", "entries": entries, "unregistered_source_versions": unregistered}
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return doc, entries


def _validate_inputs(data_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, str], dict[str, Any]]:
    manifest_path = data_root / "configs/hal_research_manifest.json"
    run_path = data_root / "data/derived/existing_runs/runs.jsonl"
    label_path = data_root / "data/derived/existing_runs/label_candidates.jsonl"
    summary_path = data_root / "data/derived/existing_runs/protocol_summary.json"
    baseline_path = Path(__file__).resolve().parents[1] / "reports/research_audit/current_evidence.json"
    for path in (manifest_path, run_path, label_path, summary_path, baseline_path):
        if not path.is_file():
            raise AuditError(f"missing required input: {path.name}")
    manifest = read_json(manifest_path)
    runs = read_jsonl(run_path)
    labels = read_jsonl(label_path)
    protocol = read_json(summary_path)
    baseline = read_json(baseline_path)
    input_paths = {"manifest": manifest_path, "runs.jsonl": run_path, "label_candidates.jsonl": label_path, "protocol_summary.json": summary_path}
    hashes = {name: sha256_file(path) for name, path in input_paths.items()}
    frozen = protocol.get("frozen_files", {})
    expected = {"runs.jsonl": frozen.get("runs.jsonl"), "label_candidates.jsonl": baseline.get("input_sha256", {}).get("label_candidates.jsonl")}
    for name, expected_hash in expected.items():
        if expected_hash and hashes[name] != expected_hash:
            raise AuditError(f"frozen derived input hash mismatch: {name}")
    if protocol.get("runs_sha256") != hashes["runs.jsonl"]:
        raise AuditError("protocol summary runs_sha256 does not match the frozen runs file")
    if baseline.get("source_manifest_sha256") != hashes["manifest"]:
        raise AuditError("public baseline source manifest hash does not match fixed manifest")
    _, grouped_labels = _validate_run_label_relations(runs, labels)
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, list) or len(manifest_files) != 17:
        raise AuditError("manifest does not contain the expected frozen 17 archives")
    for item in manifest_files:
        path = data_root / item["local_path"]
        if not path.is_file():
            raise AuditError(f"missing archive: {item.get('filename', '<unknown>')}")
        _verify_file_receipt(path, item.get("bytes"), item.get("sha256"), f"archive {item.get('filename', '<unknown>')}")
    return manifest, runs, labels, hashes, {"protocol": protocol, "baseline": baseline, "grouped_labels": grouped_labels, "paths": input_paths}


def build_index(data_root: Path, source_index_path: Path, private_output: Path, public_output: Path) -> dict[str, Any]:
    manifest, runs, labels, input_hashes, extra = _validate_inputs(data_root)
    read_archive = _archive_reader(data_root)
    manifest_by_hash = {item["sha256"]: item for item in manifest["files"]}
    runs_by_archive: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        if run.get("archive_sha256") not in manifest_by_hash:
            raise AuditError("run references an archive outside the fixed manifest")
        runs_by_archive[run["archive_sha256"]].append(run)
    archive_values: dict[str, dict[str, Any]] = {}
    archive_receipts = []
    for archive_hash, meta in sorted(manifest_by_hash.items()):
        archive_path = data_root / meta["local_path"]
        before = sha256_file(archive_path)
        raw = read_archive(archive_path)
        after = sha256_file(archive_path)
        if before != after or before != archive_hash:
            raise AuditError("archive changed while being read")
        archive_values[archive_hash] = raw
        archive_commit = raw.get("git_info", {}).get("commit") if isinstance(raw.get("git_info"), dict) else None
        for run in runs_by_archive.get(archive_hash, []):
            if run.get("code_commit") != archive_commit:
                raise AuditError("derived code_commit disagrees with raw archive")
            if run.get("source_run_id") != (raw.get("config", {}).get("run_id") if isinstance(raw.get("config"), dict) else None):
                raise AuditError("derived source_run_id disagrees with raw archive")
            if run.get("benchmark") != (raw.get("config", {}).get("benchmark_name") if isinstance(raw.get("config"), dict) else None):
                raise AuditError("derived benchmark disagrees with raw archive")
        archive_receipts.append({"path": meta["local_path"], "filename": meta["filename"], "sha256": archive_hash, "bytes": meta["bytes"], "archive_commit": archive_commit, "raw_json_members": ["raw_eval_results", "raw_logging_results", "config", "git_info"], "read_status": "verified_read_only"})
    sources, source_entries = _source_index(data_root, runs, source_index_path, archive_values)
    source_by_version = {(entry.get("archive_repository_url_original"), entry["hal_commit"]): entry for entry in source_entries}
    private_rows = []
    tau_action_counts: list[int] = []
    review_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    def add_review_example(kind: str, example: dict[str, Any], limit: int = 3) -> None:
        examples = review_examples[kind]
        if len(examples) < limit and example not in examples:
            examples.append(example)
    for run in sorted(runs, key=lambda row: row["episode_id"]):
        archive = archive_values[run["archive_sha256"]]
        task_evidence = _archive_task_evidence(archive, run)
        pointer, raw_record, join_status = task_evidence["raw_record_pointer"], task_evidence["raw_record"], task_evidence["join_status"]
        restrictions = _rules(run)
        raw_git = archive.get("git_info") if isinstance(archive.get("git_info"), dict) else {}
        source = source_by_version.get((raw_git.get("repository_url"), run.get("code_commit")))
        observations = list(task_evidence["observations"])
        for task_observation in observations:
            if task_observation.get("code") == "explicit_timeout_prefix":
                add_review_example("explicit_timeout", {"episode_id": run["episode_id"], "archive_sha256": run["archive_sha256"], "raw_record_pointer": task_observation["field_pointer"]}, limit=5)
            elif task_observation.get("code") == "eval_log_info":
                add_review_example("evaluation_log", {"episode_id": run["episode_id"], "archive_sha256": run["archive_sha256"], "raw_record_pointer": task_observation["field_pointer"]})
        config = archive.get("config") if isinstance(archive.get("config"), dict) else {}
        raw_args = config.get("agent_args") if isinstance(config.get("agent_args"), dict) else {}
        configuration_conflict = False
        for rule in restrictions:
            name = rule["name"]
            if name == "whole_run_token_cap":
                continue
            if name in raw_args:
                raw_value = raw_args[name]
                is_same = raw_value == rule["value"]
                observations.append({"layer": "configuration_rule", "code": "configuration_value_matched" if is_same else "configuration_value_conflict", "source_ref": "archive", "field_pointer": f"/config/agent_args/{_pointer_escape(name)}", "presence": _presence(raw_args, name), "interpretation_scope": f"configured {rule['scope']} rule ({rule['unit']}); activation not established", "private_summary": f"type={type(raw_value).__name__}"})
                configuration_conflict = configuration_conflict or not is_same
            else:
                observations.append({"layer": "configuration_rule", "code": "configuration_field_not_found_in_archive", "source_ref": "archive", "field_pointer": f"/config/agent_args/{_pointer_escape(name)}", "presence": "absent", "interpretation_scope": "derived restriction not verified in raw config"})
        if pointer and isinstance(raw_record, dict):
                # Only inspect named diagnostic/termination fields. Preserve values privately.
                for key in ("log_info", "error", "exception", "finish_reason", "stop_reason", "timeout", "taken_actions", "reward"):
                    if key in raw_record:
                        val = raw_record[key]
                        if run.get("benchmark") == "taubench_airline" and key == "taken_actions" and isinstance(val, list):
                            count = len(val)
                            tau_action_counts.append(count)
                            observations.append({"layer": "task_runtime_marker", "code": "tau_candidate_step_default_comparison", "source_ref": "archive", "field_pointer": f"/{pointer}/taken_actions", "presence": "present", "interpretation_scope": "99 observed action-list counts; candidate dependency default max_num_steps=30; actual dependency pin and stop activation unknown", "private_summary": f"action_count={count}; candidate_default=30"})
                            if count > 30:
                                add_review_example("tau_candidate_default_exceeded", {"episode_id": run["episode_id"], "archive_sha256": run["archive_sha256"], "raw_record_pointer": f"/{pointer}/taken_actions", "observed_action_count": count, "candidate_default": 30, "runtime_pin": "unknown"}, limit=3)
                        if key == "log_info":
                            observations.append({"layer": "evaluation_diagnostic", "code": "eval_log_info", "source_ref": "archive", "field_pointer": f"/{pointer}/{key}", "presence": _presence(raw_record, key), "interpretation_scope": "evaluation-only", "excerpt_internal": json.dumps(val, ensure_ascii=False)[:400]})
                            if val not in (None, "", [], {}):
                                add_review_example("evaluation_log", {"episode_id": run["episode_id"], "archive_sha256": run["archive_sha256"], "raw_record_pointer": f"/{pointer}/{key}"})
                        else:
                            observations.append({"layer": "evaluation_diagnostic" if key in {"error", "exception"} else "task_runtime_marker", "code": f"raw_{key}_observed", "source_ref": "archive", "field_pointer": f"/{pointer}/{key}", "presence": _presence(raw_record, key), "interpretation_scope": "field-specific; does not by itself establish censoring", "private_summary": f"type={type(val).__name__}; length={len(val) if isinstance(val,(str,list,dict)) else None}"})
                if run.get("benchmark") == "swebench_verified_mini":
                    observations.append({"layer": "evaluation_diagnostic", "code": "swe_result_membership", "source_ref": "archive", "field_pointer": f"/{pointer}", "presence": "present", "interpretation_scope": "final evaluator membership; not task stopping reason", "private_summary": ",".join(raw_record.get("membership_fields", []))})
        elif pointer and run.get("benchmark") == "scicode":
            observations.append({"layer": "evaluation_diagnostic", "code": "scicode_details_entry", "source_ref": "archive", "field_pointer": f"/{pointer}", "presence": _presence({"value": raw_record}, "value"), "interpretation_scope": "final evaluator details; evaluation timeout is not agent runtime cutoff", "private_summary": f"type={type(raw_record).__name__}; length={len(raw_record) if isinstance(raw_record,(str,list,dict)) else None}"})
        elif join_status != "exact_task_key":
            observations.append({"layer": "task_runtime_marker", "code": join_status, "source_ref": "archive", "field_pointer": "/raw_eval_results", "presence": "uninspected", "interpretation_scope": "raw task join not established"})
        # Evaluator diagnostics come from the evaluator channel, never from the
        # agent-output marker channel. Both joins use the exact task key.
        observations.extend(_raw_call_evidence(archive, run))
        limit_conflict = None
        if isinstance(raw_record, dict) and isinstance(raw_record.get("taken_actions"), list):
            configured_steps = next((rule["value"] for rule in restrictions if rule["name"] == "max_steps" and isinstance(rule["value"], (int, float))), None)
            limit_conflict = _limit_consistency(configured_steps, len(raw_record["taken_actions"]))
            if limit_conflict["status"] == "conflicting":
                observations.append({"layer": "task_runtime_marker", "code": "observed_action_count_exceeds_configured_step_limit", "source_ref": "archive", "field_pointer": f"/{pointer}/taken_actions", "presence": "present", "interpretation_scope": "count/unit mapping requires source review", "private_summary": f"action_count={len(raw_record['taken_actions'])}; configured_step_limit={configured_steps}"})
                add_review_example("source_runtime_conflict", {"episode_id": run["episode_id"], "archive_sha256": run["archive_sha256"], "raw_record_pointer": f"/{pointer}/taken_actions"})
        if run.get("stop_reason") in {"explicit_timeout", "explicit_error"} and not any(o.get("code") in {"explicit_timeout_prefix", "explicit_error_prefix"} for o in observations):
            # Keep the legacy derived fact visible, while flagging failure to reproduce its raw join.
            observations.append({"layer": "task_runtime_marker", "code": run["stop_reason"], "source_ref": "derived_runs/stop_reason", "field_pointer": "/stop_reason", "presence": "present", "interpretation_scope": "legacy parser result; raw marker not rejoined"})
        labels_for_episode = extra["grouped_labels"][run["episode_id"]]
        in_b = _b_failure_candidate(labels_for_episode, run.get("benchmark"))
        # B candidate source data does not contain any scientific censor decision.
        assessment = task_evidence["identification_assessment"]
        source_verified = bool(source and any(item.get("content_verification") == "local_receipt_sha256_verified" for item in source.get("source_files", [])))
        consistency = "conflicting" if configuration_conflict or (limit_conflict and limit_conflict["status"] == "conflicting") else "unknown"
        if source and not source_verified:
            add_review_example("unverified_source_version", {"archive_sha256": run["archive_sha256"], "code_commit": run.get("code_commit"), "source_index_commit": source["hal_commit"]})
        evidence_row = {
            "schema_version": SCHEMA_VERSION, "episode_id": run["episode_id"], "benchmark": run["benchmark"], "scaffold": run["scaffold"], "config_id": run["config_id"],
            "archive_sha256": run["archive_sha256"], "code_commit": run.get("code_commit"),
            "raw_record_pointer": f"/{pointer}" if pointer else None, "raw_join_status": join_status,
            "in_B_failure_subset": in_b, "configured_rules": restrictions, "observations": observations,
            "task_termination": {**task_evidence["task_termination"], "observed_category": "explicit_timeout_marker" if any(o.get("code") == "explicit_timeout_prefix" for o in observations) else ("explicit_error_marker" if any(o.get("code") == "explicit_error_prefix" for o in observations) else "unknown"), "evidence_refs": [o["field_pointer"] for o in observations if o["layer"] == "task_runtime_marker"], "reason": "A final marker, result/diagnostic or call finish reason does not identify the actual task stopping branch."},
            "source_runtime_consistency": {"status": consistency, "reason": "A source receipt can establish committed source bytes, but archive metadata alone does not prove the executing runtime matched those bytes."},
            "identification_assessment": assessment,
            "limitations": ["No whole-run token cap verified.", "Configuration is not evidence of rule activation.", "Final evaluation outcome is not a task termination event."],
            "approved_for_training": False,
        }
        if not evidence_row["task_termination"]["evidence_refs"]:
            add_review_example("termination_unknown", {
                "episode_id": run["episode_id"],
                "archive_sha256": run["archive_sha256"],
                "raw_record_pointer": evidence_row["raw_record_pointer"],
                "reason": "exact raw task result exists but does not establish the stopping branch",
            })
        private_rows.append(evidence_row)
    # Exact one-row-per-episode and cohort checks.
    if len(private_rows) != len(runs) or len({row["episode_id"] for row in private_rows}) != len(runs):
        raise AuditError("internal index does not preserve one row per episode")
    for name, path in extra["paths"].items():
        if sha256_file(path) != input_hashes[name]:
            raise AuditError(f"frozen input changed during read: {name}")
    b_count = sum(row["in_B_failure_subset"] for row in private_rows)
    private_output.mkdir(parents=True, exist_ok=True)
    internal_path = private_output / "run_evidence.internal.jsonl"
    internal_payload, internal_hash = _serialize_evidence_rows(private_rows)
    internal_path.write_text(internal_payload, encoding="utf-8")
    # Public aggregate is explicit field construction; never serialize internal rows.
    dimensions = defaultdict(Counter)
    totals = Counter()
    coverage = Counter()
    b_dimensions = defaultdict(Counter)
    evidence_coverage = defaultdict(Counter)
    b_evidence_coverage = defaultdict(Counter)
    rule_coverage = defaultdict(Counter)
    b_rule_coverage = defaultdict(Counter)
    b_raw_markers = Counter()
    all_raw_markers = Counter()
    identification = defaultdict(Counter)
    for row in private_rows:
        key = (row["benchmark"], row["scaffold"], row.get("code_commit") or "unknown")
        totals["runs"] += 1
        if row["in_B_failure_subset"]:
            totals["B_failure_subset"] += 1
        dimensions[key]["runs"] += 1
        b_dimensions[key]["runs"] += int(row["in_B_failure_subset"])
        coverage[row["raw_join_status"]] += 1
        for observation in row["observations"]:
            evidence_coverage[observation["layer"]][observation["code"]] += 1
            if row["in_B_failure_subset"]:
                b_evidence_coverage[observation["layer"]][observation["code"]] += 1
            if observation["code"] in {"explicit_timeout_prefix", "explicit_error_prefix"}:
                all_raw_markers[observation["code"]] += 1
                if row["in_B_failure_subset"]:
                    b_raw_markers[observation["code"]] += 1
        for rule in row["configured_rules"]:
            layer = f"{rule['scope']}:{rule['unit']}:{rule['name']}"
            rule_coverage[layer][rule["presence"]] += 1
            if row["in_B_failure_subset"]:
                b_rule_coverage[layer][rule["presence"]] += 1
        for name, judgment in row["identification_assessment"].items():
            identification[name][judgment["status"]] += 1
        if row["in_B_failure_subset"]:
            b_dimensions[key]["raw_joined"] += int(row["raw_join_status"] == "exact_task_key")
            b_dimensions[key]["task_termination_unknown"] += int(row["task_termination"]["status"] == "unknown")
    public = {
        "schema_version": "hal-stopping-summary-v1", "tool_version": TOOL_VERSION,
        "scope": "aggregate evidence indexing only; no scientific identification established",
        "input_sha256": dict(sorted(input_hashes.items())), "archive_count": len(manifest["files"]),
        "run_count": len(private_rows), "B_failure_subset_count": b_count,
            "coverage": {"raw_task_join_status": dict(sorted(coverage.items())), "source_sha256_verified_files": sum(item.get("content_verification") == "local_receipt_sha256_verified" for entry in source_entries for item in entry.get("source_files", [])), "source_git_blob_pinned_files": sum(bool(item.get("git_blob_sha")) for entry in source_entries for item in entry.get("source_files", [])), "source_files_total": sum(len(entry.get("source_files", [])) for entry in source_entries), "source_versions_expected": len(source_entries), "unregistered_source_version_count": len(sources["unregistered_source_versions"])},
        "evidence_coverage_all_runs": {layer: dict(sorted(counts.items())) for layer,counts in sorted(evidence_coverage.items())},
        "evidence_coverage_B_failure_subset": {layer: dict(sorted(counts.items())) for layer,counts in sorted(b_evidence_coverage.items())},
        "evidence_presence_all_runs": _aggregate_observation_presence(private_rows),
        "evidence_presence_B_failure_subset": _aggregate_observation_presence(private_rows, b_subset=True),
        "configured_rule_presence_all_runs": {name: dict(sorted(counts.items())) for name,counts in sorted(rule_coverage.items())},
        "configured_rule_presence_B_failure_subset": {name: dict(sorted(counts.items())) for name,counts in sorted(b_rule_coverage.items())},
        "explicit_raw_markers_all_runs": dict(sorted(all_raw_markers.items())),
        "explicit_raw_markers_B_failure_subset": dict(sorted(b_raw_markers.items())),
        "tau_candidate_step_default_diagnostic": {
            "runs_with_observed_taken_actions": len(tau_action_counts),
            "at_or_below_candidate_default_30": sum(count <= 30 for count in tau_action_counts),
            "equal_candidate_default_30": sum(count == 30 for count in tau_action_counts),
            "above_candidate_default_30": sum(count > 30 for count in tau_action_counts),
            "observed_action_count_min": min(tau_action_counts) if tau_action_counts else None,
            "observed_action_count_median": sorted(tau_action_counts)[len(tau_action_counts) // 2] if len(tau_action_counts) % 2 else (sum(sorted(tau_action_counts)[len(tau_action_counts) // 2 - 1:len(tau_action_counts) // 2 + 1]) / 2 if tau_action_counts else None),
            "observed_action_count_max": max(tau_action_counts) if tau_action_counts else None,
            "interpretation": "candidate source/configuration conflict only; runtime dependency pin and limit activation are unknown, so this is not a censoring determination",
            "runtime_pin": "unknown",
        },
        "strata": [{"benchmark": b, "scaffold": s, "code_commit": c, "runs": counts["runs"], "B_failure_subset": b_dimensions[(b,s,c)]["runs"], "B_failure_raw_joined": b_dimensions[(b,s,c)]["raw_joined"], "B_failure_task_termination_unknown": b_dimensions[(b,s,c)]["task_termination_unknown"]} for (b,s,c),counts in sorted(dimensions.items())],
        "identification_coverage": {name: dict(sorted(counts.items())) for name,counts in sorted(identification.items())},
        "known_gaps": ["Raw runtime marker association is exact-keyed but does not establish which agent branch ended a task.", "Historical source bytes are only marked verified when a local pinned receipt matches; missing receipts remain unknown.", "Per-call finish reasons, dollar/step limits, evaluation diagnostics, and task termination are distinct evidence layers."],
        "training_approved_rows": 0, "scientific_contribution_established": False,
        "evidence_content_sha256": internal_hash,
    }
    _validate_public_payload(public)
    public_output.parent.mkdir(parents=True, exist_ok=True)
    public_output.write_text(json.dumps(public, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    receipt = {
        "schema_version": "hal-stopping-receipts-v1", "tool_version": TOOL_VERSION,
        "inputs": [{"path": name, "bytes": path.stat().st_size, "sha256": input_hashes[name]} for name,path in sorted(extra["paths"].items())],
        "archives": archive_receipts, "sources_registry_sha256": sha256_file(source_index_path),
        "evidence_content_sha256": internal_hash,
        "commands": [["python3", "tools/audit_stopping_evidence.py", "--data-root", ".", "--source-index", "configs/hal_stopping_sources.json", "--private-output", "data/derived/stopping_audit", "--public-output", "reports/research_audit/stopping_evidence_summary.json"]], "exit_status": 0,
        "note": "Paths are relative to --data-root; no row-level values included in this receipt.",
    }
    (private_output / "source_receipts.internal.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (private_output / "review_examples.internal.json").write_text(json.dumps(review_examples, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return public


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--source-index", required=True, type=Path)
    parser.add_argument("--private-output", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = build_index(args.data_root, args.source_index, args.private_output, args.public_output)
    except (AuditError, OSError, zipfile.BadZipFile, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"audit input failure: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "evidence_index_written", "run_count": report["run_count"], "B_failure_subset_count": report["B_failure_subset_count"], "evidence_content_sha256": report["evidence_content_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
