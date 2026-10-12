# speechlog

로컬 음성 전사와 화자·시간·문장 조회를 위한 Python SDK와 CLI입니다. 조회 코어는 외부 의존성이 없으며 모델을 불러오거나 내려받지 않습니다.

```python
from speechlog import Transcript

transcript = Transcript.load("transcript.json")
result = transcript.query(speaker=2, start=60, end=90, text="확인")
print(result.to_json())
```

정본 JSON은 `schema_version`, `source_id`, `duration`, `speakers`, `segments`를 담습니다. 구간에는 `id/start/end/speaker/text/overlap/uncertain`이 있습니다. 기존 실험의 `turns`와 `words` JSON도 읽으며 기존 ID와 시간을 유지합니다. 화자가 없는 구간에는 임의 화자를 붙이지 않습니다.

조회 시간은 초 또는 `HH:MM:SS`입니다. 기본 `overlap`은 조회 범위와 겹치는 구간을, `contained`는 완전히 들어오는 구간을 고릅니다. 범위는 반열린 구간입니다. `context_turns`는 앞뒤 구간을 더하고 `matched/context`로 직접 검색 결과와 문맥을 구별합니다. `limit/offset`은 직접 일치 항목에 적용하며 `total/next_offset/truncated`로 잘림을 알립니다. 빈 결과는 정상입니다.

개발 검증: `uv run pytest`. 실제 음성과 전사 결과는 무시되는 `work/`에만 보관합니다.
