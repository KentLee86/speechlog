# 데이터와 조회 계약

`schema_version: 1`의 시간 단위는 초이며 원본 음성 시간축을 사용합니다. `source_id`는 경로 대신 내용 식별자를 사용하도록 권장합니다. `speakers`는 `{id, label}` 배열이고 화자 ID는 정수 또는 문자열입니다. `segments`의 ID는 파일 안에서 고유하며 시간은 `0 <= start <= end <= duration`이어야 합니다. 겹치는 구간과 파일 내 순서를 유지합니다.

`Transcript.from_dict/load`는 `segments`, `turns`, `words` 순서로 가져옵니다. ID가 없을 때만 1부터 번호를 생성합니다. `has_overlap` 또는 `overlap_speakers`는 `overlap`으로 가져옵니다. 정본 외 추가 정보는 `metadata`에 보관할 수 있습니다.

조회는 파일 내 구간 순서로 반환합니다. `speaker`는 ID의 문자열 표현으로 비교하고 일반 문장 검색은 대소문자를 구별하지 않습니다. `regex=True`는 Python 정규식을 사용합니다. `context_turns`는 일치 구간 앞뒤의 파일 내 구간 수입니다. 페이지에 포함된 직접 일치 항목만 `matched=true`이며, 문맥이 다른 페이지의 일치 항목이어도 이번 페이지에서는 `context=true`입니다.

speechlog는 이 JSON을 생성하는 STT 서버나 서버 API 클라이언트가 아닙니다. 외부 도구가 가져온 JSON을 독립적으로 조회합니다. 조회와 내보내기에는 모델·FFmpeg·네트워크가 필요하지 않습니다. CLI의 공개 명령은 `query`, `inspect`, `speakers`, `export`입니다.
