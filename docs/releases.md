# 버전과 릴리스

버전은 `src/speechlog/_version.py`가 정본입니다. pyproject의 Hatch dynamic version, SDK `__version__`, CLI `--version`은 이를 공유합니다. 안정 SemVer의 major/minor/patch 또는 명시적 증가 버전을 지원합니다. 범프와 dry-run 모두 작업 트리가 깨끗해야 하며 스크립트는 credential을 생성하거나 로그인하지 않습니다.

```sh
python3 scripts/bump_version.py minor --dry-run
python3 scripts/bump_version.py 0.2.0
# CHANGELOG.md에 새 버전 항목 작성, 테스트·빌드 후 로컬 커밋
python3 scripts/release.py --dry-run
# 부모 리뷰 및 배포 승인 후
python3 scripts/release.py --publish
```

범프는 버전 정본만 수정합니다. release dry-run은 clean/main/origin/version/CHANGELOG/기존 태그를 검사하고 배포할 커밋과 태그를 출력합니다. 네트워크 전송·태그 생성·테스트·빌드는 하지 않습니다. publish는 테스트와 wheel/sdist 빌드, 버전 및 커밋 재확인 뒤 `v<version>` annotated tag를 만들고 main·태그를 push한 뒤 GitHub release에 해당 wheel/sdist를 첨부합니다. PyPI에 publish하지 않습니다.

이미 존재하는 태그는 거부합니다. 네트워크 단계가 일부 실패하면 생성한 태그나 push를 자동으로 되돌리지 않으며, 출력된 오류와 원격 상태를 확인하고 수동으로 남은 단계를 처리합니다. 스크립트를 재실행해 태그를 덮어쓰지 않습니다.
