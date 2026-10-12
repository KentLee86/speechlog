"""Standard-library version helpers; never access credentials."""
import ast
from pathlib import Path
import re
import subprocess

VERSION_PATH = 'src/speechlog/_version.py'

def run(root, *args):
    return subprocess.check_output(args, cwd=root, text=True).strip()

def clean(root):
    if run(root, 'git', 'status', '--porcelain'):
        raise ValueError('작업 트리가 깨끗해야 합니다. 먼저 검증하고 커밋하세요.')

def version(root):
    text = (Path(root)/VERSION_PATH).read_text()
    assignments = [n for n in ast.parse(text).body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets)]
    if len(assignments) != 1:
        raise ValueError('버전 정본은 __version__ 한 개여야 합니다')
    value = ast.literal_eval(assignments[0].value)
    parse(value)
    config = (Path(root)/'pyproject.toml').read_text()
    if 'dynamic = ["version"]' not in config or f'path = "{VERSION_PATH}"' not in config or re.search(r'^version\s*=', config, re.M):
        raise ValueError('pyproject 버전은 정본 파일의 dynamic 설정이어야 합니다')
    return value

def parse(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value):
        raise ValueError('안정 SemVer major.minor.patch 형식이 필요합니다')
    return tuple(map(int, value.split('.')))

def next_version(current, target):
    major, minor, patch = parse(current)
    if target == 'major': result = (major+1, 0, 0)
    elif target == 'minor': result = (major, minor+1, 0)
    elif target == 'patch': result = (major, minor, patch+1)
    else: result = parse(target)
    if result <= (major, minor, patch):
        raise ValueError('새 버전은 현재 버전보다 커야 합니다')
    return '.'.join(map(str, result))

def bump(root, target, dry_run=False):
    clean(root)
    current = version(root)
    wanted = next_version(current, target)
    if not dry_run:
        path = Path(root)/VERSION_PATH
        text = path.read_text()
        path.write_text(re.sub(r'(__version__\s*=\s*)[\'\"][^\'\"]+[\'\"]', lambda m: m[1]+f'"{wanted}"', text))
    return {'current': current, 'next': wanted, 'dry_run': dry_run}
