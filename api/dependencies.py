"""Shared dependencies for API routes."""

from typing import Optional
from nuvo_sdk import NuVoClient
from .config import settings

# Global client instance
_client: Optional[NuVoClient] = None


async def get_client() -> NuVoClient:
    """
    Get the shared NuVo client instance.

    Returns:
        NuVoClient instance
    """
    global _client
    if _client is None or not _client._connected:
        raise RuntimeError("NuVo client not connected")
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
