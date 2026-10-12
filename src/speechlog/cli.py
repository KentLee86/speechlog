"""Command line interface. Results on stdout, diagnostics on stderr."""
import argparse
import json
from pathlib import Path
import sys
from .core import Transcript, SpeechlogError
from .export import render

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise SpeechlogError(message, 'usage_error')

def parser():
    root = Parser(prog='speechlog', description='로컬 음성 전사 및 시간·화자 조회')
    root.add_argument('--version', action='version', version='speechlog 0.1.0')
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
    t = commands.add_parser('transcribe', help='외부 로컬 엔진으로 전사')
    t.add_argument('input')
    t.add_argument('--profile', choices=['call-ko'], default='call-ko')
    t.add_argument('--out', required=True)
    t.add_argument('--diarize', action='store_true')
    t.add_argument('--device', choices=['auto', 'cpu', 'vulkan'], default='auto')
    t.add_argument('--preprocess', choices=['none', 'dynaudnorm'], default='dynaudnorm')
    t.add_argument('--whisper-bin', help='native whisper-cli 실행 파일')
    t.add_argument('--whisper-model', help='Whisper GGML 모델 파일')
    t.add_argument('--nemo-bin', help='native nemo-speech 실행 파일')
    t.add_argument('--nemo-model', help='Nemotron GGUF 모델 파일')
    t.add_argument('--whisper-docker', help='명시적 Docker fallback 이미지(digest 권장)')
    t.add_argument('--threads', type=int, default=8)
    m = commands.add_parser('models', help='영속 모델·엔진 캐시 관리')
    mc = m.add_subparsers(dest='model_command', required=True)
    mc.add_parser('list')
    for name in ('fetch', 'prepare'):
        f = mc.add_parser(name)
        f.add_argument('name', nargs='?', choices=['whisper', 'nemotron', 'nemo-engine', 'all'], default='all')
        f.add_argument('--from-file', help='공식 해시를 검증할 로컬 파일')
    commands.add_parser('doctor', help='FFmpeg·엔진·캐시·GPU 진단')
    return root

def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))

def main(argv=None):
    try:
        args = parser().parse_args(argv)
        if args.command in ('models', 'doctor'):
            from .models import catalogue, prepare, doctor
            if args.command == 'doctor': emit(doctor())
            elif args.model_command == 'list': emit(catalogue())
            else: emit(prepare(args.name, from_file=args.from_file))
            return 0
        if args.command == 'transcribe':
            from .inference import transcribe
            result = transcribe(args.input, profile=args.profile, out=args.out, diarize=args.diarize, device=args.device, preprocess=args.preprocess, whisper_bin=args.whisper_bin, whisper_model=args.whisper_model, nemo_bin=args.nemo_bin, nemo_model=args.nemo_model, whisper_docker=args.whisper_docker, threads=args.threads)
            emit({'source_id': result.source_id, 'duration': result.duration, 'segments': len(result.segments), 'speakers': len(result.speakers)})
            return 0
        transcript = Transcript.load(args.file)
        if args.command == 'query':
            result = transcript.query(speaker=args.speaker, start=args.start, end=args.end, text=args.text, regex=args.regex, mode=args.mode, context_turns=args.context_turns, limit=args.limit, offset=args.offset)
            if args.json: print(result.to_json(indent=2))
            else:
                for s in result.to_dict()['segments']:
                    print(f"{s['start']:.3f}-{s['end']:.3f} [{s['speaker']}] {'*' if s['matched'] else '~'} {s['text']}")
                print(f'일치 {result.total}개; 다음 offset={result.next_offset}', file=sys.stderr)
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
        return {'usage_error': 2, 'invalid_input': 3, 'invalid_regex': 3, 'read_error': 3, 'io_error': 4, 'dependency_missing': 5, 'model_error': 6, 'engine_error': 7}.get(code, 1)

if __name__ == '__main__':
    raise SystemExit(main())
