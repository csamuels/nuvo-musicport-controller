"""
NuVo MusicPort SDK

A Python library for controlling NuVo MusicPort multi-room audio systems.
"""

from .client import NuVoClient
from .mcs_client import MCSClient, MusicServer, PickListItem
from .models import Zone, Source, SystemStatus, StateChangeEvent
from .discovery import discover_devices, DiscoveredDevice, get_local_network
from .exceptions import (
    NuVoException,
    ConnectionError,
    ProtocolError,
    CommandError,
)

__version__ = "0.1.0"
__all__ = [
    "NuVoClient",
    "MCSClient",
    "MusicServer",
    "PickListItem",
    "Zone",
    "Source",
    "SystemStatus",
    "StateChangeEvent",
    "DiscoveredDevice",
    "discover_devices",
    "get_local_network",
    "NuVoException",
    "ConnectionError",
    "ProtocolError",
    "CommandError",
]
