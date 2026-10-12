import json
import pytest
from speechlog import Transcript, SpeechlogError
from speechlog.stats import union_seconds

@pytest.fixture
def sample():
    return Transcript.from_dict({'duration': 20, 'speakers': [{'id':1}, {'id':2}, {'id':3}], 'segments': [
        {'start':0,'end':10,'speaker':1,'text':'가 나 가'},
        {'start':5,'end':15,'speaker':1,'text':'A a'},
        {'start':8,'end':12,'speaker':2,'text':'나\t가'},
        {'start':18,'end':20,'speaker':None,'text':''},
    ]})

def test_hand_counted_stats(sample):
    s=sample.stats().to_dict()
    assert s['declared_speaker_count']==3 and s['observed_speaker_count']==2
    assert s['unknown_speaker']['turns']==1
    assert s['total']['turns']==4 and s['total']['characters_with_spaces']==11
    assert s['total']['characters_without_spaces']==7 and s['total']['words']==7
    assert s['total']['duration_sum_seconds']==26
    assert s['total']['duration_union_seconds']==17
    assert s['speech_coverage_seconds']==17 and s['speech_coverage_ratio']==.85
    assert s['speakers'][0]['duration_sum_seconds']==20
    assert s['speakers'][0]['duration_union_seconds']==15
    assert s['total']['duration_sum_minutes']==26/60
    assert json.loads(sample.stats().to_json())==s

def test_clipped_filtered_stats(sample):
    s=sample.stats(speaker=1,start=6,end=9).to_dict()
    assert s['total']['duration_sum_seconds']==6
    assert s['total']['duration_union_seconds']==3
    assert s['window']['duration_seconds']==3 and s['speech_coverage_ratio']==1
    assert s['total']['words']==5 # Full text: cannot time-clip without word alignment.
    assert s['timing']['text_clipped'] is False
    assert sample.stats(start=6,end=9,mode='contained').to_dict()['total']['turns']==0
    assert sample.stats(text='나').to_dict()['total']['turns']==2
    assert sample.stats(text='^A',regex=True).to_dict()['total']['turns']==1

def test_coarse_recording_time_unavailable(sample):
    d=sample.to_dict(); d['metadata']={'time_granularity':'recording'}
    s=Transcript.from_dict(d).stats(start=6,end=9).to_dict()
    assert s['timing']['estimated'] and not s['timing']['available']
    assert s['total']['duration_sum_seconds'] is None
    assert s['speech_coverage_ratio'] is None and s['speech_coverage_seconds'] is None
    assert s['total']['estimated_interval_union_seconds']==3

def test_words_unicode_and_matching(sample):
    w=sample.words().to_dict()
    assert w['counts']==[{'text':'가','count':3},{'text':'a','count':2},{'text':'나','count':2}]
    assert sample.word_counts(text='A').to_dict()['counts'][0]['count']==2
    assert sample.words(text='A',case_sensitive=True).to_dict()['counts'][0]['count']==1
    assert sample.words(top=1).to_dict()['truncated']
    assert sample.words(speaker=2,start=9,end=11).to_dict()['total_tokens']==2
    assert sample.words(text='가 나',count_mode='literal').to_dict()['counts'][0]['count']==1
    assert sample.words(text='[가나]',count_mode='regex').to_dict()['counts'][0]['count']==5
    assert sample.words(text='^',count_mode='regex').to_dict()['counts'][0]['count']==0
    assert sample.words(text='없는말').to_dict()['counts']==[{'text':'없는말','count':0}]

def test_empty_unknown_and_declared_roundtrip():
    empty=Transcript.from_dict({'segments':[],'duration':0})
    assert empty.stats().to_dict()['speech_coverage_ratio']==0
    assert empty.words().to_dict()['counts']==[]
    t=Transcript.from_dict({'segments':[{'start':0,'end':1,'speaker':None,'text':'가'}]})
    assert t.stats().to_dict()['observed_speaker_count']==0
    assert t.stats().to_dict()['unknown_speaker']['words']==1
    t=Transcript.from_dict({'segments':[{'start':0,'end':1,'speaker':7,'text':'가'}]})
    assert t.stats().to_dict()['declared_speaker_count']==0
    assert Transcript.from_dict(t.to_dict()).stats().to_dict()['declared_speaker_count']==0
    assert t.stats(speaker=999).to_dict()['total']['turns']==0

@pytest.mark.parametrize('kwargs',[{'top':0},{'top':True},{'text':''},{'text':[]},{'case_sensitive':1},{'count_mode':'bad'},{'count_mode':'literal'},{'count_mode':'regex','text':'['},{'speaker':True},{'start':'01:-1:00'}])
def test_invalid_words_arguments(sample,kwargs):
    with pytest.raises(SpeechlogError): sample.words(**kwargs)

def test_union_touching_unsorted_and_zero():
    assert union_seconds([(5,8),(0,2),(2,6),(9,9)])==8
