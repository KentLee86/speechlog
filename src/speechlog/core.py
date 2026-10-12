"""Canonical records, legacy import, and deterministic queries."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
import re
from typing import Any

class SpeechlogError(ValueError):
    def __init__(self, message: str, code: str = "invalid_input"):
        super().__init__(message)
        self.code = code

def seconds(value: str | float | None) -> float | None:
    if value is None:
        return None
    try:
        parts = str(value).split(":")
        if len(parts) not in (1, 3):
            raise ValueError()
        components = [float(part) for part in parts]
        if any(not math.isfinite(part) or part < 0 for part in components):
            raise ValueError()
        if len(parts) == 3 and (not components[0].is_integer() or not components[1].is_integer()):
            raise ValueError()
        result = components[0] if len(parts) == 1 else components[0]*3600+components[1]*60+components[2]
        if not math.isfinite(result) or result < 0:
            raise ValueError()
        if len(parts) == 3 and (float(parts[1]) >= 60 or float(parts[2]) >= 60):
            raise ValueError()
        return result
    except (ValueError, TypeError):
        raise SpeechlogError("시간은 음이 아닌 초 또는 HH:MM:SS여야 합니다") from None

@dataclass(frozen=True)
class Speaker:
    id: int | str
    label: str

@dataclass(frozen=True)
class Segment:
    id: int | str
    start: float
    end: float
    speaker: int | str | None
    text: str
    overlap: bool = False
    uncertain: bool = False

@dataclass(frozen=True)
class QueryResult:
    segments: tuple[Segment, ...]
    matched_ids: tuple[int | str, ...]
    total: int
    offset: int
    limit: int | None
    next_offset: int | None
    def to_dict(self) -> dict:
        return {"segments": [{**asdict(s), "matched": s.id in self.matched_ids, "context": s.id not in self.matched_ids} for s in self.segments], "matched_ids": list(self.matched_ids), "total": self.total, "offset": self.offset, "limit": self.limit, "next_offset": self.next_offset, "truncated": self.next_offset is not None}
    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

@dataclass(frozen=True)
class Transcript:
    source_id: str
    duration: float
    speakers: tuple[Speaker, ...]
    segments: tuple[Segment, ...]
    metadata: dict[str, Any]
    schema_version: int = 1
    declared_speaker_ids: tuple[int | str, ...] | None = None

    @classmethod
    def load(cls, path: str | Path) -> Transcript:
        try:
            return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise SpeechlogError(str(error), "read_error") from error

    @classmethod
    def from_dict(cls, data: dict) -> Transcript:
        try:
            if not isinstance(data, dict):
                raise ValueError("JSON 객체가 필요합니다")
            if type(data.get("schema_version", 1)) is not int or data.get("schema_version", 1) != 1:
                raise ValueError("지원하지 않는 schema_version")
            rows = data.get("segments", data.get("turns", data.get("words")))
            if not isinstance(rows, list):
                raise ValueError("segments/turns/words 배열이 필요합니다")
            segments = []
            ids = set()
            for i, row in enumerate(rows):
                if not isinstance(row, dict):
                    raise ValueError("각 segment/turn/word는 JSON 객체여야 합니다")
                ident = row.get("id", i + 1)
                if isinstance(ident, bool) or not isinstance(ident, (str, int)) or ident in ids:
                    raise ValueError("segment id는 고유한 문자열 또는 정수여야 합니다")
                ids.add(ident)
                if any(isinstance(row[key], bool) or not isinstance(row[key], (int, float)) for key in ("start", "end")):
                    raise ValueError("segment 시간은 숫자여야 합니다")
                start, end = float(row["start"]), float(row["end"])
                if not math.isfinite(start) or not math.isfinite(end) or not 0 <= start <= end:
                    raise ValueError("잘못된 segment 시간")
                speaker = row.get("speaker")
                if speaker is not None and (isinstance(speaker, bool) or not isinstance(speaker, (str, int))):
                    raise ValueError("잘못된 speaker id")
                text = row.get("text", row.get("word", ""))
                if not isinstance(text, str):
                    raise ValueError("text는 문자열이어야 합니다")
                overlap = row.get("overlap", row.get("has_overlap", bool(row.get("overlap_speakers"))))
                uncertain = row.get("uncertain", speaker is None)
                if not isinstance(overlap, bool) or not isinstance(uncertain, bool):
                    raise ValueError("overlap/uncertain은 boolean이어야 합니다")
                segments.append(Segment(ident, start, end, speaker, text, overlap, uncertain))
            raw_duration = data.get("duration", max((s.end for s in segments), default=0))
            if isinstance(raw_duration, bool) or not isinstance(raw_duration, (int, float)):
                raise ValueError("duration은 숫자여야 합니다")
            duration = float(raw_duration)
            if not math.isfinite(duration) or duration < 0 or any(s.end > duration for s in segments):
                raise ValueError("duration 범위 밖 segment")
            supplied = data.get("speakers", [])
            if not isinstance(supplied, list):
                raise ValueError("speakers는 배열이어야 합니다")
            speakers = []
            for supplied_speaker in supplied:
                if not isinstance(supplied_speaker, dict):
                    raise ValueError("각 speaker는 JSON 객체여야 합니다")
                ident = supplied_speaker["id"]
                if isinstance(ident, bool) or not isinstance(ident, (str, int)):
                    raise ValueError("speaker id는 문자열 또는 정수여야 합니다")
                label = supplied_speaker.get("label", f"화자 {ident}")
                if not isinstance(label, str):
                    raise ValueError("speaker label은 문자열이어야 합니다")
                speakers.append(Speaker(ident, label))
            known = {s.id for s in speakers}
            if len(known) != len(speakers):
                raise ValueError("중복 speaker id")
            for s in segments:
                if s.speaker is not None and s.speaker not in known:
                    speakers.append(Speaker(s.speaker, f"화자 {s.speaker}")); known.add(s.speaker)
            source_id = data.get("source_id", "legacy")
            if not isinstance(source_id, str):
                raise ValueError("source_id는 문자열이어야 합니다")
            metadata = data.get("metadata", {})
            if not isinstance(metadata, dict) or any(not isinstance(key, str) for key in metadata):
                raise ValueError("metadata는 문자열 키를 가진 JSON 객체여야 합니다")
            json.dumps(metadata, allow_nan=False)
            declared = data.get("declared_speaker_ids", [s["id"] for s in supplied])
            if not isinstance(declared, list) or any(isinstance(i, bool) or not isinstance(i, (str, int)) or i not in known for i in declared):
                raise ValueError("declared_speaker_ids는 알려진 화자 ID 배열이어야 합니다")
            if len(set(declared)) != len(declared):
                raise ValueError("중복 declared_speaker_ids")
            return cls(source_id, duration, tuple(speakers), tuple(segments), metadata, declared_speaker_ids=tuple(declared))
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise SpeechlogError(str(error)) from error

    def to_dict(self) -> dict:
        return {"schema_version": self.schema_version, "source_id": self.source_id, "duration": self.duration, "speakers": [asdict(s) for s in self.speakers], "segments": [asdict(s) for s in self.segments], "metadata": self.metadata, "declared_speaker_ids": list(self.declared_speaker_ids if self.declared_speaker_ids is not None else (s.id for s in self.speakers))}

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)

    def save(self, path: str | Path):
        Path(path).write_text(self.to_json(indent=2) + "\n", encoding="utf-8")

    def query(self, *, speaker=None, start=None, end=None, text=None, search=None, regex=False, mode="overlap", context_turns=0, limit=None, offset=0) -> QueryResult:
        if speaker is not None and (isinstance(speaker, bool) or not isinstance(speaker, (str, int))):
            raise SpeechlogError("speaker는 문자열 또는 정수여야 합니다")
        if not isinstance(regex, bool):
            raise SpeechlogError("regex는 boolean이어야 합니다")
        if any(value is not None and not isinstance(value, str) for value in (text, search)):
            raise SpeechlogError("text/search는 문자열이어야 합니다")
        start, end = seconds(start), seconds(end)
        if mode not in ("overlap", "contained") or (start is not None and end is not None and start > end):
            raise SpeechlogError("잘못된 시간 범위 또는 조회 mode")
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in (offset, context_turns)) or (limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0)):
            raise SpeechlogError("offset/context_turns는 0 이상, limit는 1 이상 정수여야 합니다")
        needle = text if text is not None else search
        try:
            pattern = re.compile(needle) if regex and needle is not None else None
        except re.error as error:
            raise SpeechlogError(str(error), "invalid_regex") from error
        indices = []
        for i, s in enumerate(self.segments):
            if speaker is not None and str(s.speaker) != str(speaker): continue
            if mode == "overlap":
                if start is not None and s.end <= start: continue
                if end is not None and s.start >= end: continue
            else:
                if start is not None and s.start < start: continue
                if end is not None and s.end > end: continue
            if needle is not None and not (pattern.search(s.text) if pattern else needle.casefold() in s.text.casefold()): continue
            indices.append(i)
        page = indices[offset:] if limit is None else indices[offset:offset+limit]
        included = set()
        for i in page:
            included.update(range(max(0, i-context_turns), min(len(self.segments), i+context_turns+1)))
        next_offset = offset + len(page) if offset + len(page) < len(indices) else None
        return QueryResult(tuple(self.segments[i] for i in sorted(included)), tuple(self.segments[i].id for i in page), len(indices), offset, limit, next_offset)

    def stats(self, **filters):
        from .stats import stats
        return stats(self, **filters)

    def words(self, *, text=None, top=None, case_sensitive=False, count_mode="token", **filters):
        from .stats import words
        return words(self, text=text, top=top, case_sensitive=case_sensitive, count_mode=count_mode, **filters)

    def word_counts(self, **options):
        return self.words(**options)
