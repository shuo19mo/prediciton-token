import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/audit_stopping_evidence.py"
SPEC = importlib.util.spec_from_file_location("audit_stopping_evidence", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class StoppingEvidenceSemanticsTests(unittest.TestCase):
    def test_source_registration_requires_exact_archive_repository_and_commit_pair(self):
        commit = "23fc5665d6804fa72240f479e38f73fb53600002"
        origin = audit.EXPECTED_REPOSITORY_BY_COMMIT[commit]
        self.assertTrue(audit._registered_source_pair(origin, commit))
        self.assertFalse(audit._registered_source_pair("https://github.com/princeton-pli/hal-harness.git", commit))
        self.assertFalse(audit._registered_source_pair(origin, "unknown-commit"))

    def test_call_token_limit_is_not_run_token_cap(self):
        rules = audit._rules({"historical_restrictions": {"max_tokens": 4096}, "whole_run_token_cap": None})
        by_name = {rule["name"]: rule for rule in rules}
        self.assertEqual((by_name["max_tokens"]["scope"], by_name["max_tokens"]["unit"]), ("per_call", "tokens"))
        self.assertIsNone(by_name["whole_run_token_cap"]["value"])

    def test_usd_and_step_limits_keep_their_units(self):
        rules = audit._rules({"historical_restrictions": {"budget": 1.0, "max_steps": 40}})
        got = {rule["name"]: (rule["scope"], rule["unit"]) for rule in rules}
        self.assertEqual(got["budget"], ("run", "USD_or_unspecified_currency"))
        self.assertEqual(got["max_steps"], ("run", "steps"))

    def test_eval_diagnostic_is_not_task_termination(self):
        diag = {"log_info": "evaluation failed"}
        obs = {"layer": "evaluation_diagnostic", "code": "eval_log_info", "presence": audit._presence(diag, "log_info")}
        self.assertEqual(obs["presence"], "present")
        self.assertEqual(audit._identification_unknown("diagnostic only")["T_gt_U"]["status"], "unknown")

    def test_explicit_timeout_does_not_support_identification_claims(self):
        result = audit._identification_unknown("timeout marker only")
        self.assertEqual({item["status"] for item in result.values()}, {"unknown"})
        self.assertIn("T_gt_U", result)

    def test_call_finish_reason_stays_call_level(self):
        archive = {"raw_logging_results": [{"attributes": {"weave_task_id": "task-a"}, "output": {"finish_reason": "length"}}]}
        run = {"task_id": "task-a"}
        observations = audit._raw_call_evidence(archive, run)
        self.assertTrue(any(item["layer"] == "call_finish_reason" and item["code"] == "finish_reason_observed" for item in observations))
        self.assertTrue(all(item["interpretation_scope"] == "call-level" for item in observations))

    def test_missing_empty_and_uninspected_remain_distinct(self):
        self.assertEqual(audit._presence({}, "x"), "absent")
        self.assertEqual(audit._presence({"x": ""}, "x"), "empty")
        self.assertEqual(audit._presence({}, "x", inspected=False), "uninspected")
        self.assertIsNone(audit._rules({"historical_restrictions": {"max_tokens": None}})[0]["value"])

    def test_multiple_protocol_rows_do_not_duplicate_episode_and_bad_b_join_fails(self):
        rows = [
            {"protocol": "A", "benchmark": "b", "event": 0, "included": False},
            {"protocol": "B", "benchmark": "b", "event": 0, "included": True},
        ]
        self.assertTrue(audit._b_failure_candidate(rows, "b"))
        with self.assertRaises(audit.AuditError):
            audit._b_failure_candidate(rows + [rows[1]], "b")
        with self.assertRaises(audit.AuditError):
            audit._b_failure_candidate(rows, "different-benchmark")

    def test_exact_task_join_keeps_agent_output_and_evaluator_separate(self):
        archive = {"raw_eval_results": {
            "agent_output": {"task-a": "TIMEOUT after fixture"},
            "eval_result": {"task-a": {"log_info": "fixture diagnostic"}},
        }}
        pointer, record, status = audit._archive_record_locator(archive, {"benchmark": "scienceagentbench", "task_id": "task-a"})
        self.assertEqual(status, "exact_task_key")
        self.assertEqual(pointer, "raw_eval_results/agent_output/task-a")
        self.assertEqual(record, "TIMEOUT after fixture")
        self.assertNotIn("log_info", record)

    def test_step_action_count_conflict_is_retained_not_resolved(self):
        mismatch = audit._limit_consistency(30, 34)
        self.assertEqual(mismatch["status"], "conflicting")
        self.assertIn("unit/runtime mapping", mismatch["reason"])
        self.assertEqual(audit._limit_consistency(30, 20)["status"], "unknown")

    def test_public_whitelist_guard_rejects_private_ids_text_and_local_paths(self):
        audit._validate_public_payload({"runs": 2, "summary": "safe aggregate", "url": "https://example.test/source"})
        for payload in (
            {"episode_id": "private"},
            {"details": [{"prompt": "secret"}]},
            {"file": "/Users/example/work/data.json"},
        ):
            with self.assertRaises(audit.AuditError):
                audit._validate_public_payload(payload)

    def test_deterministic_content_hash_ignores_map_insertion_order(self):
        self.assertEqual(audit.stable_hash({"a": 1, "b": 2}), audit.stable_hash({"b": 2, "a": 1}))
        self.assertNotEqual(audit.stable_hash({"a": 1}), audit.stable_hash({"a": 2}))


if __name__ == "__main__":
    unittest.main()
