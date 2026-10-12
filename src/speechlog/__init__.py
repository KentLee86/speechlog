"""Dependency-free transcript SDK."""
from ._version import __version__
from .core import Transcript, Segment, Speaker, QueryResult, SpeechlogError

__all__ = ["Transcript", "Segment", "Speaker", "QueryResult", "SpeechlogError"]
