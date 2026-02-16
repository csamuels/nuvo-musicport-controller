"""Debug MCS GetStatus response to see what it actually returns."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def main():
    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        # Try to play a station first
        print("\n[DEBUG] Playing a station (Hot 97)...")
        try:
            await client.play_radio_station("e6f62e2c-ec94-d9b7-58ee-563466c3604f")
        except Exception as e:
            print(f"[DEBUG] Play failed: {e}")

        await asyncio.sleep(3)

        # Get raw status response
        print("\n[DEBUG] Getting raw status response...")
        response = await client._execute_command("GetStatus")

        print(f"\n[DEBUG] GetStatus returned {len(response)} lines:")
        for i, line in enumerate(response):
            print(f"  Line {i}: {repr(line)}")

        # Try parsed status
        print("\n[DEBUG] Getting parsed status...")
        status = await client.get_status()
        print(f"[DEBUG] Parsed status: {status}")

        await client.disconnect()

    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
