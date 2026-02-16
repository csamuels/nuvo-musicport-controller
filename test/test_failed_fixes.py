"""Test script to verify all fixes for the 6 failed tests."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_validation_endpoint():
    """Test: /api/tunein/validate-stations (was 404)"""
    print("\n[TEST 1] Validation Endpoint")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/tunein/validate-stations?instance=Music_Server_A")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        valid_count = sum(1 for s in data if s['appears_valid'])
        invalid_count = len(data) - valid_count

        print(f"[OK] PASS - Endpoint working")
        print(f"   Stations validated: {len(data)}")
        print(f"   Valid: {valid_count}")
        print(f"   Invalid: {invalid_count}")

        # Check Hot 97
        hot_97 = next((s for s in data if "Hot 97" in s['title']), None)
        if hot_97:
            print(f"   Hot 97: {'VALID' if hot_97['appears_valid'] else 'INVALID'}")

        return True
    else:
        print(f"[X] FAIL - Expected 200, got {response.status_code}")
        return False


def test_working_stations_endpoint():
    """Test: /api/tunein/working-stations (was 404)"""
    print("\n[TEST 2] Working Stations Endpoint")
    print("=" * 60)

    response = requests.get(f"{BASE_URL}/api/tunein/working-stations?instance=Music_Server_A")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"[OK] PASS - Endpoint working")
        print(f"   Working stations: {len(data)}")
        return True
    else:
        print(f"[X] FAIL - Expected 200, got {response.status_code}")
        return False


def test_volume_validation():
    """Test: Volume validation returns 422 (was 400)"""
    print("\n[TEST 3] Volume Validation Error Code")
    print("=" * 60)

    response = requests.post(
        f"{BASE_URL}/api/zones/1/volume",
        json={"volume": 100}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 422:
        print(f"[OK] PASS - Correct 422 status code")
        return True
    else:
        print(f"[X] FAIL - Expected 422, got {response.status_code}")
        return False


def test_tunein_play_with_retry():
    """Test: TuneIn play with retry logic (was 503)"""
    print("\n[TEST 4-6] TuneIn Play with Retry Logic")
    print("=" * 60)

    # Test 3 stations that previously failed
    test_stations = [
        "89.1 - WFDU (Eclectic Music)",
        "95.3 - WBAB (Classic Rock Music)",
        "97.1 - Hot 97 (Hip Hop Music)"
    ]

    passed = 0
    failed = 0

    for station_name in test_stations:
        print(f"\nTrying: {station_name}")

        response = requests.post(
            f"{BASE_URL}/api/tunein/play",
            json={
                "station_name": station_name,
                "music_server_instance": "Music_Server_A"
            }
        )

        print(f"  Status Code: {response.status_code}")

        if response.status_code == 200:
            print(f"  [OK] PASS")
            passed += 1
        else:
            print(f"  [X] FAIL - {response.json().get('detail', 'Unknown error')}")
            failed += 1

        time.sleep(2)  # Wait between stations

    print(f"\nTuneIn Play Tests: {passed} passed, {failed} failed")
    return failed == 0


def main():
    """Run all tests for the fixes."""
    print("\n" + "=" * 60)
    print("TESTING FIXES FOR 6 FAILED TESTS")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")

    results = []

    # Run all tests
    results.append(("Validation Endpoint", test_validation_endpoint()))
    results.append(("Working Stations Endpoint", test_working_stations_endpoint()))
    results.append(("Volume Validation", test_volume_validation()))
    results.append(("TuneIn Play (3 tests)", test_tunein_play_with_retry()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} test groups passed")

    if passed == total:
        print("\n[SUCCESS] ALL FIXES VERIFIED!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test group(s) still failing")
        return 1


if __name__ == "__main__":
    exit(main())
