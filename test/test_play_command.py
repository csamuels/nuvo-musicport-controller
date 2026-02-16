"""Test the correct command to play a specific radio station."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_play_commands():
    """Test different ways to play a radio station."""

    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        # Get the list of stations
        print("Getting radio stations...")
        items = await client.browse_pick_list()
        print(f"Found {len(items)} stations\n")

        # Try to play Frank Sinatra Radio (index 21)
        frank = [s for s in items if 'Frank Sinatra' in s.title][0]
        print(f"Target station: {frank.title}")
        print(f"  GUID: {frank.guid}")
        print(f"  Index: {frank.index}\n")

        # Test 1: Try PlayRadioStation command with name
        print("=" * 60)
        print("TEST 1: PlayRadioStation with name")
        print("=" * 60)
        response = await client._execute_command(f'PlayRadioStation "{frank.title}"')
        print(f"Response: {response[:3] if len(response) > 3 else response}\n")

        await asyncio.sleep(3)

        # Test 2: Try PlayRadioStation with GUID
        print("=" * 60)
        print("TEST 2: PlayRadioStation with GUID")
        print("=" * 60)
        response = await client._execute_command(f'PlayRadioStation {frank.guid}')
        print(f"Response: {response[:3] if len(response) > 3 else response}\n")

        await asyncio.sleep(3)

        # Test 3: Check status
        print("=" * 60)
        print("TEST 3: GetStatus to see what's playing")
        print("=" * 60)
        status = await client.get_status()
        print(f"Play state: {status.get('play_state')}")
        print(f"Now playing: {status.get('now_playing')}\n")

        await client.disconnect()

    except Exception as e:
        print(f"\n!!! ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client._connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_play_commands())
