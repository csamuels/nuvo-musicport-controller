"""Local music library endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from nuvo_sdk.mcs_client_simple import SimpleMCSClient as MCSClient
from ..dependencies import get_mcs_client
from ..models import CommandResponse

router = APIRouter(prefix="/library", tags=["Music Library"])


# ==================== RESPONSE MODELS ====================

class TrackResponse(BaseModel):
    """Track information."""
    guid: str
    name: str
    artist: str
    album: str
    album_guid: str
    duration: str
    track_number: int
    queue_index: int = 0
    is_now_playing: bool = False


class AlbumResponse(BaseModel):
    """Album information."""
    guid: str
    name: str
    artist: str
    unique_name: str


class ArtistResponse(BaseModel):
    """Artist information."""
    guid: str
    name: str


# ==================== REQUEST MODELS ====================

class PlayByGuidRequest(BaseModel):
    """Request to play media by GUID."""
    guid: str
    instance: str = "Music_Server_A"


# ==================== ENDPOINTS ====================

@router.get("/queue", response_model=List[TrackResponse])
async def get_queue(
    instance: str = "Music_Server_A",
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Get the current playback queue.

    Args:
        instance: Music Server instance (default: Music_Server_A)

    Returns:
        List of tracks in the queue with full metadata
    """
    try:
        await mcs_client.set_instance(instance)
        tracks = await mcs_client.browse_now_playing()

        return [
            TrackResponse(
                guid=t['guid'],
                name=t['name'],
                artist=t['artist'],
                album=t['album'],
                album_guid=t['album_guid'],
                duration=t['duration'],
                track_number=t['track_number'],
                queue_index=t['queue_index'],
                is_now_playing=t['is_now_playing']
            )
            for t in tracks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/albums", response_model=List[AlbumResponse])
async def get_albums(
    instance: str = "Music_Server_A",
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Browse all albums in the local music library.

    Args:
        instance: Music Server instance (default: Music_Server_A)

    Returns:
        List of all albums with metadata
    """
    try:
        await mcs_client.set_instance(instance)
        albums = await mcs_client.browse_albums()

        return [
            AlbumResponse(
                guid=a['guid'],
                name=a['name'],
                artist=a['artist'],
                unique_name=a['unique_name']
            )
            for a in albums
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/artists", response_model=List[ArtistResponse])
async def get_artists(
    instance: str = "Music_Server_A",
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Browse all artists in the local music library.

    Args:
        instance: Music Server instance (default: Music_Server_A)

    Returns:
        List of all artists
    """
    try:
        await mcs_client.set_instance(instance)
        artists = await mcs_client.browse_artists()

        return [
            ArtistResponse(
                guid=a['guid'],
                name=a['name']
            )
            for a in artists
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/albums/{album_guid}/tracks", response_model=List[TrackResponse])
async def get_album_tracks(
    album_guid: str,
    instance: str = "Music_Server_A",
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Get all tracks in a specific album.

    Args:
        album_guid: Album GUID
        instance: Music Server instance (default: Music_Server_A)

    Returns:
        List of tracks in the album
    """
    try:
        await mcs_client.set_instance(instance)
        tracks = await mcs_client.browse_album_titles(album_guid)

        return [
            TrackResponse(
                guid=t['guid'],
                name=t['name'],
                artist=t['artist'],
                album=t['album'],
                album_guid=album_guid,
                duration=t['duration'],
                track_number=t['track_number']
            )
            for t in tracks
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/play/track", response_model=CommandResponse)
async def play_track(
    request: PlayByGuidRequest,
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Play a specific track by GUID.

    Args:
        request: Track GUID and instance

    Returns:
        Command execution result
    """
    try:
        await mcs_client.set_instance(request.instance)
        await mcs_client.play_title(request.guid)

        return CommandResponse(
            success=True,
            message=f"Playing track {request.guid}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/play/album", response_model=CommandResponse)
async def play_album(
    request: PlayByGuidRequest,
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Play an entire album by GUID.

    Args:
        request: Album GUID and instance

    Returns:
        Command execution result
    """
    try:
        await mcs_client.set_instance(request.instance)
        await mcs_client.play_album(request.guid)

        return CommandResponse(
            success=True,
            message=f"Playing album {request.guid}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/play/artist", response_model=CommandResponse)
async def play_artist(
    request: PlayByGuidRequest,
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Play all tracks by an artist.

    Args:
        request: Artist GUID and instance

    Returns:
        Command execution result
    """
    try:
        await mcs_client.set_instance(request.instance)
        await mcs_client.play_artist(request.guid)

        return CommandResponse(
            success=True,
            message=f"Playing artist {request.guid}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/play/all", response_model=CommandResponse)
async def play_all_music(
    instance: str = "Music_Server_A",
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Play all music in the library.

    Args:
        instance: Music Server instance (default: Music_Server_A)

    Returns:
        Command execution result
    """
    try:
        await mcs_client.set_instance(instance)
        await mcs_client.play_all_music()

        return CommandResponse(
            success=True,
            message="Playing all music"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
