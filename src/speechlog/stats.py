"""Deterministic Unicode text counts and clipped interval statistics."""
from collections import Counter
from dataclasses import dataclass
import json
import re
from .core import SpeechlogError, seconds

@dataclass(frozen=True)
class StatsResult:
    data: dict

    def to_dict(self):
        # A JSON copy keeps the result independent of caller mutations.
        return json.loads(self.to_json())

    def to_json(self, **kwargs):
        return json.dumps(self.data, ensure_ascii=False, **kwargs)


def union_seconds(intervals):
    total = 0.0
    left = right = None
    for start, end in sorted(intervals):
        if left is None:
            left, right = start, end
        elif start <= right:
            right = max(right, end)
        else:
            total += right - left
            left, right = start, end
    return total + (right - left if left is not None else 0.0)


def selected(transcript, *, speaker=None, start=None, end=None, text=None, search=None, regex=False, mode='overlap'):
    rows = transcript.query(speaker=speaker, start=start, end=end, text=text, search=search, regex=regex, mode=mode).segments
    left = min(seconds(start) or 0.0, transcript.duration)
    right = min(seconds(end) if end is not None else transcript.duration, transcript.duration)
    return rows, left, right


def counts(rows):
    return {'turns': len(rows), 'characters_with_spaces': sum(len(s.text) for s in rows),
            'characters_without_spaces': sum(sum(not c.isspace() for c in s.text) for s in rows),
            'words': sum(len(s.text.split()) for s in rows)}


def stats(transcript, **filters):
    rows, left, right = selected(transcript, **filters)
    coarse = transcript.metadata.get('time_granularity') == 'recording'
    intervals = [(max(s.start, left), min(s.end, right)) for s in rows]
    def summarize(group):
        spans = [(max(s.start, left), min(s.end, right)) for s in group]
        summed = sum(max(0, b-a) for a,b in spans)
        union = union_seconds(spans)
        return {**counts(group), 'duration_sum_seconds': None if coarse else summed,
                'duration_sum_minutes': None if coarse else summed/60,
                'duration_union_seconds': None if coarse else union,
                'duration_union_minutes': None if coarse else union/60,
                'estimated_interval_sum_seconds': summed if coarse else None,
                'estimated_interval_union_seconds': union if coarse else None}
    ids = list(dict.fromkeys(s.speaker for s in rows if s.speaker is not None))
    declared = transcript.declared_speaker_ids if transcript.declared_speaker_ids is not None else tuple(s.id for s in transcript.speakers)
    labels = {s.id: s.label for s in transcript.speakers}
    by_speaker = [{'id': ident, 'label': labels.get(ident, f'화자 {ident}'), **summarize([s for s in rows if s.speaker == ident])} for ident in ids]
    coverage = union_seconds(intervals)
    window = max(0.0, right-left)
    return StatsResult({'source_id': transcript.source_id, 'recording_duration_seconds': transcript.duration,
        'window': {'start': left, 'end': right, 'duration_seconds': window},
        'timing': {'available': not coarse, 'estimated': coarse, 'time_granularity': transcript.metadata.get('time_granularity', 'segment'), 'text_clipped': False},
        'declared_speaker_count': len(declared), 'declared_speaker_ids': list(declared),
        'observed_speaker_count': len(ids), 'observed_speaker_ids': ids,
        'unknown_speaker': summarize([s for s in rows if s.speaker is None]),
        'total': summarize(rows), 'speakers': by_speaker,
        'speech_coverage_seconds': None if coarse else coverage,
        'speech_coverage_ratio': None if coarse else (coverage/window if window else 0.0),
        'estimated_interval_coverage_seconds': coverage if coarse else None})


def words(transcript, *, text=None, top=None, case_sensitive=False, count_mode='token', **filters):
    if text is not None and (not isinstance(text, str) or not text):
        raise SpeechlogError('빈 문자열이 아닌 text가 필요합니다')
    if not isinstance(case_sensitive, bool) or count_mode not in ('token', 'literal', 'regex'):
        raise SpeechlogError('잘못된 case_sensitive 또는 count_mode')
    if top is not None and (isinstance(top, bool) or not isinstance(top, int) or top <= 0):
        raise SpeechlogError('top은 1 이상 정수여야 합니다')
    if count_mode != 'token' and text is None:
        raise SpeechlogError('literal/regex 빈도에는 text가 필요합니다')
    rows, _, _ = selected(transcript, **filters)
    normalize = (lambda x: x) if case_sensitive else str.casefold
    tokens = Counter(normalize(token) for s in rows for token in s.text.split())
    total_tokens = sum(tokens.values())
    if count_mode == 'token':
        if text is not None:
            key = normalize(text)
            tokens = Counter({key: tokens[key]})
    elif count_mode == 'literal':
        key = normalize(text)
        tokens = Counter({text: sum(normalize(s.text).count(key) for s in rows)})
    else:
        try:
            pattern = re.compile(text, 0 if case_sensitive else re.IGNORECASE)
        except re.error as error:
            raise SpeechlogError(str(error), 'invalid_regex') from error
        tokens = Counter({text: sum(1 for s in rows for m in pattern.finditer(s.text) if m.start() != m.end())})
    ranked = sorted(tokens.items(), key=lambda item: (-item[1], item[0]))
    total_entries = len(ranked)
    page = ranked if top is None else ranked[:top]
    return StatsResult({'count_mode': count_mode, 'case_sensitive': case_sensitive,
        'token_policy': 'unicode_whitespace', 'turns': len(rows), 'total_tokens': total_tokens,
        'total_entries': total_entries, 'top': top, 'truncated': len(page) < total_entries,
        'counts': [{'text': token, 'count': count} for token, count in page]})
