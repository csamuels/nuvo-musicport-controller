"""Zone control endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from nuvo_sdk import NuVoClient
from ..dependencies import get_client
from ..models import ZoneResponse, CommandResponse

router = APIRouter(prefix="/zones", tags=["System"])


class VolumeRequest(BaseModel):
    """Request to set volume."""

    volume: int  # 0-79


class SourceRequest(BaseModel):
    """Request to set source."""

    source_guid: str


@router.get("", response_model=List[ZoneResponse])
async def list_zones(client: NuVoClient = Depends(get_client)):
    """
    Get all zones.

    Returns:
        List of zones with current status
    """
    try:
        zones = await client.get_zones()
        return [
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
            for z in zones
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{zone_number}", response_model=ZoneResponse)
async def get_zone(zone_number: int, client: NuVoClient = Depends(get_client)):
    """
    Get specific zone by number.

    Args:
        zone_number: Zone number (1-6)

    Returns:
        Zone information
    """
    try:
        zones = await client.get_zones()
        for z in zones:
            if z.zone_number == zone_number:
                return ZoneResponse(
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
        raise HTTPException(status_code=404, detail=f"Zone {zone_number} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{zone_number}/power/on", response_model=CommandResponse)
async def power_on(zone_number: int, client: NuVoClient = Depends(get_client)):
    """
    Turn zone on.

    Args:
        zone_number: Zone number (1-6)
    """
    try:
        await client.power_on(zone_number)
        return CommandResponse(
            success=True, message=f"Zone {zone_number} powered on"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{zone_number}/power/off", response_model=CommandResponse)
async def power_off(zone_number: int, client: NuVoClient = Depends(get_client)):
    """
    Turn zone off.

    Args:
        zone_number: Zone number (1-6)
    """
    try:
        await client.power_off(zone_number)
        return CommandResponse(
            success=True, message=f"Zone {zone_number} powered off"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{zone_number}/volume", response_model=CommandResponse)
async def set_volume(
    zone_number: int,
    request: VolumeRequest,
    client: NuVoClient = Depends(get_client),
):
    """
    Set zone volume.

    Args:
        zone_number: Zone number (1-6)
        request: Volume level (0-79)
    """
    try:
        if not 0 <= request.volume <= 79:
            raise HTTPException(
                status_code=422, detail="Volume must be between 0 and 79"
            )

        await client.set_volume(request.volume, zone_number)
        return CommandResponse(
            success=True,
            message=f"Zone {zone_number} volume set to {request.volume}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{zone_number}/mute", response_model=CommandResponse)
async def toggle_mute(zone_number: int, client: NuVoClient = Depends(get_client)):
    """
    Toggle zone mute.

    Args:
        zone_number: Zone number (1-6)
    """
    try:
        await client.mute_toggle(zone_number)
        return CommandResponse(success=True, message=f"Zone {zone_number} mute toggled")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{zone_number}/source", response_model=CommandResponse)
async def set_source(
    zone_number: int,
    request: SourceRequest,
    client: NuVoClient = Depends(get_client),
):
    """
    Set zone source.

    Args:
        zone_number: Zone number (1-6)
        request: Source GUID
    """
    try:
        # First set the zone as active
        zones = await client.get_zones()
        zone = next((z for z in zones if z.zone_number == zone_number), None)
        if not zone:
            raise HTTPException(status_code=404, detail=f"Zone {zone_number} not found")

        await client.set_zone(zone.guid)
        await client.set_source(request.source_guid)

        return CommandResponse(
            success=True, message=f"Zone {zone_number} source changed"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
