"""TuneIn Radio Station Validation - Filter out dead/invalid stations."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio

from nuvo_sdk.mcs_client_simple import SimpleMCSClient as MCSClient
from ..dependencies import get_mcs_client

router = APIRouter(prefix="/tunein", tags=["Radio"])


class StationValidationResult(BaseModel):
    """Result of station validation."""
    guid: str
    title: str
    appears_valid: bool
    message: str


@router.get("/validate-stations", response_model=List[StationValidationResult])
async def validate_all_stations(
    instance: str = "Music_Server_A",
    quick_check: bool = True,
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Validate all TuneIn radio stations and identify dead/invalid ones.

    Quick check (default): Just verifies the station returns a "Tuning to..."
    message, which indicates the MusicPort acknowledges it.

    Full check (slow): Actually plays each station and waits to see if playback
    starts. WARNING: This will interrupt current playback and take a long time!

    Args:
        instance: Music Server instance
        quick_check: If True, just check for "Tuning to" message (fast)
                    If False, actually try playing and wait (slow, disruptive)

    Returns:
        List of validation results for each station
    """
    try:
        await mcs_client.set_instance(instance)

        # Browse all stations with retry logic
        stations = None
        max_retries = 3

        for attempt in range(max_retries):
            try:
                stations = await mcs_client.browse_pick_list()
                if stations:
                    break
                await asyncio.sleep(1.0)
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0)
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Failed to browse stations after {max_retries} attempts: {str(e)}"
                    )

        if not stations:
            raise HTTPException(
                status_code=404,
                detail="No radio stations found"
            )

        results = []

        for station in stations:
            guid = station.guid
            title = station.title

            if quick_check:
                # Quick validation: Just send PlayRadioStation and check response
                try:
                    response = await mcs_client._execute_command(f"PlayRadioStation {guid}")

                    # Look for "Tuning to" message in response
                    tuning_found = False
                    for line in response:
                        if "Tuning to" in line and title.split()[0] in line:
                            tuning_found = True
                            break

                    if tuning_found:
                        results.append(StationValidationResult(
                            guid=guid,
                            title=title,
                            appears_valid=True,
                            message="Station acknowledged by device"
                        ))
                    else:
                        results.append(StationValidationResult(
                            guid=guid,
                            title=title,
                            appears_valid=False,
                            message="No tuning confirmation received"
                        ))

                except Exception as e:
                    results.append(StationValidationResult(
                        guid=guid,
                        title=title,
                        appears_valid=False,
                        message=f"Error: {str(e)}"
                    ))

                # Small delay between checks
                await asyncio.sleep(0.5)

            else:
                # Full validation: Actually play and check (slow!)
                # TODO: Implement full playback verification if needed
                results.append(StationValidationResult(
                    guid=guid,
                    title=title,
                    appears_valid=True,
                    message="Full validation not yet implemented"
                ))

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/working-stations")
async def get_working_stations(
    instance: str = "Music_Server_A",
    mcs_client: MCSClient = Depends(get_mcs_client)
):
    """
    Get only the working/valid TuneIn radio stations (filtered list).

    This performs quick validation and returns only stations that appear to work.

    Args:
        instance: Music Server instance

    Returns:
        List of working stations (same format as browse endpoint)
    """
    try:
        # Get validation results
        validation_results = await validate_all_stations(
            instance=instance,
            quick_check=True,
            mcs_client=mcs_client
        )

        # Browse all stations with retry logic
        await mcs_client.set_instance(instance)
        all_stations = None
        max_retries = 3

        for attempt in range(max_retries):
            try:
                all_stations = await mcs_client.browse_pick_list()
                if all_stations:
                    break
                await asyncio.sleep(1.0)
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0)
                else:
                    raise

        if not all_stations:
            all_stations = []

        # Filter to only valid ones
        valid_guids = {r.guid for r in validation_results if r.appears_valid}

        working_stations = [
            {
                "index": s.index,
                "title": s.title,
                "guid": s.guid,
                "item_type": s.item_type,
                "metadata": s.metadata
            }
            for s in all_stations
            if s.guid in valid_guids
        ]

        return working_stations

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
