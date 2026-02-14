"""WebSocket connection manager for broadcasting events."""

import asyncio
import json
from typing import List
from fastapi import WebSocket
from nuvo_sdk.models import StateChangeEvent


class WebSocketManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection to unregister
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, event: StateChangeEvent):
        """
        Broadcast state change event to all connected clients.

        Args:
            event: StateChangeEvent to broadcast
        """
        if not self.active_connections:
            return

        # Convert event to JSON
        message = json.dumps(
            {
                "type": "state_change",
                "target": event.target,
                "property": event.property,
                "value": event.value,
                "timestamp": event.timestamp,
            }
        )

        # Send to all clients (remove disconnected ones)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global manager instance
websocket_manager = WebSocketManager()
