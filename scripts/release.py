#!/usr/bin/env python3
"""Validate a clean main commit, then explicitly publish its version tag."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from versioning import clean, run, version


def plan(root):
    clean(root)
    current = version(root)
    if run(root, 'git', 'branch', '--show-current') != 'main':
        raise ValueError('main 브랜치에서 배포해야 합니다')
    remote = run(root, 'git', 'remote', 'get-url', 'origin')
    if remote not in ('https://github.com/KentLee86/speechlog.git', 'https://github.com/KentLee86/speechlog', 'git@github.com:KentLee86/speechlog.git'):
        raise ValueError('origin이 speechlog 공개 저장소여야 합니다')
    changelog = (Path(root)/'CHANGELOG.md').read_text()
    marker = f'## {current}\n'
    if marker not in changelog:
        raise ValueError('현재 버전 CHANGELOG 항목이 필요합니다')
    notes = changelog.split(marker, 1)[1].split('\n## ', 1)[0].strip()
    if not notes:
        raise ValueError('릴리스 변경 기록이 비어 있습니다')
    tag = f'v{current}'
    tags = run(root, 'git', 'tag', '--list', tag)
    if tags:
        raise ValueError('이 버전 태그가 이미 존재합니다')
    return {'version': current, 'tag': tag, 'commit': run(root, 'git', 'rev-parse', 'HEAD'), 'notes': notes}


def publish(root, release):
    root = Path(root)
    subprocess.run(['uv', 'run', 'pytest', '-q'], cwd=root, check=True)
    subprocess.run(['uv', 'build'], cwd=root, check=True)
    clean(root)
    if run(root, 'git', 'rev-parse', 'HEAD') != release['commit'] or version(root) != release['version']:
        raise ValueError('검증 중 커밋 또는 버전이 바뀌었습니다')
    wheel = root/'dist'/f"speechlog-{release['version']}-py3-none-any.whl"
    sdist = root/'dist'/f"speechlog-{release['version']}.tar.gz"
    if not wheel.is_file() or not sdist.is_file():
        raise ValueError('현재 버전 wheel/sdist가 필요합니다')
    with zipfile.ZipFile(wheel) as package:
        metadata = package.read(f"speechlog-{release['version']}.dist-info/METADATA").decode()
        if f"Version: {release['version']}\n" not in metadata:
            raise ValueError('wheel 버전 불일치')
    subprocess.run(['git','tag','-a',release['tag'],'-m',f"speechlog {release['version']}",release['commit']],cwd=root,check=True)
    subprocess.run(['git','push','origin','HEAD:main'],cwd=root,check=True)
    subprocess.run(['git','push','origin',release['tag']],cwd=root,check=True)
    with tempfile.TemporaryDirectory() as tmp:
        notes = Path(tmp)/'notes.md'; notes.write_text(release['notes'])
        subprocess.run(['gh','release','create',release['tag'],str(wheel),str(sdist),'--repo','KentLee86/speechlog','--verify-tag','--title',f"speechlog {release['version']}",'--notes-file',str(notes)],cwd=root,check=True)


def main():
    parser = argparse.ArgumentParser(description='검증된 main 커밋의 태그·GitHub 릴리스 배포')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--dry-run', action='store_true', help='태그·push·업로드 없이 사전 검사와 계획 출력')
    mode.add_argument('--publish', action='store_true', help='테스트·빌드 후 태그·push·wheel/sdist 릴리스 실행')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        release = plan(root)
        if args.publish: publish(root, release)
        print(json.dumps({**release, 'dry_run':args.dry_run},ensure_ascii=False))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
