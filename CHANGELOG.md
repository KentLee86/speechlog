# 변경 기록

## 0.2.0

- stats SDK/CLI에 화자별 구간·문자·Unicode 공백 토큰 수, 클립된 시간 합산과 합집합, coverage 제공.
- 선언·관측 화자와 미상 화자를 구별하고 recording 단위 시간 자료는 정밀 발화시간을 unavailable로 표시.
- words/word_counts SDK 및 words CLI에 토큰·literal phrase·정규식 빈도, top·대소문자 옵션 제공.
- 기존 0.1.0 query API와 입력 전사의 원문·시간·ID 보존.
- 버전 정본 통일, SemVer 범프 및 검증된 커밋의 태그·wheel/sdist GitHub 릴리스 스크립트 추가.

## 0.1.0

- 독립 전사 결과 조회 SDK와 query/inspect/speakers/export CLI 제공.
- 기존 turns/words JSON 가져오기와 정본 JSON 왕복 지원.
- 입력 검증, 문맥·페이지 표시, TXT/SRT/JSON/JSONL 출력 제공.
