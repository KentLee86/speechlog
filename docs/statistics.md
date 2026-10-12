# 통계 계약

`Transcript.stats(speaker=None, start=None, end=None, text=None, search=None, regex=False, mode="overlap")`는 query와 같은 필터로 구간을 선택합니다. 결과의 `to_dict()/to_json()`을 사용합니다. stats는 페이지·문맥 필터를 받지 않습니다.

- `declared_speaker_count/ids`는 입력의 speakers에 선언된 화자입니다. `observed_speaker_count/ids`는 선택된 구간에서 실제 관측된 화자이며 None은 제외합니다. None 구간은 `unknown_speaker`에 별도 집계합니다. 화자가 없는 데이터에도 화자를 추가하지 않습니다.
- 가져올 때 생성된 익명 화자와 원래 선언된 화자를 구분하도록 정본 JSON에 선택적 `declared_speaker_ids`를 기록합니다. 없으면 입력 speakers의 ID를 선언된 것으로 봅니다.
- `turns`는 선택된 구간 수입니다. 문자 수는 Python Unicode 코드 포인트 수이며 공백 제외는 `str.isspace()` 문자를 제외합니다. 단어 수는 `str.split()`의 Unicode 공백 토큰 수입니다. 한국어 형태소 분석을 하지 않으며 문장부호는 토큰의 일부입니다.
- `duration_sum_seconds/minutes`는 선택한 구간을 조회 시간으로 잘라 합산합니다. 같은 화자의 겹친 구간도 중복 합산합니다. `duration_union_seconds/minutes`는 그 집합의 구간 합집합 길이입니다. 화자마다 따로 계산하며 total의 union은 모든 화자의 합집합입니다. 화자별 sum 또는 union을 더하면 다른 화자끼리 겹친 시간이 중복되어 녹음 길이보다 클 수 있습니다.
- `recording_duration_seconds`는 원본 전체 길이, `window`는 0부터 원본 끝 사이로 제한한 조회 시간입니다. `speech_coverage_seconds`는 선택된 모든 구간의 합집합이고 ratio의 분모는 window 길이입니다. 빈 window의 ratio는 0입니다.
- `metadata.time_granularity="recording"`이면 정밀 발화시간을 알 수 없으므로 `timing.available=false/estimated=true`, duration과 speech coverage는 null입니다. 대신 `estimated_interval_*`는 기록된 거친 구간의 추정 길이를 명시합니다. 일반 segment 자료도 실제 음성과 대조해야 합니다.
- 시간 필터는 구간 선택 및 시간 통계만 자릅니다. 정밀 단어 시간이 없으므로 선택된 구간의 전체 문장을 집계하고 `timing.text_clipped=false`로 알립니다.

`Transcript.words(text=None, top=None, case_sensitive=False, count_mode="token", **filters)` 및 별칭 `word_counts`는 같은 구간 필터를 사용합니다. 여기서 text는 집계할 단어나 패턴입니다. 구간 text 필터는 `search`를 사용합니다. 기본 token 모드는 casefold로 정규화한 완전한 공백 토큰 빈도이며 top은 양수입니다. count 내림차순, 동률은 정규화 문자열 순서로 정렬합니다. `total_tokens`는 text/top 제한 전 선택된 문장의 전체 토큰 수이고 `truncated`는 top에 의한 잘림입니다.

`count_mode="literal"`은 구간마다 공백을 포함한 phrase의 겹치지 않는 문자열 출현 수, `regex`는 Python finditer의 겹치지 않는 비어 있지 않은 매치 수입니다. 구간 경계를 넘어 연결하지 않습니다. literal/token은 기본 casefold, regex는 기본 Unicode IGNORECASE이며 case_sensitive=True이면 대소문자를 구별합니다. 빈 text와 잘못된 타입은 invalid_input, 정규식 문법 오류는 invalid_regex입니다. 존재하지 않는 단어는 count=0입니다.
