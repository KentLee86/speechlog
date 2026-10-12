import json
import sys
import pytest
from speechlog import Transcript, SpeechlogError

@pytest.fixture
def transcript():
    return Transcript.from_dict({'source_id': 'synthetic-call', 'duration': 100, 'segments': [
        {'id': 'a', 'start': 50, 'end': 65, 'speaker': 1, 'text': '첫 번째 문장'},
        {'id': 'b', 'start': 65, 'end': 70, 'speaker': 2, 'text': '가상 확인 문장', 'overlap': True},
        {'id': 'c', 'start': 89, 'end': 95, 'speaker': 2, 'text': '다음 확인'},
        {'id': 'd', 'start': 95, 'end': 100, 'speaker': None, 'text': '마지막'},
    ]})

def test_query_boundaries_and_context(transcript):
    result = transcript.query(speaker=2, start='00:01:00', end=90, text='확인', limit=1, context_turns=1).to_dict()
    assert result['matched_ids'] == ['b']
    assert [s['id'] for s in result['segments']] == ['a', 'b', 'c']
    assert [s['matched'] for s in result['segments']] == [False, True, False]
    assert result['total'] == 2 and result['truncated'] and result['next_offset'] == 1
    assert transcript.query(speaker=2, start=60, end=90, mode='contained').matched_ids == ('b',)
    assert transcript.query(start=70, end=89).total == 0
    assert transcript.query(speaker=2, limit=1, offset=1).matched_ids == ('c',)
    assert transcript.query(text='^다음', regex=True).matched_ids == ('c',)
    assert transcript.query(text='없는 문장').to_dict()['segments'] == []

def test_roundtrip_and_no_model_import(tmp_path, transcript):
    target = tmp_path/'transcript.json'
    transcript.save(target)
    assert Transcript.load(target).to_dict() == transcript.to_dict()
    assert json.loads(transcript.query().to_json())['total'] == 4
    assert 'speechlog.inference' not in sys.modules

def test_legacy_preserves_ids_and_time():
    imported = Transcript.from_dict({'turns': [{'id': 42, 'start': 5.3, 'end': 6.4, 'speaker': 2, 'text': '가상', 'has_overlap': True}]})
    assert imported.segments[0].id == 42
    assert imported.segments[0].start == 5.3
    assert imported.segments[0].overlap
    words = Transcript.from_dict({'words': [{'start': 1, 'end': 2, 'word': '단어', 'overlap_speakers': [1,2]}]})
    assert words.segments[0].text == '단어' and words.segments[0].speaker is None

@pytest.mark.parametrize('change', [{'end': 101}, {'start': -1}, {'end': float('nan')}, {'text': 1}])
def test_invalid_records_are_rejected(transcript, change):
    data = transcript.to_dict()
    data['segments'][0].update(change)
    with pytest.raises(SpeechlogError):
        Transcript.from_dict(data)

@pytest.mark.parametrize('kwargs', [{'start': -1}, {'start': 90, 'end': 60}, {'start': '00:90:00'}, {'limit': 0}, {'offset': -1}, {'regex': True, 'text': '['}, {'mode': 'bad'}])
def test_invalid_query(transcript, kwargs):
    with pytest.raises(SpeechlogError):
        transcript.query(**kwargs)

def test_duplicate_id_guard(transcript):
    data = transcript.to_dict()
    data['segments'][1]['id'] = 'a'
    with pytest.raises(SpeechlogError):
        Transcript.from_dict(data)

@pytest.mark.parametrize('value', ['01:-1:00', '01:00:-1', '-1:59:59', '01:00:nan', '01:00:inf', '01:1.5:00'])
def test_invalid_time_components(transcript, value):
    with pytest.raises(SpeechlogError) as caught:
        transcript.query(start=value)
    assert caught.value.code == 'invalid_input'

@pytest.mark.parametrize('data', [
    {'segments': [None]}, {'segments': [1]}, {'turns': ['invalid']}, {'words': [[]]},
    {'segments': [], 'speakers': None}, {'segments': [], 'speakers': [None]},
    {'segments': [], 'speakers': [{'id': True}]},
    {'segments': [], 'speakers': [{'id': False}]},
    {'segments': [], 'speakers': [{'id': []}]},
    {'segments': [], 'speakers': [{'id': 2, 'label': None}]},
    {'segments': [], 'speakers': [{'id': 2, 'label': 9}]},
    {'segments': [], 'metadata': []}, {'segments': [], 'metadata': None},
    {'segments': [], 'metadata': {2: 'invalid'}},
    {'segments': [], 'metadata': {'unsupported': object()}},
    {'segments': [], 'schema_version': True}, {'segments': [], 'source_id': []},
    {'segments': [], 'duration': True},
    {'segments': [{'start': True, 'end': 2}]},
    {'segments': [{'start': 1, 'end': 2, 'speaker': True}]},
    {'segments': [{'start': 1, 'end': 2, 'overlap': 'false'}]},
    {'segments': [{'start': 1, 'end': 2, 'uncertain': 0}]},
])
def test_typed_input_errors(data):
    with pytest.raises(SpeechlogError) as caught:
        Transcript.from_dict(data)
    assert caught.value.code == 'invalid_input'

@pytest.mark.parametrize('kwargs', [
    {'text': 1}, {'search': []}, {'text': b'bytes', 'regex': True},
    {'text': 'ok', 'regex': 'yes'}, {'text': 'ok', 'regex': 1},
    {'speaker': True}, {'speaker': []},
])
def test_query_type_errors(transcript, kwargs):
    with pytest.raises(SpeechlogError) as caught:
        transcript.query(**kwargs)
    assert caught.value.code == 'invalid_input'

def test_invalid_utf8_is_read_error(tmp_path):
    path = tmp_path/'invalid.json'
    path.write_bytes(b'\xff\xfe')
    with pytest.raises(SpeechlogError) as caught:
        Transcript.load(path)
    assert caught.value.code == 'read_error'

def test_valid_typed_speakers_metadata_roundtrip():
    data = {'source_id': 'fiction', 'segments': [], 'speakers': [{'id': 'a', 'label': '가상 화자'}], 'metadata': {'nested': {'list': [None, True, 1, 'value']}}}
    imported = Transcript.from_dict(data)
    assert imported.speakers[0].label == '가상 화자'
    assert json.loads(imported.to_json())['metadata'] == data['metadata']
