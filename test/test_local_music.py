"""Test local music library browsing on MusicPort."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_music_library():
    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        print("=== Testing Music Library Commands ===\n")

        # Try BrowsePickList without being in radio mode
        # This might show music library instead of radio stations
        print("1. BrowsePickList (default):")
        response = await client._execute_command("BrowsePickList")
        print(f"Response ({len(response)} lines):")
        for line in response[:10]:
            print(f"  {line}")
        print()

        # Try setting music filter
        print("2. SetMusicFilter (empty - show all):")
        response = await client._execute_command("SetMusicFilter ")
        print(f"Response: {response[:5]}")
        print()

        # Try browsing music
        print("3. BrowseMusic command:")
        response = await client._execute_command("BrowseMusic")
        print(f"Response ({len(response)} lines):")
        for line in response[:10]:
            print(f"  {line}")
        print()

        # Try getting music categories
        print("4. GetMusicTypes:")
        response = await client._execute_command("GetMusicTypes")
        print(f"Response: {response[:10]}")
        print()

        # Try PlayAllMusic
        print("5. PlayAllMusic command:")
        response = await client._execute_command("PlayAllMusic")
        print(f"Response: {response}")

        await client.disconnect()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_music_library())
