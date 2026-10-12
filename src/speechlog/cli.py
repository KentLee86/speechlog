"""Command line interface. Results on stdout, diagnostics on stderr."""
import argparse
import json
from pathlib import Path
import sys
from ._version import __version__
from .core import Transcript, SpeechlogError
from .export import render

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise SpeechlogError(message, 'usage_error')

def parser():
    root = Parser(prog='speechlog', description='전사 결과의 화자·시간·문장 조회 및 내보내기')
    root.add_argument('--version', action='version', version=f'speechlog {__version__}')
    commands = root.add_subparsers(dest='command', required=True)
    q = commands.add_parser('query', help='화자·시간·문장 조회')
    q.add_argument('file')
    q.add_argument('--speaker')
    q.add_argument('--start')
    q.add_argument('--end')
    q.add_argument('--mode', choices=['overlap', 'contained'], default='overlap')
    q.add_argument('--text', '--search', dest='text')
    q.add_argument('--regex', action='store_true')
    q.add_argument('--context-turns', type=int, default=0)
    q.add_argument('--limit', type=int)
    q.add_argument('--offset', type=int, default=0)
    q.add_argument('--json', action='store_true')
    for name in ('inspect', 'speakers'):
        p = commands.add_parser(name)
        p.add_argument('file')
        p.add_argument('--json', action='store_true', help='JSON 출력(기본값)')
    e = commands.add_parser('export')
    e.add_argument('file')
    e.add_argument('--format', choices=['txt', 'srt', 'json', 'jsonl'], required=True)
    e.add_argument('--out')
    st = commands.add_parser('stats', help='화자·문자·단어·시간 통계')
    w = commands.add_parser('words', help='단어·phrase·정규식 빈도')
    for p in (st, w):
        p.add_argument('file')
        p.add_argument('--speaker')
        p.add_argument('--start')
        p.add_argument('--end')
        p.add_argument('--mode', choices=['overlap', 'contained'], default='overlap')
        p.add_argument('--json', action='store_true', help='JSON 출력(기본값)')
    st.add_argument('--text', '--search', dest='text')
    st.add_argument('--regex', action='store_true')
    w.add_argument('--text', help='집계할 토큰·phrase·정규식')
    w.add_argument('--search', '--filter-text', dest='search', help='집계 전 구간 문장 필터')
    w.add_argument('--top', type=int)
    w.add_argument('--case-sensitive', action='store_true')
    counting = w.add_mutually_exclusive_group()
    counting.add_argument('--count-mode', choices=['token', 'literal', 'regex'], default='token')
    counting.add_argument('--regex', action='store_const', const='regex', dest='count_mode')
    return root

def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def main(argv=None):
    try:
        args = parser().parse_args(argv)
        transcript = Transcript.load(args.file)
        if args.command == 'query':
            result = transcript.query(speaker=args.speaker, start=args.start, end=args.end, text=args.text, regex=args.regex, mode=args.mode, context_turns=args.context_turns, limit=args.limit, offset=args.offset)
            if args.json: print(result.to_json(indent=2))
            else:
                for s in result.to_dict()['segments']:
                    print(f"{s['start']:.3f}-{s['end']:.3f} [{s['speaker']}] {'*' if s['matched'] else '~'} {s['text']}")
                print(f'일치 {result.total}개; 다음 offset={result.next_offset}', file=sys.stderr)
        elif args.command == 'stats':
            emit(transcript.stats(speaker=args.speaker, start=args.start, end=args.end, text=args.text, regex=args.regex, mode=args.mode).to_dict())
        elif args.command == 'words':
            emit(transcript.words(speaker=args.speaker, start=args.start, end=args.end, search=args.search, mode=args.mode, text=args.text, top=args.top, case_sensitive=args.case_sensitive, count_mode=args.count_mode).to_dict())
        elif args.command == 'inspect':
            emit({'schema_version': transcript.schema_version, 'source_id': transcript.source_id, 'duration': transcript.duration, 'segments': len(transcript.segments), 'speakers': len(transcript.speakers), 'overlap_segments': sum(s.overlap for s in transcript.segments), 'uncertain_segments': sum(s.uncertain for s in transcript.segments), 'metadata': transcript.metadata})
        elif args.command == 'speakers':
            emit({'speakers': [{**s.__dict__, 'segments': sum(x.speaker == s.id for x in transcript.segments)} for s in transcript.speakers]})
        elif args.command == 'export':
            content = render(transcript, args.format)
            if args.out: Path(args.out).write_text(content, encoding='utf-8')
            else: sys.stdout.write(content)
        return 0
    except (SpeechlogError, OSError) as error:
        code = getattr(error, 'code', 'io_error')
        print(json.dumps({'error': {'code': code, 'message': str(error)}}, ensure_ascii=False), file=sys.stderr)
        return {'usage_error': 2, 'invalid_input': 3, 'invalid_regex': 3, 'read_error': 3, 'io_error': 4}.get(code, 1)

if __name__ == '__main__':
    raise SystemExit(main())
