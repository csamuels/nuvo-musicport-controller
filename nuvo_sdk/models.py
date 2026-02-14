"""Data models for NuVo MusicPort system."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Zone:
    """Represents a zone in the NuVo system."""

    guid: str
    name: str
    zone_id: str  # e.g., "Zone_1"
    zone_number: int  # e.g., 1
    is_on: bool
    volume: int  # 0-79
    mute: bool
    source_id: int
    source_name: str
    source_guid: str
    party_mode: str  # "On" or "Off"
    max_volume: int
    min_volume: int
    zone_group_name: str  # e.g., "ZG_1"
    zone_group_id: str
    do_not_disturb: bool = False
    is_locked: bool = False


@dataclass
class Source:
    """Represents a music source in the NuVo system."""

    guid: str
    name: str
    source_id: int
    is_smart: bool  # NuVo smart source (MCS capable)
    is_network: bool  # Network source
    zone_count: int  # Number of zones using this source
    zone_list: str  # Comma-separated zone names
    metadata1: str = ""
    metadata2: str = ""
    metadata3: str = ""
    metadata4: str = ""
    metadata_art: str = ""


@dataclass
class SystemStatus:
    """Overall system status."""

    device_type: str
    firmware_version: str
    all_mute: bool
    all_off: bool
    active_zone: str
    active_source: str
    zones: List[Zone]
    sources: List[Source]


@dataclass
class StateChangeEvent:
    """Represents a state change event from the device."""

    target: str  # e.g., "Zone_1", "ZG_1", "NV-I8G"
    property: str  # e.g., "Volume", "PowerOn", "Mute"
    value: str  # The new value
    timestamp: Optional[float] = None
