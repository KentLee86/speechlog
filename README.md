# speechlog

이미 받은 전사 JSON에서 화자·시간·문장을 조사하고, 검색 결과와 주변 문맥을 확인하거나 TXT/SRT/JSON/JSONL로 내보내는 독립 Python SDK와 CLI입니다. Python 3.10 이상에서 표준 라이브러리만으로 실행합니다. 음성 전사와 서버 API 호출은 별도 도구나 스킬이 담당하며, speechlog는 로컬 전사 파일을 읽습니다.

## 설치와 실행

Git 저장소에서 바로 실행하거나 전역 도구로 설치할 수 있습니다. PyPI 배포는 하지 않습니다.

```sh
uvx --from git+https://github.com/KentLee86/speechlog speechlog --help
pipx run --spec git+https://github.com/KentLee86/speechlog speechlog --help
uv tool install git+https://github.com/KentLee86/speechlog
speechlog --help
```

Python 프로젝트의 SDK 의존성으로 추가할 때:

```sh
uv add 'speechlog @ git+https://github.com/KentLee86/speechlog'
# 또는
python -m pip install 'speechlog @ git+https://github.com/KentLee86/speechlog'
```

재현 가능한 설치는 Git URL 뒤에 `@<commit SHA>`를 붙여 고정합니다.

## SDK

```python
from speechlog import Transcript

transcript = Transcript.load("transcript.json")
result = transcript.query(speaker=2, start=60, end=90, text="확인")
print(result.to_json())
# result.to_dict()는 같은 결과를 Python 객체로 반환합니다.
```

정본 JSON은 `schema_version`, `source_id`, `duration`, `speakers`, `segments`를 담습니다. 구간에는 `id/start/end/speaker/text/overlap/uncertain`이 있습니다. 기존 실험의 `turns`와 `words` JSON도 읽으며 기존 ID와 시간을 유지합니다. `Transcript.save(path)`로 정본 JSON을 저장할 수 있습니다. 자세한 형식은 [데이터 계약](docs/schema.md)에 있습니다.

조회 시간은 초 또는 `HH:MM:SS`이며 소수 초를 지원합니다. 기본 `overlap`은 조회 범위와 겹치는 구간을, `contained`는 완전히 들어오는 구간을 고릅니다. 범위는 반열린 구간입니다. `context_turns`는 앞뒤 구간을 더하고 `matched/context`로 직접 검색 결과와 문맥을 구별합니다. `limit/offset`은 직접 일치 항목에 적용하며 `total/next_offset/truncated`로 잘림을 알립니다. 빈 결과는 정상입니다.

## CLI

```sh
speechlog query transcript.json --speaker 2 --start 60 --end 90 --json
speechlog query transcript.json --search 확인 --context-turns 1 --limit 20 --offset 0 --json
speechlog query transcript.json --text '^다음' --regex --mode contained --json
speechlog inspect transcript.json
speechlog speakers transcript.json
speechlog export transcript.json --format srt --out transcript.srt
speechlog export transcript.json --format json --out canonical.json
speechlog export transcript.json --format jsonl --out segments.jsonl
```

`--text`와 `--search`는 같은 옵션입니다. `--json`을 생략한 조회는 직접 일치에 `*`, 문맥에 `~`를 표시합니다. 결과는 stdout, 진단과 구조화된 오류는 stderr로 나갑니다. 종료 코드는 성공·빈 조회 0, 사용법 오류 2, 입력·조회 오류 3, 파일 쓰기 오류 4입니다. `inspect`와 `speakers`는 기본으로 JSON을 출력합니다.

TXT/SRT는 화자와 겹침·확인 필요 표시를 포함합니다. JSON은 전체 정본을, JSONL은 구간당 한 객체를 출력합니다. JSONL은 교환용 출력이며 `Transcript.load` 입력은 JSON 객체입니다.

## 해석상의 한계

화자 번호는 익명 식별자이며 실명이나 동일인 여부를 보장하지 않습니다. 화자가 없는 구간에는 임의 화자를 붙이지 않습니다. 겹침과 불확실성 표시는 입력 전사 결과를 따르며, speechlog가 음성을 다시 분석하지 않습니다. 인식 오류와 시간 정렬 오류는 원본 음성과 대조해 확인해야 합니다. FFmpeg·GPU·모델 설치는 조회 도구 실행에 필요하지 않습니다.

## 개발

```sh
uv run pytest
uv build
```

실제 음성과 전사 결과는 무시되는 `work/`에만 보관하고, 커밋에는 가상 fixture만 사용합니다. 개발 정본 지침은 `AGENTS.md`, `CLAUDE.md`는 그 심링크입니다.

잘못된 UTF-8 입력은 `read_error`, 잘못된 구간·화자·metadata 타입은 `invalid_input`으로 반환합니다. 화자 ID에 boolean을 사용할 수 없고, `HH:MM:SS`의 음수 구성 요소도 거부합니다. 프로젝트 라이선스는 [MIT](LICENSE)입니다.
