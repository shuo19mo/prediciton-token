"""Recompute aggregate evidence from existing HAL outputs; no training or benchmark execution."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    data = ROOT / 'data/derived/existing_runs'
    rows = [json.loads(line) for line in (data / 'runs.jsonl').open()]
    labels = [json.loads(line) for line in (data / 'label_candidates.jsonl').open()]
    manifest = json.loads((ROOT / 'configs/hal_research_manifest.json').read_text())
    frozen = json.loads((data / 'protocol_summary.json').read_text())
    errors = []
    for source in manifest['files']:
        path = ROOT / source['local_path']
        if not path.is_file() or path.stat().st_size != source['bytes'] or sha(path) != source['sha256']:
            errors.append('Source absent or drifted: ' + source['filename'])
    for name, expected in frozen['frozen_files'].items():
        if sha(data / name) != expected:
            errors.append('Derived file drifted: ' + name)
    lookup = {r['episode_id']: r for r in rows}
    if len(lookup) != len(rows):
        errors.append('Duplicate episode IDs')
    for label in labels:
        if label['episode_id'] not in lookup:
            errors.append('Unmatched candidate')
    counts = []
    for benchmark in sorted({r['benchmark'] for r in rows}):
        rr = [r for r in rows if r['benchmark'] == benchmark]
        a = [x for x in labels if x['benchmark'] == benchmark and x['protocol'] == 'A' and x['included']]
        b = [x for x in labels if x['benchmark'] == benchmark and x['protocol'] == 'B' and x['included']]
        failures = [lookup[x['episode_id']] for x in b if x['event'] == 0]
        counts.append({'benchmark': benchmark, 'runs': len(rr),
            'task_identities': len({r['canonical_task_id'] for r in rr}),
            'observed_success': sum(r['success'] is True for r in rr),
            'observed_failure': sum(r['success'] is False for r in rr),
            'unknown_outcome': sum(r['success'] is None for r in rr),
            'A_candidates': len(a), 'A_failure_candidates': sum(x['event'] == 0 for x in a),
            'A_success_tasks': len({x['task_group'] for x in a if x['event'] == 1}),
            'B_failure_candidates': len(failures),
            'B_failure_parsed_stops': dict(sorted(Counter(r['stop_reason'] or 'unknown' for r in failures).items())),
            'B_failure_has_eval_log': sum(r['has_eval_log'] for r in failures),
            'B_failure_restriction_fields': dict(sorted(Counter(k for r in failures for k in r['historical_restrictions']).items()))})
    result = {'scope': 'aggregate_source_and_derived_fact_recheck_not_identification',
        'sources_checked': len(manifest['files']), 'derived_frozen_files_checked': len(frozen['frozen_files']),
        'runs': len(rows), 'task_identities': len({r['canonical_task_id'] for r in rows}),
        'whole_run_token_cap_unknown': sum(r['whole_run_token_cap'] is None for r in rows),
        'training_approved_rows': sum(x['approved_for_training'] for x in labels),
        'benchmarks': counts, 'source_manifest_sha256': sha(ROOT / 'configs/hal_research_manifest.json'),
        'input_sha256': {name: sha(data / name) for name in ['runs.jsonl', 'label_candidates.jsonl', 'protocol_summary.json']},
        'scientific_contribution_established': False, 'errors': errors,
        'status': 'pass_fact_recheck_only' if not errors else 'fail'}
    output = ROOT / 'reports/research_audit/current_evidence.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
