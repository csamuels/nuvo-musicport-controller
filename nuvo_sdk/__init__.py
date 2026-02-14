"""
NuVo MusicPort SDK

A Python library for controlling NuVo MusicPort multi-room audio systems.
"""

from .client import NuVoClient
from .models import Zone, Source, SystemStatus, StateChangeEvent
from .exceptions import (
    NuVoException,
    ConnectionError,
    ProtocolError,
    CommandError,
)

__version__ = "0.1.0"
__all__ = [
    "NuVoClient",
    "Zone",
    "Source",
    "SystemStatus",
    "StateChangeEvent",
    "NuVoException",
    "ConnectionError",
    "ProtocolError",
    "CommandError",
]
