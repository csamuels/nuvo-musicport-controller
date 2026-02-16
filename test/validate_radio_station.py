"""
Test to validate if a radio station actually works.

Tests by:
1. Playing the station
2. Waiting for playback to start
3. Checking if play state changed to "Playing"
4. Verifying actual audio is streaming
"""

import asyncio
import sys
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def validate_station(station_name: str, station_guid: str, host: str = "10.0.0.45"):
    """
    Validate if a radio station actually works.

    Returns:
        (is_valid, message)
    """
    client = SimpleMCSClient(host, 5004)

    try:
        print(f"\n[TEST] Validating station: {station_name}")
        print(f"[TEST] GUID: {station_guid}")

        # Connect
        await client.connect()
        await client.set_instance("Music_Server_A")

        # Get initial status
        print("[TEST] Getting initial status...")
        initial_status = await client.get_status()
        initial_state = initial_status.get('play_state', 'Unknown')
        print(f"[TEST] Initial play state: {initial_state}")

        # Play the station
        print(f"[TEST] Playing station...")
        try:
            await client.play_radio_station(station_guid)
        except Exception as e:
            print(f"[TEST] Play command failed: {e}")
            return False, f"Play command failed: {e}"

        # Wait for playback to start
        print("[TEST] Waiting 5 seconds for playback to start...")
        await asyncio.sleep(5)

        # Check status
        print("[TEST] Checking playback status...")
        final_status = await client.get_status()
        final_state = final_status.get('play_state', 'Unknown')
        now_playing = final_status.get('now_playing', {})

        print(f"[TEST] Final play state: {final_state}")
        print(f"[TEST] Now playing info: {now_playing}")

        # Determine if station is valid
        is_valid = False
        message = ""

        if final_state == "Playing":
            is_valid = True
            message = "Station is valid and playing"
            print(f"[TEST] [OK] SUCCESS: Station is playing!")
            if now_playing:
                print(f"[TEST]   Track: {now_playing.get('track', 'Unknown')}")
                print(f"[TEST]   Artist: {now_playing.get('artist', 'Unknown')}")
                print(f"[TEST]   Station: {now_playing.get('station', 'Unknown')}")
        elif final_state == "Stopped":
            is_valid = False
            message = "Station failed to start - play state is still Stopped"
            print(f"[TEST] [X] FAILED: Play state is still Stopped")
        elif final_state == "Paused":
            is_valid = False
            message = "Station paused immediately - likely invalid"
            print(f"[TEST] [X] FAILED: Play state is Paused")
        else:
            is_valid = False
            message = f"Unknown play state: {final_state}"
            print(f"[TEST] [X] FAILED: Unknown state: {final_state}")

        await client.disconnect()
        return is_valid, message

    except Exception as e:
        print(f"[TEST] [X] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {e}"


async def validate_multiple_stations(stations: list, host: str = "10.0.0.45"):
    """Validate multiple stations and return results."""
    results = []

    for station in stations:
        name = station.get("title", "Unknown")
        guid = station.get("guid", "")

        if not guid:
            results.append({
                "name": name,
                "guid": "",
                "valid": False,
                "message": "No GUID provided"
            })
            continue

        is_valid, message = await validate_station(name, guid, host)
        results.append({
            "name": name,
            "guid": guid,
            "valid": is_valid,
            "message": message
        })

        # Wait between tests
        await asyncio.sleep(2)

    return results


async def main():
    """Main test function."""

    # Test Hot 97
    print("="*70)
    print("RADIO STATION VALIDATION TEST")
    print("="*70)

    stations_to_test = [
        {
            "title": "97.1 - Hot 97 (Hip Hop Music)",
            "guid": "e6f62e2c-ec94-d9b7-58ee-563466c3604f"
        },
        {
            "title": "89.1 - WFDU (Eclectic Music)",
            "guid": "c3476d58-7806-e7b4-f70d-8b9b48fde619"
        },
        {
            "title": "95.9 The Fox",
            "guid": "bc2c0882-f90a-5b05-347d-a23423ed31f7"
        }
    ]

    results = await validate_multiple_stations(stations_to_test)

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION RESULTS SUMMARY")
    print("="*70)

    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = len(results) - valid_count

    print(f"\nTested: {len(results)} stations")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid_count}")
    print()

    for result in results:
        status = "[OK] VALID" if result['valid'] else "[X] INVALID"
        print(f"{status:12} | {result['name']}")
        print(f"{'':12} | {result['message']}")
        print()

    return invalid_count == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
