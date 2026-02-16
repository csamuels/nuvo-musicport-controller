"""Test TuneIn play with reconnection logic."""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_tunein_play():
    """Test TuneIn play endpoint with different stations."""

    test_stations = [
        "89.1 - WFDU (Eclectic Music)",
        "95.3 - WBAB (Classic Rock Music)",
        "97.1 - Hot 97 (Hip Hop Music)"
    ]

    print("\n" + "=" * 60)
    print("TESTING TUNEIN PLAY WITH RECONNECTION LOGIC")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}\n")

    passed = 0
    failed = 0

    for i, station_name in enumerate(test_stations, 1):
        print(f"\n[{i}/{len(test_stations)}] Testing: {station_name}")
        print("-" * 60)

        try:
            response = requests.post(
                f"{BASE_URL}/api/tunein/play",
                json={
                    "station_name": station_name,
                    "music_server_instance": "Music_Server_A"
                },
                timeout=30
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"[OK] PASS - {result.get('message', 'Success')}")
                passed += 1
            else:
                error = response.json().get('detail', 'Unknown error')
                print(f"[X] FAIL - {error}")
                failed += 1

        except requests.exceptions.Timeout:
            print(f"[X] FAIL - Request timeout (30s)")
            failed += 1
        except Exception as e:
            print(f"[X] FAIL - Exception: {e}")
            failed += 1

        # Wait between stations
        if i < len(test_stations):
            print("\nWaiting 3 seconds before next test...")
            time.sleep(3)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(test_stations)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_stations)*100):.1f}%")

    if failed == 0:
        print("\n[SUCCESS] All TuneIn play tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(test_tunein_play())
