"""Apply reviewed tracker setup/operations to this repository only; never reads research data."""
import base64
import json
import os
import re
import urllib.request
from pathlib import Path


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    if repo != 'shuo19mo/prediciton-token':
        raise SystemExit('Repository does not match the authorized destination')
    commit = os.environ['GITHUB_SHA']
    token = os.environ['GH_TOKEN']
    prefix = 'https://api.github.com/repos/' + repo

    def api(path, method='GET', body=None):
        request = urllib.request.Request(prefix + path,
            data=None if body is None else json.dumps(body).encode(), method=method,
            headers={'Authorization': 'Bearer ' + token,
                     'Accept': 'application/vnd.github+json', 'User-Agent': 'research-tracker',
                     'Content-Type': 'application/json', 'X-GitHub-Api-Version': '2022-11-28'})
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)

    def pages(path):
        rows = []
        for page in range(1, 101):
            batch = api(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')
            rows.extend(batch)
            if len(batch) < 100:
                return rows
        raise RuntimeError('Pagination limit reached; no mutation attempted for this collection')

    if os.environ.get('TRACKER_MODE') == 'serial_replan':
        apply_serial_replan(api, pages, repo, commit)
        return
    raw = api('/contents/configs/github_research_bootstrap.json?ref=' + commit)
    spec = json.loads(base64.b64decode(raw['content']))
    if spec['repository'] != repo:
        raise SystemExit('Payload repository mismatch')
    milestones = pages('/milestones?state=all')
    issues = [i for i in pages('/issues?state=all') if 'pull_request' not in i]
    label_rows = pages('/labels')
    known_labels = {x['name'] for x in label_rows}
    colors = {'literature': 'bfd4f2', 'data': '0075ca', 'method': 'd4c5f9',
              'experiment': 'fbca04', 'review': '0e8a16', 'blocked': 'b60205',
              'needs-training': 'd93f0b', 'in-progress': '1d76db'}
    for name, color in colors.items():
        if name not in known_labels:
            api('/labels', 'POST', {'name': name, 'color': color,
                'description': 'Research work type or execution state: ' + name})
    milestone_ids = {}
    for m in spec['milestones']:
        matches = [x for x in milestones if x['title'] == m['title']]
        if len(matches) > 1:
            raise RuntimeError('Duplicate milestone title: ' + m['title'])
        item = matches[0] if matches else api('/milestones', 'POST',
                   {'title': m['title'], 'description': m['description'], 'state': 'open'})
        milestone_ids[m['key']] = item['number']

    issue_ids, created = {}, set()
    def marker(key):
        return '<!-- research-tracker:' + key + ' -->'

    # First allocate stable identities, then resolve dependency links.
    for i in spec['issues']:
        matches = [x for x in issues if marker(i['key']) in (x.get('body') or '') or x['title'] == i['title']]
        if len(matches) > 1:
            raise RuntimeError('Duplicate issue identity: ' + i['key'])
        if matches:
            item = matches[0]
        else:
            item = api('/issues', 'POST', {'title': i['title'],
                'body': marker(i['key']) + '\n' + i['body'], 'labels': i['labels'],
                'milestone': milestone_ids[i['milestone']]})
            created.add(i['key'])
        issue_ids[i['key']] = item['number']

    def resolve(text):
        text = text.replace('{{commit}}', commit)
        return re.sub(r'\{\{issue:([^}]+)\}\}',
                      lambda m: 'https://github.com/' + repo + '/issues/' + str(issue_ids[m[1]]), text)

    for i in spec['issues']:
        old = next((x for x in issues if x['number'] == issue_ids[i['key']]), None)
        # Preserve ongoing discussion and manual edits on subsequent executions.
        if i['key'] in created or (old and '{{issue:' in (old.get('body') or '')):
            api('/issues/' + str(issue_ids[i['key']]), 'PATCH',
                {'body': marker(i['key']) + '\n' + resolve(i['body'])})

    for operation in spec.get('operations', []):
        number = issue_ids[operation['issue']]
        comment_marker = '<!-- research-operation:' + operation['id'] + ' -->'
        comments = pages(f'/issues/{number}/comments')
        if any(comment_marker in c['body'] for c in comments):
            continue
        patch = operation.get('patch')
        if patch:
            if set(patch) - {'state', 'state_reason', 'labels', 'body'}:
                raise ValueError('Unsupported patch field')
            patch = {k: resolve(v) if isinstance(v, str) else v for k, v in patch.items()}
            api(f'/issues/{number}', 'PATCH', patch)
        api(f'/issues/{number}/comments', 'POST',
            {'body': comment_marker + '\n' + resolve(operation['body'])})
    output = {'commit': commit, 'milestones': milestone_ids, 'issues': issue_ids}
    print(json.dumps(output, ensure_ascii=False))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with Path(summary).open('a') as stream:
            stream.write('Research tracker applied at `' + commit + '`.\n\n')
            for key, number in issue_ids.items():
                stream.write(f'- {key}: https://github.com/{repo}/issues/{number}\n')


def apply_serial_replan(api, pages, repo, commit):
    """Close only known premature placeholders and leave one active issue."""
    raw = api('/contents/configs/github_replan.json?ref=' + commit)
    spec = json.loads(base64.b64decode(raw['content']))
    if spec.get('mode') != 'serial_replan' or spec.get('repository') != repo:
        raise SystemExit('Expected an explicit serial-replan payload for this repository')
    milestones = pages('/milestones?state=all')
    issues = [x for x in pages('/issues?state=all') if 'pull_request' not in x]
    by_number = {x['number']: x for x in issues}
    by_milestone = {x['number']: x for x in milestones}
    if len(by_number) != len(issues):
        raise RuntimeError('Duplicate issue IDs in GitHub response')
    completed = spec['completed_issue']
    if completed['number'] not in by_number or by_number[completed['number']]['title'] != completed['title'] or by_number[completed['number']]['state'] != 'closed':
        raise RuntimeError('The accepted fact-audit issue changed; refusing to replan')
    active = spec['active_issue']
    if active['number'] not in by_number or by_number[active['number']]['title'] != active['title'] or by_number[active['number']]['state'] != 'open':
        raise RuntimeError('The current mechanism issue changed; refusing to replan')
    for milestone in spec['milestones']:
        existing = by_milestone.get(milestone['number'])
        if not existing or existing['title'] != milestone['title'] or existing['state'] != 'open':
            raise RuntimeError('A research milestone changed; refusing to replan')
    for retired in spec['retire_issues']:
        existing = by_number.get(retired['number'])
        already_retired_title = '撤销预建（本阶段进入时再创建） · ' + retired['title']
        if not existing or not (
                (existing['state'] == 'open' and existing['title'] == retired['title']) or
                (existing['state'] == 'closed' and existing['title'] == already_retired_title and
                 existing.get('state_reason') == 'not_planned')):
            raise RuntimeError('A planned issue changed; refusing to retire it: ' + str(retired['number']))
    expected_open = {active['number']} | {x['number'] for x in spec['retire_issues']}
    actual_open = {x['number'] for x in issues if x['state'] == 'open'}
    if actual_open != expected_open:
        raise RuntimeError('Open issue set changed; refusing to leave multiple active tasks')

    for milestone in spec['milestones']:
        api('/milestones/' + str(milestone['number']), 'PATCH',
            {'description': milestone['description']})
    api('/issues/' + str(active['number']), 'PATCH',
        {'body': active['body'], 'labels': active['labels'],
         'milestone': 1, 'state': 'open'})
    for retired in spec['retire_issues']:
        number = retired['number']
        existing = by_number[number]
        if existing['state'] == 'open':
            title = '撤销预建（本阶段进入时再创建） · ' + retired['title']
            note = '> 状态：2026-09-28顺序重排时撤销的阶段占位issue，GitHub关闭原因为 `not_planned`。该任务尚未开始、也未验收；**关闭不表示完成或阶段通过**。只保留milestone概要，进入阶段时再创建一个当前issue。执行顺序见 [Milestones](https://github.com/' + repo + '/milestones)。'
            body = note + '\n\n---\n\n' + (existing.get('body') or '')
            api('/issues/' + str(number), 'PATCH',
                {'title': title, 'body': body, 'state': 'closed', 'state_reason': 'not_planned',
                 'milestone': None, 'labels': [x['name'] for x in existing['labels'] if x['name'] not in {'blocked', 'in-progress', 'needs-training'}]})
        comment_path = '/issues/' + str(number) + '/comments'
        comments = pages(comment_path)
        marker = '<!-- ' + retired['marker'] + ' -->'
        if not any(marker in c['body'] for c in comments):
            api(comment_path, 'POST', {'body': marker + '\n按滚动顺序撤销提前创建的阶段占位issue。保留关闭记录供追溯；issue关闭状态不代表验收完成。该milestone仍是后续阶段概要。'})
    result = {'mode': 'serial_replan', 'active_issue': active['number'],
        'completed_issue_preserved': completed['number'],
        'retired_planned_issues': [x['number'] for x in spec['retire_issues']],
        'milestones': [x['number'] for x in spec['milestones']]}
    print(json.dumps(result, ensure_ascii=False))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with Path(summary).open('a') as stream:
            stream.write('Serial research sequence applied.\n\n')
            stream.write(f'- Current issue: https://github.com/{repo}/issues/{active["number"]}\n')
            stream.write(f'- Preserved accepted issue: https://github.com/{repo}/issues/{completed["number"]}\n')
            stream.write('- Closed as not planned: ' + ', '.join(
                f'[#{x["number"]}](https://github.com/{repo}/issues/{x["number"]})'
                for x in spec['retire_issues']) + '\n')
            stream.write(f'- Milestones: https://github.com/{repo}/milestones\n')


if __name__ == '__main__':
    main()
