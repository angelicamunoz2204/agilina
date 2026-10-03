"""Agilina agent worker.

Long-lived process with no interface or inbound port: on start it opens an
outbound connection to LiveKit and registers as an available worker. When a
ceremony room is created, LiveKit offers the job over that already-open
connection and the worker launches a subprocess dedicated to that room. It
never needs to be reachable from the internet.
"""

__version__ = "0.1.0"
