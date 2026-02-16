"""Source information endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends

from nuvo_sdk import NuVoClient
from ..dependencies import get_client
from ..models import SourceResponse

router = APIRouter(prefix="/sources", tags=["System"])


@router.get("", response_model=List[SourceResponse])
async def list_sources(client: NuVoClient = Depends(get_client)):
    """
    Get all sources.

    Returns:
        List of available sources
    """
    try:
        sources = await client.get_sources()
        return [
            SourceResponse(
                guid=s.guid,
                name=s.name,
                source_id=s.source_id,
                is_smart=s.is_smart,
                is_network=s.is_network,
                zone_count=s.zone_count,
            )
            for s in sources
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: int, client: NuVoClient = Depends(get_client)):
    """
    Get specific source by ID.

    Args:
        source_id: Source ID (1-6)

    Returns:
        Source information
    """
    try:
        sources = await client.get_sources()
        for s in sources:
            if s.source_id == source_id:
                return SourceResponse(
                    guid=s.guid,
                    name=s.name,
                    source_id=s.source_id,
                    is_smart=s.is_smart,
                    is_network=s.is_network,
                    zone_count=s.zone_count,
                )
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
