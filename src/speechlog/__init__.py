"""Dependency-free transcript SDK."""
from .core import Transcript, Segment, Speaker, QueryResult, SpeechlogError

__all__ = ["Transcript", "Segment", "Speaker", "QueryResult", "SpeechlogError", "transcribe"]

def transcribe(*args, **kwargs):
    from .inference import transcribe as run
    return run(*args, **kwargs)
