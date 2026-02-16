"""TuneIn Radio station playback."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import asyncio

from nuvo_sdk import NuVoClient, MCSClient
from ..dependencies import get_client, get_mcs_client
from ..models import CommandResponse

router = APIRouter(prefix="/tunein", tags=["Radio"])


class PlayTuneInStationRequest(BaseModel):
    """Request to play a TuneIn radio station."""
    station_name: str
    music_server_instance: str = "Music_Server_A"


@router.post("/play", response_model=CommandResponse)
async def play_tunein_station(
    request: PlayTuneInStationRequest,
    nuvo_client: NuVoClient = Depends(get_client),
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Play a TuneIn radio station directly.

    Steps:
    1. Enable party mode
    2. Set MCS instance
    3. Browse TuneIn radio stations
    4. Find station by name
    5. Play using PlayRadioStation command with GUID
    """
    print(f"[TuneIn] Playing station: {request.station_name}")

    try:
        # 1. Enable party mode (all zones linked to Music Server A)
        print("[TuneIn] Enabling party mode...")
        await nuvo_client.party_mode_toggle()
        await asyncio.sleep(1.5)

        # 2. Set Music Server instance
        print(f"[TuneIn] Setting instance to {request.music_server_instance}")
        await mcs_client.set_instance(request.music_server_instance)
        await asyncio.sleep(1.0)

        # 3. Browse TuneIn radio stations with retry logic
        print("[TuneIn] Browsing radio stations...")
        stations = None
        max_retries = 3

        for attempt in range(max_retries):
            try:
                stations = await mcs_client.browse_pick_list()
                if stations:
                    break
                print(f"[TuneIn] Browse returned empty, retrying... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(1.0)
            except Exception as e:
                print(f"[TuneIn] Browse error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0)
                else:
                    raise

        if not stations:
            raise HTTPException(
                status_code=503,
                detail="Failed to retrieve TuneIn radio station list after multiple attempts"
            )

        print(f"[TuneIn] Found {len(stations)} radio stations")

        # 4. Find the requested station
        station = None
        for s in stations:
            # Match by exact name or partial match
            if (request.station_name.lower() == s.title.lower() or
                request.station_name.lower() in s.title.lower()):
                station = s
                print(f"[TuneIn] Matched station: {s.title}")
                break

        if not station:
            # Try fuzzy match
            for s in stations:
                # Extract just the station name (before parentheses)
                station_name = s.title.split('(')[0].strip()
                if request.station_name.lower() in station_name.lower():
                    station = s
                    print(f"[TuneIn] Fuzzy matched station: {s.title}")
                    break

        if not station:
            available = ", ".join([s.title for s in stations[:10]])
            raise HTTPException(
                status_code=404,
                detail=f"Station '{request.station_name}' not found. First 10 available: {available}"
            )

        # 5. Play the station using its GUID
        print(f"[TuneIn] Playing station: {station.title} (GUID: {station.guid})")
        await mcs_client.play_radio_station(station.guid)

        await asyncio.sleep(1.5)

        print(f"[TuneIn] Successfully started: {station.title}")

        return CommandResponse(
            success=True,
            message=f"Playing {station.title} on TuneIn Radio"
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = f"{type(e).__name__}: {str(e)}"
        print(f"[TuneIn] Error: {error_details}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_details)
