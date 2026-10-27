"""Small static guard for obvious dangerous Python APIs; not a pentest or CVE audit."""
import ast
from pathlib import Path

roots = (Path('flakewise'), Path('api'))
errors = []
files = 0
for root in roots:
    for path in root.rglob('*.py'):
        files += 1
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f'{path}: cannot parse: {exc}')
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'eval', 'exec'}:
                errors.append(f'{path}:{node.lineno}: dynamic code execution: {node.func.id}')
            if isinstance(node, ast.Call) and any(k.arg == 'shell' and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords):
                errors.append(f'{path}:{node.lineno}: shell=True')

if not files:
    errors.append('No Python application files found')
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print(f'Bounded AST scan: {files} Python files; no dynamic eval/exec or shell=True found.')
print('Scope excludes dependency advisories, DOM injection, network, infrastructure and penetration testing.')
