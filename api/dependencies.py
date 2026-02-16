"""Shared dependencies for API routes."""

import logging
from typing import Optional
from nuvo_sdk import NuVoClient
from nuvo_sdk.mcs_client_simple import SimpleMCSClient as MCSClient
from .config import settings

logger = logging.getLogger(__name__)

# Global client instances
_client: Optional[NuVoClient] = None
_mcs_client: Optional[MCSClient] = None


async def get_client() -> NuVoClient:
    """
    Get the shared NuVo client instance.

    Returns:
        NuVoClient instance

    Raises:
        HTTPException: 503 if NuVo client not connected
    """
    from fastapi import HTTPException

    global _client
    logging.info(f"[Dependencies] get_client called - _client is None: {_client is None}")
    if _client is not None:
        logging.info(f"[Dependencies] _client._connected: {_client._connected}")

    if _client is None:
        logging.error("[Dependencies] _client is None! Device not initialized")
        raise HTTPException(
            status_code=503,
            detail="NuVo device not available. The device may be offline or failed to connect during startup."
        )

    # If connection is down, try to reconnect
    if not _client._connected:
        logging.info("[Dependencies] MRAD connection is down, attempting reconnect...")
        try:
            await _client.connect()
            logging.info("[Dependencies] MRAD reconnected successfully")
        except Exception as e:
            logging.error(f"[Dependencies] MRAD reconnection failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"NuVo device connection is down and reconnection failed: {str(e)}"
            )

    return _client


async def set_client(client: NuVoClient) -> None:
    """
    Set the global client instance.

    Args:
        client: NuVoClient instance
    """
    global _client
    _client = client


async def get_client_or_none() -> Optional[NuVoClient]:
    """
    Get client if available, None otherwise.

    Returns:
        NuVoClient or None
    """
    global _client
    return _client


async def get_mcs_client() -> MCSClient:
    """
    Get the shared MCS client instance.

    Returns:
        MCSClient instance

    Raises:
        HTTPException: 503 if MCS client not connected
    """
    from fastapi import HTTPException

    global _mcs_client
    if _mcs_client is None:
        raise HTTPException(
            status_code=503,
            detail="Music Control Server (MCS) not available. The MCS service may not be running or failed to connect during startup."
        )

    # If connection is down, try to reconnect
    if not _mcs_client._connected:
        logging.info("[Dependencies] MCS connection is down, attempting reconnect...")
        try:
            await _mcs_client.reconnect()
            logging.info("[Dependencies] MCS reconnected successfully")
        except Exception as e:
            logging.error(f"[Dependencies] MCS reconnection failed: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Music Control Server (MCS) connection is down and reconnection failed: {str(e)}"
            )

    return _mcs_client


async def set_mcs_client(client: MCSClient) -> None:
    """
    Set the global MCS client instance.

    Args:
        client: MCSClient instance
    """
    global _mcs_client
    _mcs_client = client


async def get_mcs_client_or_none() -> Optional[MCSClient]:
    """
    Get MCS client if available, None otherwise.

    Returns:
        MCSClient or None
    """
    global _mcs_client
    return _mcs_client
