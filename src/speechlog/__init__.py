"""Dependency-free transcript SDK."""
from .core import Transcript, Segment, Speaker, QueryResult, SpeechlogError

__all__ = ["Transcript", "Segment", "Speaker", "QueryResult", "SpeechlogError", "transcribe"]

def transcribe(*args, **kwargs):
    raise SpeechlogError('원격 API 서버 계약 연결 전입니다', 'feature_pending')
