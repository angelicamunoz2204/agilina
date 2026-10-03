"""Agilina transcription service.

Turns audio segments into text. It does not identify speakers: the identity
arrives with the audio track, signed in the LiveKit token. It lives in its own
instance because it needs a GPU, it is the most expensive component per hour
and it must be switchable on and off with the ceremony without affecting the
rest.
"""

__version__ = "0.1.0"
