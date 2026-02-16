"""Test what GetStatus actually returns from the MCS server."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test():
    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        print("Sending GetStatus command...")
        response = await client._execute_command("GetStatus")

        print(f"\nReceived {len(response)} lines:")
        for i, line in enumerate(response):
            print(f"{i+1}: {line}")

        print("\n" + "="*60)
        print("Parsed status:")
        status = await client.get_status()
        import json
        print(json.dumps(status, indent=2))

        await client.disconnect()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
