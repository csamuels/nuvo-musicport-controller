#!/usr/bin/env python3
"""Test WebSocket real-time event broadcasting."""

import asyncio
import websockets
import json


async def test_websocket():
    """Connect to WebSocket and print events."""
    uri = "ws://localhost:8000/ws"

    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:
        print("Connected! Waiting for events...")
        print("(Change zone settings using the API to see events)\n")

        try:
            while True:
                message = await websocket.recv()
                event = json.loads(message)

                print(
                    f"Event: {event['target']} {event['property']}={event['value']}"
                )

        except KeyboardInterrupt:
            print("\nDisconnected")


if __name__ == "__main__":
    asyncio.run(test_websocket())
