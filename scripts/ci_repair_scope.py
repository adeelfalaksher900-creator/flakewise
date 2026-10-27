"""CI scope gate for the supervised classify_counts repair challenge.

Run the copy from the trusted MR target branch with a target commit SHA. It compares
syntax trees with only classify_counts' body removed, so the agent cannot change other
application logic, imports, its signature, the independent tests or the gate itself.
"""
import ast
import copy
import subprocess
import sys
from pathlib import Path

ALLOWED = {'flakewise/analyzer.py', 'docs/repair.md'}
TARGET = 'flakewise/analyzer.py'
SAFE_FUNCTION_NODES = (
    ast.If, ast.IfExp, ast.Return, ast.Expr, ast.Compare, ast.BoolOp, ast.UnaryOp, ast.BinOp,
    ast.Name, ast.Load, ast.Constant, ast.And, ast.Or, ast.Not, ast.Gt,
    ast.GtE, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Add, ast.Sub,
)


def git(*args):
    return subprocess.check_output(['git', *args], text=True)


def normalized(source):
    module = ast.parse(source)
    copy_module = copy.deepcopy(module)
    matches = [item for item in copy_module.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == 'classify_counts']
    if len(matches) != 1 or not isinstance(matches[0], ast.FunctionDef):
        raise ValueError('expected exactly one top-level classify_counts function')
    matches[0].body = [ast.Pass()]
    return ast.dump(copy_module, include_attributes=False)


def check_body(source):
    module = ast.parse(source)
    matches = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'classify_counts']
    if len(matches) != 1:
        raise ValueError('expected exactly one top-level classify_counts function')
    for statement in matches[0].body:
        for node in ast.walk(statement):
            if not isinstance(node, SAFE_FUNCTION_NODES):
                raise ValueError(f'classify_counts contains forbidden syntax: {type(node).__name__}')


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: ci_repair_scope.py <trusted-target-sha>')
    base = sys.argv[1]
    changed = set(git('diff', '--name-only', '--no-renames', f'{base}...HEAD').splitlines())
    if TARGET not in changed or not changed <= ALLOWED:
        raise ValueError('repair must change only classifier and optional repair notes')
    entry = git('ls-tree', 'HEAD', '--', TARGET).splitlines()
    if len(entry) != 1 or not entry[0].startswith('100644 blob '):
        raise ValueError('classifier must be a regular non-executable file')
    trusted = git('show', f'{base}:{TARGET}')
    proposed = git('show', f'HEAD:{TARGET}')
    if normalized(trusted) != normalized(proposed):
        raise ValueError('changes outside the classify_counts body are not allowed')
    check_body(proposed)
    print('Repair scope passed: only classify_counts body and optional docs/repair.md changed.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, SyntaxError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f'Repair scope failed: {exc}')
