"""Music Server control endpoints (MCS protocol)."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from nuvo_sdk import MCSClient
from ..dependencies import get_mcs_client

router = APIRouter(prefix="/music-servers", tags=["Music"])


# ==================== REQUEST/RESPONSE MODELS ====================

class PickListItemResponse(BaseModel):
    """Pick list item (station, album, playlist, etc.)."""
    index: int
    title: str
    guid: str
    item_type: str
    metadata: Dict[str, str]


class MusicServerStatusResponse(BaseModel):
    """Music Server status."""
    server_name: Optional[str]
    instance_name: Optional[str]
    running: bool
    volume: int
    mute: bool
    play_state: str
    now_playing: Dict[str, Any]
    supported_types: List[str]


class SetInstanceRequest(BaseModel):
    """Request to select Music Server instance."""
    instance_name: str


class SetFilterRequest(BaseModel):
    """Request to set content filter."""
    filter_value: str = ""


class AckPickItemRequest(BaseModel):
    """Request to select an item."""
    index: int


class AddToQueueRequest(BaseModel):
    """Request to add item to queue."""
    guid: str


class SavePlaylistRequest(BaseModel):
    """Request to save playlist."""
    name: str


class SetVolumeRequest(BaseModel):
    """Request to set volume."""
    volume: int


class PlayRadioStationRequest(BaseModel):
    """Request to play a specific radio station."""
    instance: str = "Music_Server_A"
    station_name: str


# ==================== ENDPOINTS ====================

@router.get("/instances", response_model=List[str])
async def get_instances(client: MCSClient = Depends(get_mcs_client)):
    """
    Get list of available Music Server instances.

    Returns:
        List of instance names (e.g., ["Music_Server_A", "Music_Server_B"])
    """
    try:
        instances = await client.browse_instances()
        return instances
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instance")
async def set_instance(
    request: SetInstanceRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """
    Select which Music Server instance to control.

    Args:
        request: Instance name to select
    """
    try:
        await client.set_instance(request.instance_name)
        return {"success": True, "instance": request.instance_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status(instance: str = "Music_Server_A", client: MCSClient = Depends(get_mcs_client)):
    """
    Get current Music Server status.

    Args:
        instance: Music Server instance (default: Music_Server_A)

    Returns:
        Server status including now playing info
    """
    try:
        # Set instance first
        await client.set_instance(instance)

        # Get status
        status = await client.get_status()

        # Return simplified status (remove complex response model for now)
        return {
            "instance": instance,
            "volume": status.get('volume', 0),
            "mute": status.get('mute', False),
            "play_state": status.get('play_state', 'Unknown'),
            "now_playing": status.get('now_playing', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browse", response_model=List[PickListItemResponse])
async def browse_content(
    instance: str = "Music_Server_A",
    client: MCSClient = Depends(get_mcs_client)
):
    """
    Browse current content menu.

    Returns list of items (radio stations, albums, playlists, etc.)
    depending on the current navigation state.

    Args:
        instance: Music Server instance to browse (default: Music_Server_A)

    Returns:
        List of browseable items
    """
    try:
        # Set the instance first
        await client.set_instance(instance)

        # Browse radio stations
        items = await client.browse_pick_list()
        return [
            PickListItemResponse(
                index=item.index,
                title=item.title,
                guid=item.guid,
                item_type=item.item_type,
                metadata=item.metadata
            )
            for item in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/select")
async def select_item(
    request: AckPickItemRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """
    Select/acknowledge an item from the browse menu.

    This is how you:
    - Select a radio station
    - Choose a Spotify playlist
    - Navigate into a folder/category
    - Play an album or track

    Args:
        request: Index of item to select
    """
    try:
        await client.ack_pick_item(request.index)
        return {"success": True, "index": request.index}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter/radio")
async def set_radio_filter(
    request: SetFilterRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """
    Set radio station filter/search.

    Args:
        request: Filter value (empty string to clear)
    """
    try:
        await client.set_radio_filter(request.filter_value)
        return {"success": True, "filter": request.filter_value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter/music")
async def set_music_filter(
    request: SetFilterRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """
    Set music library filter/search.

    Args:
        request: Filter value (empty string to clear)
    """
    try:
        await client.set_music_filter(request.filter_value)
        return {"success": True, "filter": request.filter_value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/add")
async def add_to_queue(
    request: AddToQueueRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """Add item to playback queue."""
    try:
        await client.add_to_queue(request.guid)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/clear")
async def clear_queue(client: MCSClient = Depends(get_mcs_client)):
    """Clear playback queue."""
    try:
        await client.clear_now_playing()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/queue/{index}")
async def remove_queue_item(
    index: int,
    client: MCSClient = Depends(get_mcs_client)
):
    """Remove item from queue by index."""
    try:
        await client.remove_now_playing_item(index)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playlist/save")
async def save_playlist(
    request: SavePlaylistRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """Save current queue as a playlist."""
    try:
        await client.save_playlist(request.name)
        return {"success": True, "name": request.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/volume")
async def set_volume(
    request: SetVolumeRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """Set Music Server volume (0-100)."""
    try:
        await client.set_volume(request.volume)
        return {"success": True, "volume": request.volume}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/play/all")
async def play_all(client: MCSClient = Depends(get_mcs_client)):
    """Play all music."""
    try:
        await client.play_all_music()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/play/radio-station")
async def play_radio_station(
    request: PlayRadioStationRequest,
    client: MCSClient = Depends(get_mcs_client)
):
    """
    Navigate to and play a specific radio station.

    This handles the complex flow of:
    1. Selecting the Music Server instance
    2. Finding and selecting TuneIn Radio
    3. Finding the station by name
    4. Playing the station

    Args:
        request: Instance name and station name/call sign
    """
    try:
        # Step 1: Set the instance
        await client.set_instance(request.instance)

        # Step 2: Browse main menu to find TuneIn/RadioTime
        items = await client.browse_pick_list()
        tunein_index = None

        for item in items:
            # Look for TuneIn, RadioTime, or similar
            if any(keyword in item.title.lower() for keyword in ['tunein', 'radiotime', 'radio']):
                tunein_index = item.index
                break

        if tunein_index is None:
            raise HTTPException(
                status_code=404,
                detail="TuneIn Radio not found in Music Server menu"
            )

        # Step 3: Select TuneIn
        await client.ack_pick_item(tunein_index)

        # Step 4: Browse TuneIn menu to find the station
        items = await client.browse_pick_list()
        station_index = None

        for item in items:
            # Match by name or call sign (case-insensitive)
            if request.station_name.lower() in item.title.lower():
                station_index = item.index
                break

        if station_index is None:
            # Try filtering for the station
            await client.set_radio_filter(request.station_name)
            items = await client.browse_pick_list()

            for item in items:
                if request.station_name.lower() in item.title.lower():
                    station_index = item.index
                    break

        if station_index is None:
            raise HTTPException(
                status_code=404,
                detail=f"Station '{request.station_name}' not found in TuneIn menu"
            )

        # Step 5: Select and play the station
        await client.ack_pick_item(station_index)

        return {
            "success": True,
            "instance": request.instance,
            "station": request.station_name,
            "tunein_index": tunein_index,
            "station_index": station_index
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
