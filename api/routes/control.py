"""System control endpoints."""

from fastapi import APIRouter, HTTPException, Depends

from nuvo_sdk import NuVoClient
from ..dependencies import get_client
from ..models import CommandResponse, SystemStatusResponse, ZoneResponse, SourceResponse

router = APIRouter(prefix="/control", tags=["control"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_status(client: NuVoClient = Depends(get_client)):
    """
    Get full system status.

    Returns:
        Complete system status with all zones and sources
    """
    try:
        status = await client.get_status()
        return SystemStatusResponse(
            device_type=status.device_type,
            firmware_version=status.firmware_version,
            all_mute=status.all_mute,
            all_off=status.all_off,
            active_zone=status.active_zone,
            active_source=status.active_source,
            zones=[
                ZoneResponse(
                    guid=z.guid,
                    name=z.name,
                    zone_id=z.zone_id,
                    zone_number=z.zone_number,
                    is_on=z.is_on,
                    volume=z.volume,
                    mute=z.mute,
                    source_id=z.source_id,
                    source_name=z.source_name,
                    party_mode=z.party_mode,
                    max_volume=z.max_volume,
                    min_volume=z.min_volume,
                )
                for z in status.zones
            ],
            sources=[
                SourceResponse(
                    guid=s.guid,
                    name=s.name,
                    source_id=s.source_id,
                    is_smart=s.is_smart,
                    is_network=s.is_network,
                    zone_count=s.zone_count,
                )
                for s in status.sources
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/partymode", response_model=CommandResponse)
async def toggle_party_mode(client: NuVoClient = Depends(get_client)):
    """
    Toggle party mode (all zones play same source).

    Returns:
        Command execution result
    """
    try:
        await client.party_mode_toggle()
        return CommandResponse(success=True, message="Party mode toggled")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alloff", response_model=CommandResponse)
async def all_off(client: NuVoClient = Depends(get_client)):
    """
    Turn off all zones.

    Returns:
        Command execution result
    """
    try:
        await client.all_off()
        return CommandResponse(success=True, message="All zones turned off")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
