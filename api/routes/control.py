"""System control endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from nuvo_sdk import NuVoClient, MCSClient
from ..dependencies import get_client, get_client_or_none, get_mcs_client
from ..models import CommandResponse, SystemStatusResponse, ZoneResponse, SourceResponse
from ..config import settings

router = APIRouter(prefix="/control", tags=["System"])


@router.get("/health")
async def get_health():
    """
    Health check endpoint.

    Returns:
        Health status and connected device information
    """
    client = await get_client_or_none()
    return {
        "status": "healthy" if client and client._connected else "disconnected",
        "device": settings.nuvo_host,
    }


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


class PlayRadioStationRequest(BaseModel):
    """Request to play a radio station on Music Server A in party mode."""
    station_name: str
    music_server_instance: str = "Music_Server_A"


async def _retry_with_delay(func, max_attempts=3, delay=1.0, backoff=1.5):
    """Retry a function with exponential backoff."""
    import asyncio

    for attempt in range(max_attempts):
        try:
            result = await func()
            return result
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = delay * (backoff ** attempt)
            print(f"[Retry] Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
            await asyncio.sleep(wait_time)


@router.post("/play-radio-station", response_model=CommandResponse)
async def play_radio_station(
    request: PlayRadioStationRequest,
    nuvo_client: NuVoClient = Depends(get_client),
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    One-click radio station playback.

    This orchestrates multiple steps:
    1. Enables party mode (all zones play same source)
    2. Gets the party mode host zone
    3. Sets host zone source to Music Server A
    4. Navigates Music Server A to play the radio station

    Args:
        request: Station name/call sign and optional Music Server instance

    Returns:
        Command execution result
    """
    import asyncio

    # Wrap everything in a timeout to prevent hanging forever
    try:
        return await asyncio.wait_for(
            _play_radio_station_impl(request, nuvo_client, mcs_client),
            timeout=45.0  # 45 second hard timeout
        )
    except asyncio.TimeoutError:
        print(f"[PlayRadio] Operation timed out after 45 seconds")
        raise HTTPException(
            status_code=504,
            detail="Operation timed out. The Music Server may be unresponsive or the device is too slow. Please try again or check that the Music Server service is running."
        )


