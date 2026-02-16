"""Debug what command is actually sent and what response we get."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def main():
    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        # Try playing a station with detailed logging
        print("\n[DEBUG] Sending PlayRadioStation command...")
        guid = "e6f62e2c-ec94-d9b7-58ee-563466c3604f"  # Hot 97

        # Execute command and capture response
        response = await client._execute_command(f"PlayRadioStation {guid}")

        print(f"\n[DEBUG] PlayRadioStation response ({len(response)} lines):")
        for i, line in enumerate(response):
            print(f"  Line {i}: {repr(line)}")

        # Wait a bit
        print("\n[DEBUG] Waiting 3 seconds...")
        await asyncio.sleep(3)

        # Now try GetStatus
        print("\n[DEBUG] Sending GetStatus command...")
        response = await client._execute_command("GetStatus")

        print(f"\n[DEBUG] GetStatus response ({len(response)} lines):")
        for i, line in enumerate(response):
            print(f"  Line {i}: {repr(line)}")

        await client.disconnect()

    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
