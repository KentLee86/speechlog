# speechlog

토큰 인증 전사 API와 화자·시간·문장 조회를 위한 Python SDK와 CLI입니다. 전사와 모델 실행은 별도 큐 서버가 담당하며, 클라이언트 컴퓨터에는 모델을 설치하지 않습니다. 현재 조회·내보내기는 구현됐고 원격 API 연결은 서버 계약 확정 후 추가됩니다. 조회 코어는 외부 의존성이 없으며 모델을 불러오거나 내려받지 않습니다.

```python
from speechlog import Transcript

transcript = Transcript.load("transcript.json")
result = transcript.query(speaker=2, start=60, end=90, text="확인")
print(result.to_json())
```

정본 JSON은 `schema_version`, `source_id`, `duration`, `speakers`, `segments`를 담습니다. 구간에는 `id/start/end/speaker/text/overlap/uncertain`이 있습니다. 기존 실험의 `turns`와 `words` JSON도 읽으며 기존 ID와 시간을 유지합니다. 화자가 없는 구간에는 임의 화자를 붙이지 않습니다.

조회 시간은 초 또는 `HH:MM:SS`입니다. 기본 `overlap`은 조회 범위와 겹치는 구간을, `contained`는 완전히 들어오는 구간을 고릅니다. 범위는 반열린 구간입니다. `context_turns`는 앞뒤 구간을 더하고 `matched/context`로 직접 검색 결과와 문맥을 구별합니다. `limit/offset`은 직접 일치 항목에 적용하며 `total/next_offset/truncated`로 잘림을 알립니다. 빈 결과는 정상입니다.

개발 검증: `uv run pytest`. 실제 음성과 전사 결과는 무시되는 `work/`에만 보관합니다.

## CLI 조회와 내보내기

```sh
speechlog query transcript.json --speaker 2 --start 60 --end 90 --json
speechlog query transcript.json --search 확인 --context-turns 1 --limit 20 --offset 0 --json
speechlog query transcript.json --text '^다음' --regex --mode contained --json
speechlog inspect transcript.json
speechlog speakers transcript.json
speechlog export transcript.json --format srt --out transcript.srt
```

`--text`와 `--search`는 같은 옵션입니다. `--json`을 생략한 조회는 직접 일치에 `*`, 문맥에 `~`를 표시합니다. 결과는 stdout, 진단과 구조화된 오류는 stderr로 나갑니다. 종료 코드는 사용법 오류 2, 입력·조회 오류 3, 파일 쓰기 오류 4, 실행 의존성 누락 5, 모델 검증 오류 6, 엔진 실행 오류 7입니다. API 연결 전의 전사·모델 목록·연결 진단은 `feature_pending` 오류와 종료 코드 5를 반환합니다. 빈 조회는 0입니다. TXT/SRT는 익명 화자와 겹침·확인 필요 표시를 포함하고 JSONL은 구간당 한 객체를 출력합니다.