async def _play_radio_station_impl(
    request: PlayRadioStationRequest,
    nuvo_client: NuVoClient,
    mcs_client: MCSClient
):
    """Internal implementation of play_radio_station with timeout protection."""
    import asyncio

    try:
        # Step 1: Enable party mode if not already active
        status = await nuvo_client.get_status()
        party_mode_active = any(z.party_mode in ['Host', 'Slave'] for z in status.zones)

        if not party_mode_active:
            await nuvo_client.party_mode_toggle()
            # Wait for party mode to activate
            import asyncio
            await asyncio.sleep(0.5)
            # Refresh status to get host zone
            status = await nuvo_client.get_status()

        # Step 2: Find the host zone (retry a few times if needed)
        host_zone = None
        for attempt in range(3):
            host_zone = next((z for z in status.zones if z.party_mode == 'Host'), None)
            if host_zone:
                break
            if attempt < 2:
                import asyncio
                await asyncio.sleep(0.5)
                status = await nuvo_client.get_status()

        if not host_zone:
            raise HTTPException(
                status_code=500,
                detail="Could not find party mode host zone after 3 attempts"
            )

        # Step 3: Find Music Server A source
        music_server_source = next(
            (s for s in status.sources if 'Music Server A' in s.name or 'Music_Server_A' in s.name),
            None
        )

        if not music_server_source:
            raise HTTPException(
                status_code=404,
                detail="Music Server A source not found"
            )

        # Step 4: Set host zone to Music Server A source
        await nuvo_client.set_zone(host_zone.guid)
        await nuvo_client.set_source(music_server_source.guid)

        # Step 5: Set MCS instance (if not already set)
        # Check if instance is already set to avoid double-setting after reconnect
        current_instance = mcs_client._current_instance
        if current_instance != request.music_server_instance:
            print(f"[PlayRadio] Setting MCS instance to {request.music_server_instance}")
            await _retry_with_delay(
                lambda: mcs_client.set_instance(request.music_server_instance),
                max_attempts=2,
                delay=1.0
            )
            # Give MCS time to switch instances (old devices are slow)
            print("[PlayRadio] Waiting for MCS to switch instances...")
            await asyncio.sleep(2.0)
        else:
            print(f"[PlayRadio] MCS instance already set to {request.music_server_instance}, skipping")
            # Still give it a moment after reconnect
            await asyncio.sleep(1.0)

        # Browse main menu to find TuneIn (with retry)
        print("[PlayRadio] Browsing main menu...")

        async def browse_with_validation():
            items = await mcs_client.browse_pick_list()
            if not items:
                raise Exception("Menu returned empty")
            return items

        items = await _retry_with_delay(browse_with_validation, max_attempts=2, delay=1.5)
        print(f"[PlayRadio] Got {len(items)} menu items")
        tunein_index = None

        print(f"[PlayRadio] Music Server menu items: {[item.title for item in items]}")

        for item in items:
            if any(keyword in item.title.lower() for keyword in ['tunein', 'radiotime', 'radio']):
                tunein_index = item.index
                print(f"[PlayRadio] Found TuneIn at index {tunein_index}: {item.title}")
                break

        if tunein_index is None:
            menu_items = ", ".join([item.title for item in items])
            print(f"[PlayRadio] TuneIn not found. Available items: {menu_items}")
            raise HTTPException(
                status_code=404,
                detail=f"TuneIn Radio not found in Music Server menu. Available: {menu_items}"
            )

        # Select TuneIn
        print(f"[PlayRadio] Selecting TuneIn (index {tunein_index})...")
        await _retry_with_delay(
            lambda: mcs_client.ack_pick_item(tunein_index),
            max_attempts=3,
            delay=1.0
        )

        # Give MCS time to navigate into TuneIn menu
        print("[PlayRadio] Waiting for TuneIn menu to load...")
        await asyncio.sleep(2.0)

        # Browse TuneIn menu for the station (with retry)
        print("[PlayRadio] Browsing TuneIn stations...")

        async def browse_tunein():
            items = await mcs_client.browse_pick_list()
            if not items:
                raise Exception("TuneIn menu returned empty")
            return items

        items = await _retry_with_delay(browse_tunein, max_attempts=2, delay=2.0)
        station_index = None

        print(f"[PlayRadio] Got {len(items)} TuneIn items")
        print(f"[PlayRadio] First few items: {[item.title for item in items[:5]]}")

        for item in items:
            if request.station_name.lower() in item.title.lower():
                station_index = item.index
                print(f"[PlayRadio] Found station at index {station_index}: {item.title}")
                break

        if station_index is None:
            # Try filtering
            print(f"[PlayRadio] Station not found in list, trying filter: {request.station_name}")
            await _retry_with_delay(
                lambda: mcs_client.set_radio_filter(request.station_name),
                max_attempts=2,
                delay=1.0
            )

            # Give filter time to apply
            await asyncio.sleep(1.5)

            items = await _retry_with_delay(browse_tunein, max_attempts=2, delay=1.5)
            print(f"[PlayRadio] Got {len(items)} filtered items")
            print(f"[PlayRadio] Filtered items: {[item.title for item in items[:5]]}")

            for item in items:
                if request.station_name.lower() in item.title.lower():
                    station_index = item.index
                    print(f"[PlayRadio] Found station after filter at index {station_index}: {item.title}")
                    break

        if station_index is None:
            available_stations = ", ".join([item.title for item in items[:10]])
            print(f"[PlayRadio] Station '{request.station_name}' not found. Available: {available_stations}")
            raise HTTPException(
                status_code=404,
                detail=f"Station '{request.station_name}' not found in TuneIn. Try one of: {available_stations}"
            )

        # Play the station
        print(f"[PlayRadio] Playing station (index {station_index})...")
        await _retry_with_delay(
            lambda: mcs_client.ack_pick_item(station_index),
            max_attempts=3,
            delay=1.0
        )

        # Give it a moment to start playing
        await asyncio.sleep(0.5)

        return CommandResponse(
            success=True,
            message=f"Playing {request.station_name} on Music Server A in party mode"
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = f"{type(e).__name__}: {str(e)}"
        print(f"[PlayRadio] Error: {error_details}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_details)


@router.get("/now-playing")
async def get_now_playing(
    instance: str = "Music_Server_A",
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Get currently playing track/station from Music Server.

    Args:
        instance: Music Server instance (default: Music_Server_A)

    Returns information about what's currently playing on the specified Music Server instance.
    """
    try:
        # Set the instance first
        await mcs_client.set_instance(instance)

        # Get status
        status = await mcs_client.get_status()
        return {
            "instance": instance,
            "now_playing": status.get('now_playing', {}),
            "play_state": status.get('play_state', 'Stopped'),
            "volume": status.get('volume', 0),
            "mute": status.get('mute', False)
        }
    except Exception as e:
        print(f"[NowPlaying] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
