"""Text and subtitle exports without inference dependencies."""
import json
from .core import Transcript, SpeechlogError

def timestamp(seconds: float, separator='.') -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    secs, fraction = divmod(remainder, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}{separator}{fraction:03d}'

def render(transcript: Transcript, format: str) -> str:
    if format == 'json':
        return transcript.to_json(indent=2) + '\n'
    if format == 'jsonl':
        return ''.join(json.dumps(s.__dict__, ensure_ascii=False) + '\n' for s in transcript.segments)
    labels = {s.id: s.label for s in transcript.speakers}
    entries = []
    for i, s in enumerate(transcript.segments, 1):
        label = labels.get(s.speaker, '화자 미확정')
        marker = (' [겹침]' if s.overlap else '') + (' [확인 필요]' if s.uncertain else '')
        if format == 'txt':
            entries.append(f'[{timestamp(s.start)} ~ {timestamp(s.end)}] {label}{marker}\n{s.text}\n')
        elif format == 'srt':
            entries.append(f'{i}\n{timestamp(s.start, ",")} --> {timestamp(s.end, ",")}\n[{label}]{marker} {s.text}\n')
        else:
            raise SpeechlogError('지원하지 않는 export 형식')
    if format not in ('txt', 'srt'):
        raise SpeechlogError('지원하지 않는 export 형식')
    return '\n'.join(entries)
