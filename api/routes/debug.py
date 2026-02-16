"""Debug endpoints for troubleshooting."""

from fastapi import APIRouter, HTTPException
from ..dependencies import get_client_or_none, get_mcs_client_or_none

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.post("/reconnect-mrad")
async def force_reconnect_mrad():
    """Force MRAD client to reconnect."""
    client = await get_client_or_none()

    if client is None:
        return {"error": "MRAD client not initialized"}

    try:
        print("[Debug] Forcing MRAD reconnection...")

        # Disconnect if connected
        if client._connected:
            print("[Debug] Disconnecting existing connection...")
            await client.disconnect()

        # Reconnect
        print("[Debug] Connecting...")
        await client.connect()

        print("[Debug] MRAD reconnected successfully")

        return {
            "success": True,
            "message": "MRAD reconnected successfully",
            "connected": client._connected
        }

    except Exception as e:
        print(f"[Debug] Reconnection failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "connected": client._connected if client else False
        }


@router.post("/reconnect-mcs")
async def force_reconnect_mcs():
    """Force MCS client to reconnect."""
    client = await get_mcs_client_or_none()

    if client is None:
        return {"error": "MCS client not initialized"}

    try:
        print("[Debug] Forcing MCS reconnection...")
        await client.reconnect()
        print("[Debug] MCS reconnected successfully")

        return {
            "success": True,
            "message": "MCS reconnected successfully",
            "connected": client._connected
        }

    except Exception as e:
        print(f"[Debug] Reconnection failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            "success": False,
            "error": str(e),
            "connected": client._connected if client else False
        }
