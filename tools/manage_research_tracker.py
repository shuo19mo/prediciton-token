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


if __name__ == '__main__':
    main()
