"""Check interruption recovery and duplicate prevention without contacting GitHub."""
import base64
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tracker', ROOT / 'tools/manage_research_tracker.py')
tracker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tracker)


class Response(io.BytesIO):
    def __init__(self, data):
        super().__init__(json.dumps(data).encode())


class TrackerTests(unittest.TestCase):
    def test_resume_preserves_manual_updates_and_does_not_duplicate(self):
        payload = json.loads((ROOT / 'configs/github_research_bootstrap.json').read_text())
        payload['operations'] = [{'id': 'test-acceptance', 'issue': 'audit',
            'body': 'Verified {{commit}}', 'patch': {'state': 'closed'}}]
        state = {'milestones': [], 'issues': [], 'labels': [], 'comments': {}}
        fail_once = [True]

        def fake(request, timeout):
            path = request.full_url.split('/prediciton-token', 1)[1].split('?', 1)[0]
            method = request.method
            body = json.loads(request.data) if request.data else None
            if path.startswith('/contents/'):
                return Response({'content': base64.b64encode(json.dumps(payload).encode()).decode()})
            parts = path.strip('/').split('/')
            if len(parts) == 1:
                collection = state[parts[0]]
                if method == 'GET':
                    return Response(copy.deepcopy(collection))
                row = copy.deepcopy(body)
                row.update(number=len(collection) + 1, state='open')
                collection.append(row)
                if parts[0] == 'issues':
                    state['comments'][row['number']] = []
                    if len(collection) == 3 and fail_once[0]:
                        fail_once[0] = False
                        raise RuntimeError('Simulated lost response after creation')
                return Response(row)
            number = int(parts[1])
            if len(parts) == 3:
                collection = state['comments'][number]
                if method == 'POST':
                    collection.append(body)
                    return Response(body)
                return Response(copy.deepcopy(collection))
            row = state['issues'][number - 1]
            row.update(body)
            return Response(row)

        env = {'GITHUB_REPOSITORY': 'shuo19mo/prediciton-token',
               'GITHUB_SHA': 'test-commit', 'GH_TOKEN': 'not-a-real-token'}
        with patch.dict(os.environ, env, clear=True), patch('urllib.request.urlopen', fake), patch('sys.stdout', io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'lost response'):
                tracker.main()
            tracker.main()
            self.assertEqual(len(state['milestones']), 7)
            self.assertEqual(len(state['issues']), 10)
            audit = next(x for x in state['issues'] if '<!-- research-tracker:audit -->' in x['body'])
            self.assertEqual(audit['state'], 'closed')
            self.assertNotIn('{{issue:', ''.join(x['body'] for x in state['issues']))
            audit['state'] = 'open'
            audit['body'] += '\nManual follow-up that must survive.'
            tracker.main()
            self.assertEqual(audit['state'], 'open')
            self.assertTrue(audit['body'].endswith('Manual follow-up that must survive.'))
            self.assertEqual(len(state['comments'][audit['number']]), 1)
            self.assertEqual(len(state['issues']), 10)


if __name__ == '__main__':
    unittest.main()
