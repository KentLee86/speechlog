#!/usr/bin/env python3
"""Bump the single version source after a clean commit."""
import argparse
import json
from pathlib import Path
import sys
from versioning import bump

def main():
    parser = argparse.ArgumentParser(description='깨끗한 커밋에서 버전 정본 갱신')
    parser.add_argument('target', help='major/minor/patch 또는 명시적 안정 SemVer')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(bump(Path(__file__).resolve().parent.parent, args.target, args.dry_run), ensure_ascii=False))
        return 0
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
