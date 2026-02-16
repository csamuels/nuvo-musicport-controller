"""Device discovery endpoint."""

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from nuvo_sdk.discovery import discover_devices, get_local_network

router = APIRouter(prefix="/discovery", tags=["Device"])


class DiscoveredDeviceResponse(BaseModel):
    """Discovered device response."""

    ip: str
    hostname: Optional[str]
    mrad_port: int
    mcs_port: int
    responds_to_mrad: bool
    responds_to_mcs: bool
    device_info: Optional[str]


@router.get("", response_model=List[DiscoveredDeviceResponse])
async def discover():
    """
    Discover NuVo MusicPort devices on the local network.

    This endpoint scans the local network for devices with open ports
    5006 (MRAD) or 5004 (MCS) and attempts to identify NuVo MusicPort systems.

    Returns:
        List of discovered devices with connection information
    """
    # Get local network
    network = get_local_network()

    # Discover devices
    devices = await discover_devices(network, max_concurrent=100)

    return [
        DiscoveredDeviceResponse(
            ip=d.ip,
            hostname=d.hostname,
            mrad_port=d.mrad_port,
            mcs_port=d.mcs_port,
            responds_to_mrad=d.responds_to_mrad,
            responds_to_mcs=d.responds_to_mcs,
            device_info=d.device_info,
        )
        for d in devices
    ]
