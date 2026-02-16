"""Navigate MusicPort menu to find local music."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_navigation():
    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        print("=== Menu Navigation Test ===\n")

        # Try different BrowsePickList variations
        commands_to_try = [
            "BrowsePickList",
            "BrowsePickList 0",
            "BrowsePickList Music",
            "BrowseNowPlaying",
            "GetBrowseContext",
            "BrowseMusicLibrary",
            "SetBrowseMode Music",
            "SetContentType Music",
        ]

        for cmd in commands_to_try:
            print(f"Trying: {cmd}")
            try:
                response = await client._execute_command(cmd)
                if response and not any('Error' in str(r) or 'Unknown' in str(r) for r in response):
                    print(f"  [OK] SUCCESS - Response ({len(response)} lines):")
                    for line in response[:5]:
                        print(f"    {line}")
                else:
                    print(f"  [FAIL] Error: {response[0] if response else 'No response'}")
            except Exception as e:
                print(f"  [FAIL] Exception: {e}")
            print()

        await client.disconnect()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_navigation())
