import json
import subprocess
import sys
from speechlog import Transcript
from speechlog.export import render

def call(*args):
    return subprocess.run([sys.executable, '-m', 'speechlog', *map(str,args)], capture_output=True, text=True)

def sample(tmp_path):
    t = Transcript.from_dict({'source_id': 'fiction', 'duration': 100, 'segments': [
        {'id': 9, 'start': 61.25, 'end': 65, 'speaker': 2, 'text': '가상 확인'},
        {'id': 12, 'start': 70, 'end': 71, 'speaker': None, 'text': '다음'},
    ]})
    path = tmp_path/'sample.json'; t.save(path)
    return t, path

def test_cli_sdk_parity(tmp_path):
    t, path = sample(tmp_path)
    output = call('query', path, '--speaker', 2, '--start', '00:01:00', '--end', 90, '--search', '확인', '--context-turns', 1, '--limit', 1, '--json')
    assert output.returncode == 0 and output.stderr == ''
    assert json.loads(output.stdout) == t.query(speaker=2, start=60, end=90, text='확인', context_turns=1, limit=1).to_dict()
    assert json.loads(call('query',path,'--text','없음','--json').stdout)['total'] == 0

def test_exports_and_inspect(tmp_path):
    t, path = sample(tmp_path)
    for format in ('txt','srt','json','jsonl'):
        result = call('export', path, '--format', format)
        assert result.returncode == 0 and result.stdout == render(t, format)
    assert '00:01:01,250 --> 00:01:05,000' in render(t,'srt')
    out = tmp_path/'output.srt'
    assert call('export',path,'--format','srt','--out',out).stdout == ''
    assert out.read_text() == render(t,'srt')
    assert json.loads(call('inspect',path).stdout)['segments'] == 2
    assert json.loads(call('speakers',path).stdout)['speakers'][0]['id'] == 2

def test_structured_errors(tmp_path):
    _, path = sample(tmp_path)
    result = call('query',path,'--start','-1','--json')
    assert result.returncode == 3 and result.stdout == ''
    assert json.loads(result.stderr)['error']['code'] == 'invalid_input'
    assert call('query').returncode == 2
    assert call('query',tmp_path/'absent').returncode == 3
    assert call('query',path,'--regex','--text','[').returncode == 3


def test_only_query_tool_commands_are_exposed():
    help_output = call('--help')
    assert help_output.returncode == 0
    assert '{query,inspect,speakers,export,stats,words}' in help_output.stdout
    for command in ('transcribe', 'models', 'doctor'):
        assert command not in help_output.stdout
        result = call(command)
        assert result.returncode == 2 and result.stdout == ''
        assert json.loads(result.stderr)['error']['code'] == 'usage_error'
    import speechlog
    assert not hasattr(speechlog, 'transcribe')

def test_malformed_input_errors_do_not_leak_tracebacks(tmp_path):
    path = tmp_path/'malformed.json'
    invalid_records = [
        {'segments': [None]}, {'segments': [1]},
        {'segments': [], 'speakers': [{'id': True}]},
        {'segments': [], 'speakers': [{'id': 1, 'label': []}]},
        {'segments': [], 'metadata': []},
    ]
    for data in invalid_records:
        path.write_text(json.dumps(data))
        result = call('query', path, '--json')
        assert result.returncode == 3 and result.stdout == ''
        assert json.loads(result.stderr)['error']['code'] == 'invalid_input'
        assert 'Traceback' not in result.stderr
    path.write_bytes(b'\xff\xfe')
    result = call('inspect', path)
    assert result.returncode == 3 and result.stdout == ''
    assert json.loads(result.stderr)['error']['code'] == 'read_error'
    assert 'Traceback' not in result.stderr


def test_stats_words_cli_sdk_parity(tmp_path):
    t, path = sample(tmp_path)
    stats = call('stats', path, '--speaker', '2', '--start', '00:01:00', '--end', '90', '--json')
    assert stats.returncode == 0 and stats.stderr == ''
    assert json.loads(stats.stdout) == t.stats(speaker=2, start=60, end=90).to_dict()
    for options, flags in [
        ({'top':1}, ['--top','1']),
        ({'text':'확인'}, ['--text','확인']),
        ({'text':'가상 확인','count_mode':'literal'}, ['--text','가상 확인','--count-mode','literal']),
        ({'text':'.','count_mode':'regex','case_sensitive':True}, ['--text','.','--regex','--case-sensitive']),
        ({'search':'확인'}, ['--filter-text','확인']),
    ]:
        result=call('words',path,*flags,'--json')
        assert result.returncode==0 and not result.stderr
        assert json.loads(result.stdout)==t.words(**options).to_dict()
    result=call('words',path,'--top','0')
    assert result.returncode==3 and json.loads(result.stderr)['error']['code']=='invalid_input'
    assert call('stats',path,'--start','01:-1:00').returncode==3
