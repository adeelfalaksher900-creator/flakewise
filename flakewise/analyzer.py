"""Bounded analysis of user-supplied JUnit reports. No network or code execution."""
from __future__ import annotations
import hashlib
import math
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

MAX_RUNS = 12
MAX_FILE_BYTES = 512 * 1024
MAX_XML_BYTES = 2 * 1024 * 1024
MAX_CASES = 3000
COMMIT = re.compile(r'^[0-9a-f]{7,64}$')

class InputError(ValueError):
    pass

def clean(value: str, max_length: int) -> str:
    return ''.join(c for c in value if c in '\n\t' or ord(c) >= 32)[:max_length]

def tag(element):
    return element.tag.rsplit('}', 1)[-1] if isinstance(element.tag, str) else ''

def classify_counts(p: int, f: int, s: int) -> str:
    """Describe observed outcomes, without inferring cause."""
    return ('mixed' if p and f else 'skipped' if not p and not f else
            'insufficient' if p + f < 2 else 'passed' if p else 'failed')

def analyze(data):
    if not isinstance(data, dict) or set(data) != {'runs'} or not isinstance(data['runs'], list):
        raise InputError('Provide an object containing a runs list.')
    runs = data['runs']
    if not 1 <= len(runs) <= MAX_RUNS:
        raise InputError('Choose between 1 and 12 JUnit reports.')
    total_bytes = 0
    total_cases = 0
    summaries, names, groups = [], set(), defaultdict(list)
    warnings = ['Commit identifiers are supplied by the user and are not independently verified.',
                'Mixed outcomes on the same commit may reflect changes in test environments or data; they do not prove the cause.']
    for run in runs:
        if not isinstance(run, dict) or set(run) != {'name', 'commit', 'xml'}:
            raise InputError('Each report needs a name, commit, and XML content.')
        name, commit, xml = run['name'], run['commit'], run['xml']
        if not all(isinstance(v, str) for v in (name, commit, xml)):
            raise InputError('Report names, commits, and XML must be text.')
        try:
            name.encode('utf-8'); commit.encode('utf-8'); xml.encode('utf-8')
        except UnicodeEncodeError:
            raise InputError('Reports must contain valid Unicode text.') from None
        name = clean(name.strip(), 150)
        commit = commit.strip().lower()
        if not name or name in names:
            raise InputError('Report names must be nonempty and unique.')
        names.add(name)
        if not COMMIT.fullmatch(commit):
            raise InputError('Each report needs the same full commit hash or a 7–64 character hexadecimal commit identifier.')
        encoded = xml.encode('utf-8')
        if len(encoded) > MAX_FILE_BYTES:
            raise InputError('Each XML report must be 512 KB or smaller.')
        total_bytes += len(encoded)
        if total_bytes > MAX_XML_BYTES:
            raise InputError('Combined XML reports must be 2 MB or smaller.')
        if re.search(r'<!\s*(?:DOCTYPE|ENTITY)', xml, re.I):
            raise InputError('DTD and entity declarations are not allowed in reports.')
        try:
            root = ET.fromstring(xml)
        except (ET.ParseError, ValueError, RecursionError):
            raise InputError('The JUnit XML could not be parsed.') from None
        if tag(root) not in {'testsuite', 'testsuites'}:
            raise InputError('Expected a JUnit testsuite or testsuites document.')
        seen, count = set(), 0
        for case in root.iter():
            if tag(case) != 'testcase':
                continue
            count += 1
            total_cases += 1
            if total_cases > MAX_CASES:
                raise InputError(f'At most {MAX_CASES} test observations are allowed.')
            case_name = clean(case.get('name', '').strip(), 500)
            class_name = clean(case.get('classname', '').strip(), 500)
            if not case_name:
                raise InputError('Every testcase needs a name.')
            identity = (class_name, case_name)
            if identity in seen:
                raise InputError(f'Duplicate test identity in report {name}: {class_name} / {case_name}.')
            seen.add(identity)
            statuses = [child for child in case if tag(child) in {'failure', 'error', 'skipped'}]
            kinds = {tag(child) for child in statuses}
            if 'skipped' in kinds and kinds.intersection({'failure', 'error'}):
                raise InputError(f'A testcase in {name} is both skipped and failed.')
            failure = next((c for c in statuses if tag(c) in {'failure', 'error'}), None)
            status = 'fail' if failure is not None else ('skipped' if 'skipped' in kinds else 'pass')
            duration = None
            if case.get('time') is not None:
                try:
                    duration = float(case.get('time'))
                except (ValueError, OverflowError):
                    raise InputError(f'A testcase in {name} has invalid duration.') from None
                if not math.isfinite(duration) or duration < 0 or duration > 10_000_000:
                    raise InputError(f'A testcase in {name} has invalid duration.')
            message = ''
            if failure is not None:
                message = clean((failure.get('message') or ''.join(failure.itertext())).strip(), 500)
            groups[(commit, class_name, case_name)].append({'run': name, 'status': status, 'duration': duration, 'message': message})
        if not count:
            raise InputError(f'Report {name} has no test cases.')
        summaries.append({'name': name, 'commit': commit, 'test_count': count})
    tests = []
    for (commit, class_name, name), observations in groups.items():
        p = sum(o['status'] == 'pass' for o in observations)
        f = sum(o['status'] == 'fail' for o in observations)
        s = sum(o['status'] == 'skipped' for o in observations)
        classification = classify_counts(p, f, s)
        identifier = hashlib.sha256('\0'.join((commit, class_name, name)).encode()).hexdigest()[:20]
        tests.append({'id': identifier, 'class_name': class_name, 'name': name, 'commit': commit,
                      'observations': observations, 'classification': classification,
                      'pass_count': p, 'fail_count': f, 'skip_count': s})
    order = {'mixed': 0, 'failed': 1, 'insufficient': 2, 'passed': 3, 'skipped': 4}
    tests.sort(key=lambda t: (order[t['classification']], t['class_name'], t['name'], t['commit']))
    summary = {'runs': len(summaries), 'tests': len(tests)}
    for k in ('mixed', 'failed', 'passed', 'insufficient', 'skipped'):
        summary[k] = sum(t['classification'] == k for t in tests)
    return {'runs': summaries, 'tests': tests, 'summary': summary, 'warnings': warnings}
