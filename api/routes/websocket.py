"""WebSocket endpoint for real-time updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_manager import websocket_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time state updates.

    Clients connect here to receive state change events as they happen.

    Message format:
    {
        "type": "state_change",
        "target": "Zone_1",
        "property": "Volume",
        "value": "50",
        "timestamp": 1234567890.123
    }
    """
    await websocket_manager.connect(websocket)

    try:
        # Keep connection alive
        while True:
            # Wait for any client messages (ping/pong)
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(data)

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)
