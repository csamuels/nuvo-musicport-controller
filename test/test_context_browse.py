"""Test if BrowseRadioStations is context-sensitive."""

import asyncio
import re
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_context_sensitive_browse():
    """Test if browse results change based on navigation."""

    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        # Test 1: Browse at initial state
        print("=" * 60)
        print("TEST 1: BrowseRadioStations at initial state")
        print("=" * 60)
        response = await client._execute_command("BrowseRadioStations")
        xml = '\n'.join(response)
        print(f"Response length: {len(xml)} chars")
        print(f"First station: {xml[100:200]}")

        # Count stations
        station_count = len(re.findall(r'<RadioStation', xml))
        print(f"Number of stations: {station_count}\n")

        # Test 2: Try to navigate using Navigate command
        print("=" * 60)
        print("TEST 2: Try Navigate command")
        print("=" * 60)

        # Try different navigate attempts
        navigate_cmds = [
            "Navigate TuneIn",
            "Navigate 0",  # Navigate to index 0
            "Navigate /TuneIn",
            "SetNavigationRoot TuneIn",
        ]

        for nav_cmd in navigate_cmds:
            try:
                print(f"Trying: {nav_cmd}")
                response = await client._execute_command(nav_cmd, retry_on_error=False)
                if "Error" not in str(response):
                    print(f"  SUCCESS: {response[:2]}")

                    # Try browsing after navigation
                    print("  Browsing after navigation...")
                    response = await client._execute_command("BrowseRadioStations")
                    xml = '\n'.join(response)
                    station_count = len(re.findall(r'<RadioStation', xml))
                    print(f"  Now shows {station_count} stations")

                    if xml[100:200] != xml[100:200]:  # Different from before
                        print("  [OK] Browse results changed after navigation!")
                    break
                else:
                    print(f"  Failed: {response[0]}")
            except Exception as e:
                print(f"  Exception: {e}")

        print()

        # Test 3: Check what browse commands exist for different media types
        print("=" * 60)
        print("TEST 3: Test other Browse* commands")
        print("=" * 60)

        for cmd in ["BrowsePlaylists", "BrowsePodcasts", "BrowseGenres", "BrowseFavorites"]:
            try:
                response = await client._execute_command(cmd, retry_on_error=False)
                if "Error" not in response[0]:
                    print(f"[OK] {cmd} works!")
                else:
                    print(f"[FAIL] {cmd}: {response[0]}")
            except:
                pass

        await client.disconnect()

    except Exception as e:
        print(f"\n!!! ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client._connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_context_sensitive_browse())
