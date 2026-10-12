# 데이터와 조회 계약

`schema_version: 1`의 시간 단위는 초이며 원본 음성 시간축을 사용합니다. `source_id`는 경로 대신 내용 식별자를 사용하도록 권장합니다. `speakers`는 `{id, label}` 배열이고 화자 ID는 정수 또는 문자열입니다. `segments`의 ID는 파일 안에서 고유하며 시간은 `0 <= start <= end <= duration`이어야 합니다. 겹치는 구간과 파일 내 순서를 유지합니다.

`Transcript.from_dict/load`는 `segments`, `turns`, `words` 순서로 가져옵니다. ID가 없을 때만 1부터 번호를 생성합니다. `has_overlap` 또는 `overlap_speakers`는 `overlap`으로 가져옵니다. 정본 외 추가 정보는 `metadata`에 보관할 수 있습니다.

조회는 파일 내 구간 순서로 반환합니다. `speaker`는 ID의 문자열 표현으로 비교하고 일반 문장 검색은 대소문자를 구별하지 않습니다. `regex=True`는 Python 정규식을 사용합니다. `context_turns`는 일치 구간 앞뒤의 파일 내 구간 수입니다. 페이지에 포함된 직접 일치 항목만 `matched=true`이며, 문맥이 다른 페이지의 일치 항목이어도 이번 페이지에서는 `context=true`입니다.

speechlog는 이 JSON을 생성하는 STT 서버나 서버 API 클라이언트가 아닙니다. 외부 도구가 가져온 JSON을 독립적으로 조회합니다. 조회와 내보내기에는 모델·FFmpeg·네트워크가 필요하지 않습니다. CLI의 공개 명령은 `query`, `inspect`, `speakers`, `export`입니다.

입력은 UTF-8 JSON 객체여야 합니다. 디코딩·JSON 읽기 오류는 `read_error`, 형식·타입 위반은 `invalid_input`으로 반환하며 CLI 종료 코드는 모두 3입니다. 각 구간과 화자 항목은 객체여야 합니다. 구간 ID와 화자 ID는 정수 또는 문자열이며 boolean은 ID로 허용하지 않습니다. 화자 `label`은 문자열이고 생략하면 익명 기본값을 생성합니다. `metadata`는 문자열 키를 가진 JSON 객체이며 JSON으로 직렬화할 수 있는 값만 허용합니다. `source_id`는 문자열, `schema_version`은 정수 1, 시간과 duration은 유한한 숫자, `overlap/uncertain`은 boolean입니다.

`HH:MM:SS`의 모든 구성 요소는 음이 아니어야 하며 시간과 분은 정수, 분과 초는 60 미만이어야 합니다. SDK `text/search`는 문자열 또는 None, `regex`는 boolean이어야 합니다. 잘못된 정규식 문법은 `invalid_regex`입니다.
