import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

from prepare_success_endpoint import build_fold_payload, qualify_run


def synthetic_row(episode_id, task_id, success=True):
    run = {
        'episode_id': episode_id,
        'benchmark': 'scienceagentbench',
        'canonical_task_id': task_id,
        'config_id': 'cfg_a',
        'source_run_id': 'source_run',
        'archive_sha256': 'archive-sha',
        'source_url': 'https://example.invalid/source',
        'success': success,
        'outcome_status': 'scored' if success is not None else 'evaluation_error',
        'actor_total_tokens_observed': 12 if success is True else None,
        'quality_flags': [],
        'usage_complete_in_logged_calls': True,
        'initial_input_status': 'observed_initial',
        'stop_reason': None,
        'result_raw': None,
    }
    initial = {
        'episode_id': episode_id,
        'benchmark': 'scienceagentbench',
        'canonical_task_id': task_id,
        'config_id': 'cfg_a',
        'initial_input_status': 'observed_initial',
        'source_call_id': 'source-call',
        'task_text': 'synthetic task prompt',
    }
    feature = {
        'episode_id': episode_id,
        'benchmark': 'scienceagentbench',
        'task_group': task_id,
        'config_id': 'cfg_a',
        'task_text': initial['task_text'],
        'task_text_chars': len(initial['task_text']),
        'model': 'synthetic-model',
        'scaffold': 'synthetic-scaffold',
        'reasoning_effort': 'medium',
        'max_tokens_per_call': 100,
        'max_steps': 8,
    }
    config = {
        'benchmark': 'scienceagentbench',
        'model': 'synthetic-model',
        'scaffold': 'synthetic-scaffold',
        'reasoning_effort': 'medium',
        'max_tokens_per_call': 100,
        'max_steps': 8,
    }
    return run, initial, feature, config


class SuccessEndpointTests(unittest.TestCase):
    def test_eligibility_requires_success_measurement_and_verified_initial_input(self):
        run, initial, feature, config = synthetic_row('train-ok', 'task-train')
        self.assertEqual(qualify_run(run, initial, feature, config, {'archive-sha'}), [])

        failed, failed_input, failed_feature, failed_config = synthetic_row('failed', 'task-fail', False)
        self.assertIn('not_source_success', qualify_run(
            failed, failed_input, failed_feature, failed_config, {'archive-sha'}))

        bad_usage, bad_input, bad_feature, bad_config = synthetic_row('bad-usage', 'task-bad')
        bad_usage['actor_total_tokens_observed'] = None
        self.assertIn('invalid_actor_total', qualify_run(
            bad_usage, bad_input, bad_feature, bad_config, {'archive-sha'}))

        bad_input['initial_input_status'] = 'partial_step_input'
        self.assertIn('unverified_initial_input', qualify_run(
            run, bad_input, feature, config, {'archive-sha'}))

    def test_fold_payload_keeps_test_targets_and_task_groups_out_of_trainer(self):
        train_ok = synthetic_row('train-ok', 'task-train')
        train_bad = synthetic_row('train-bad', 'task-train-2', False)
        test_ok = synthetic_row('test-ok', 'task-test')
        test_bad = synthetic_row('test-bad', 'task-test-2', False)
        rows = [train_ok, train_bad, test_ok, test_bad]
        runs = [x[0] for x in rows]
        inputs = {x[0]['episode_id']: x[1] for x in rows}
        features = {x[0]['episode_id']: x[2] for x in rows}
        configs = {'cfg_a': train_ok[3]}
        groups = {
            x[0]['episode_id']: {
                'task_group': x[0]['canonical_task_id'],
                'family_group': x[0]['canonical_task_id'],
            }
            for x in rows
        }
        fold = {
            'train_ids': ['train-ok', 'train-bad'],
            'test_ids': ['test-ok', 'test-bad'],
            'inner': [{'inner_fold': 0, 'train_ids': ['train-ok'], 'validation_ids': ['train-bad']}],
        }
        payload = build_fold_payload('scienceagentbench', runs, inputs, features,
                                     configs, groups, fold)

        self.assertEqual([x['episode_id'] for x in payload['train_labels']], ['train-ok'])
        self.assertEqual({x['episode_id'] for x in payload['test_features']}, {'test-ok', 'test-bad'})
        self.assertTrue(all('actor_total_tokens_observed' not in x and 'success' not in x
                            for x in payload['test_features']))
        self.assertTrue(all('task_group' not in x for x in payload['train_features']))
        private = {x['episode_id']: x for x in payload['evaluator_facts']}
        self.assertEqual(private['test-ok']['actor_total_tokens_observed'], 12)
        self.assertIsNone(private['test-bad']['actor_total_tokens_observed'])
        self.assertEqual(private['test-ok']['task_group'], 'task-test')


if __name__ == '__main__':
    unittest.main()
