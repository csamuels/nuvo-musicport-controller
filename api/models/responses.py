"""API response models."""

from typing import List, Optional
from pydantic import BaseModel


class ZoneResponse(BaseModel):
    """Zone information response."""

    guid: str
    name: str
    zone_id: str
    zone_number: int
    is_on: bool
    volume: int
    mute: bool
    source_id: int
    source_name: str
    party_mode: str
    max_volume: int
    min_volume: int


class SourceResponse(BaseModel):
    """Source information response."""

    guid: str
    name: str
    source_id: int
    is_smart: bool
    is_network: bool
    zone_count: int


class SystemStatusResponse(BaseModel):
    """System status response."""

    device_type: str
    firmware_version: str
    all_mute: bool
    all_off: bool
    active_zone: str
    active_source: str
    zones: List[ZoneResponse]
    sources: List[SourceResponse]


class CommandResponse(BaseModel):
    """Generic command response."""

    success: bool
    message: str


class StateChangeEventResponse(BaseModel):
    """State change event for WebSocket."""

    target: str
    property: str
    value: str
    timestamp: float
