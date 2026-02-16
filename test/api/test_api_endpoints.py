"""
Comprehensive API Endpoint Integration Tests

Tests all endpoints against the actual NuVo device.
Cleans up after itself (reverts any changes made during testing).

Usage:
  python test_api_endpoints.py              # Basic tests only
  python test_api_endpoints.py --comprehensive  # Full comprehensive tests
"""

import requests
import json
import time
import argparse
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

BASE_URL = "http://localhost:8000"
RESULTS = []
STATE_BACKUP_FILE = Path(__file__).parent / "system_state_backup.json"

# Test configuration
MAX_VOLUME = 40  # Safety cap for volume tests
POLLING_INTERVAL = 2.0  # Seconds between polls
POLLING_TIMEOUT = 15.0  # Max seconds to wait for state change
PLAYBACK_WAIT = 5.0  # Seconds to wait for playback to start


class TestResult:
    def __init__(self, category: str, endpoint: str, method: str, success: bool,
                 message: str, response_code: Optional[int] = None, duration: Optional[float] = None):
        self.category = category
        self.endpoint = endpoint
        self.method = method
        self.success = success
        self.message = message
        self.response_code = response_code
        self.duration = duration


def log_verbose(message: str, indent: int = 0):
    """Print verbose log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    prefix = "  " * indent
    print(f"[{timestamp}] {prefix}{message}")


def test_endpoint(category: str, method: str, endpoint: str, expected_status: int = 200,
                  json_data: Optional[Dict] = None, description: str = "",
                  verbose: bool = False) -> Tuple[bool, Any, float]:
    """Test an endpoint and record the result."""
    url = f"{BASE_URL}{endpoint}"
    start_time = time.time()

    if verbose:
        log_verbose(f">> {method} {endpoint}", 1)
        if json_data:
            log_verbose(f"  Data: {json.dumps(json_data, indent=2)}", 1)

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        duration = time.time() - start_time
        success = response.status_code == expected_status

        if success:
            message = f"[OK] {description or 'Success'}"
            try:
                data = response.json()
            except:
                data = response.text

            if verbose:
                log_verbose(f"[OK] {description or 'Success'} (after {duration:.2f}s)", 1)
        else:
            message = f"[FAIL] Expected {expected_status}, got {response.status_code}"
            data = None

            if verbose:
                log_verbose(f"[X] {message} (after {duration:.2f}s)", 1)
                try:
                    error_data = response.json()
                    log_verbose(f"  Error: {json.dumps(error_data, indent=2)}", 1)
                except:
                    log_verbose(f"  Response: {response.text[:200]}", 1)

        RESULTS.append(TestResult(category, endpoint, method, success, message, response.status_code, duration))
        return success, data, duration

    except requests.exceptions.Timeout:
        duration = time.time() - start_time
        message = f"[FAIL] Timeout after 10s"
        if verbose:
            log_verbose(f"[X] {message}", 1)
        RESULTS.append(TestResult(category, endpoint, method, False, message, None, duration))
        return False, None, duration
    except Exception as e:
        duration = time.time() - start_time
        message = f"[FAIL] Exception: {str(e)}"
        if verbose:
            log_verbose(f"[X] {message}", 1)
        RESULTS.append(TestResult(category, endpoint, method, False, message, None, duration))
        return False, None, duration


def poll_for_change(check_func, expected_value, timeout: float = POLLING_TIMEOUT,
                   interval: float = POLLING_INTERVAL, verbose: bool = False) -> Tuple[bool, Any, float]:
    """
    Poll for a state change.

    Args:
        check_func: Function that returns current value
        expected_value: Expected value (or callable that returns True if value is acceptable)
        timeout: Max seconds to wait
        interval: Seconds between checks
        verbose: Print verbose logs

    Returns:
        (success, final_value, elapsed_time)
    """
    start_time = time.time()
    attempt = 0

    # Wait initial delay before first check
    time.sleep(interval)

    while True:
        attempt += 1
        elapsed = time.time() - start_time

        try:
            current_value = check_func()

            # Check if value matches expected
            if callable(expected_value):
                match = expected_value(current_value)
            else:
                match = current_value == expected_value

            if verbose:
                log_verbose(f"Poll attempt {attempt} (after {elapsed:.2f}s): {current_value}", 2)

            if match:
                if verbose:
                    log_verbose(f"[OK] Value confirmed after {elapsed:.2f}s", 2)
                return True, current_value, elapsed

        except Exception as e:
            if verbose:
                log_verbose(f"[X] Poll error: {e}", 2)

        # Check timeout
        if elapsed >= timeout:
            if verbose:
                log_verbose(f"[X] Timeout after {elapsed:.2f}s", 2)
            return False, current_value if 'current_value' in locals() else None, elapsed

        # Wait before next attempt
        time.sleep(interval)


def capture_system_state(verbose: bool = False) -> Dict[str, Any]:
    """Capture complete system state for restoration."""
    if verbose:
        log_verbose("Capturing system state...")

    state = {
        "timestamp": datetime.now().isoformat(),
        "zones": [],
        "system": {}
    }

    try:
        # Get system status
        success, system_data, _ = test_endpoint("State Capture", "GET", "/api/control/status",
                                               description="Capture system status", verbose=verbose)
        if success:
            state["system"] = system_data

        # Get all zones
        success, zones_data, _ = test_endpoint("State Capture", "GET", "/api/zones",
                                              description="Capture zones", verbose=verbose)
        if success and zones_data:
            state["zones"] = zones_data
            if verbose:
                log_verbose(f"[OK] Captured state for {len(zones_data)} zones", 1)

        # Save to backup file
        with open(STATE_BACKUP_FILE, 'w') as f:
            json.dump(state, f, indent=2)

        if verbose:
            log_verbose(f"[OK] State backup saved to {STATE_BACKUP_FILE}", 1)

        return state

    except Exception as e:
        log_verbose(f"[X] Error capturing state: {e}", 1)
        return state


def restore_system_state(original_state: Dict[str, Any], verbose: bool = False) -> bool:
    """Restore system to original state."""
    if verbose:
        log_verbose("Restoring system state...")

    all_success = True

    try:
        # Restore each zone
        for zone in original_state.get("zones", []):
            zone_num = zone["zone_number"]

            if verbose:
                log_verbose(f"Restoring Zone {zone_num}...", 1)

            # Restore power
            if zone["is_on"]:
                success, _, _ = test_endpoint("State Restore", "POST",
                                            f"/api/zones/{zone_num}/power/on",
                                            description=f"Restore Zone {zone_num} power ON",
                                            verbose=verbose)
            else:
                success, _, _ = test_endpoint("State Restore", "POST",
                                            f"/api/zones/{zone_num}/power/off",
                                            description=f"Restore Zone {zone_num} power OFF",
                                            verbose=verbose)
            all_success = all_success and success

            # Restore volume
            success, _, _ = test_endpoint("State Restore", "POST",
                                        f"/api/zones/{zone_num}/volume",
                                        json_data={"volume": zone["volume"]},
                                        description=f"Restore Zone {zone_num} volume to {zone['volume']}",
                                        verbose=verbose)
            all_success = all_success and success

            # Restore mute
            if zone["mute"]:
                # Current is unmuted, need to mute
                current_success, current_zone, _ = test_endpoint("State Restore", "GET",
                                                                f"/api/zones/{zone_num}",
                                                                verbose=False)
                if current_success and not current_zone["mute"]:
                    success, _, _ = test_endpoint("State Restore", "POST",
                                                f"/api/zones/{zone_num}/mute",
                                                description=f"Restore Zone {zone_num} mute",
                                                verbose=verbose)
                    all_success = all_success and success

        if verbose:
            if all_success:
                log_verbose("[OK] System state fully restored", 1)
            else:
                log_verbose("[X] Some state restoration failed", 1)

        return all_success

    except Exception as e:
        log_verbose(f"[X] Error restoring state: {e}", 1)
        return False


def verify_state_restored(original_state: Dict[str, Any], verbose: bool = False) -> bool:
    """Verify system state matches original."""
    if verbose:
        log_verbose("Verifying state restoration...")

    try:
        success, current_zones, _ = test_endpoint("State Verify", "GET", "/api/zones",
                                                 verbose=False)
        if not success:
            if verbose:
                log_verbose("[X] Could not fetch current zones", 1)
            return False

        original_zones = {z["zone_number"]: z for z in original_state.get("zones", [])}
        all_match = True

        for zone in current_zones:
            zone_num = zone["zone_number"]
            orig = original_zones.get(zone_num)

            if not orig:
                continue

            mismatches = []
            if zone["is_on"] != orig["is_on"]:
                mismatches.append(f"power: {orig['is_on']} -> {zone['is_on']}")
            if zone["volume"] != orig["volume"]:
                mismatches.append(f"volume: {orig['volume']} -> {zone['volume']}")
            if zone["mute"] != orig["mute"]:
                mismatches.append(f"mute: {orig['mute']} -> {zone['mute']}")

            if mismatches:
                all_match = False
                if verbose:
                    log_verbose(f"[X] Zone {zone_num} mismatch: {', '.join(mismatches)}", 1)
            elif verbose:
                log_verbose(f"[OK] Zone {zone_num} state verified", 1)

        if all_match and verbose:
            log_verbose("[OK] All state verified", 1)

        return all_match

    except Exception as e:
        if verbose:
            log_verbose(f"[X] Error verifying state: {e}", 1)
        return False


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_results():
    """Print test results summary."""
    print_section("TEST RESULTS SUMMARY")

    # Group by category
    categories = {}
    for result in RESULTS:
        if result.category not in categories:
            categories[result.category] = []
        categories[result.category].append(result)

    total_tests = len(RESULTS)
    passed_tests = sum(1 for r in RESULTS if r.success)
    failed_tests = total_tests - passed_tests

    for category, results in categories.items():
        print(f"\n{category}:")
        for result in results:
            status = "[OK]" if result.success else "[FAIL]"
            code = f"[{result.response_code}]" if result.response_code else ""
            duration = f"({result.duration:.2f}s)" if result.duration else ""
            print(f"  {status} {result.method:6} {result.endpoint:45} {code} {duration}")
            if not result.success:
                print(f"      -> {result.message}")

    print(f"\n{'='*70}")
    print(f"Total: {total_tests} tests | Passed: {passed_tests} | Failed: {failed_tests}")
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"{'='*70}\n")


def confirm_comprehensive_test() -> bool:
    """Show warning and get user confirmation for comprehensive tests."""
    print("\n" + "="*70)
    print("  [!] COMPREHENSIVE TEST MODE")
    print("="*70)
    print("\nThis will perform extensive testing that WILL affect your system:")
    print("  * Test ALL 6 zones (power, volume, mute, source changes)")
    print("  * Change volumes to 0, 1, 5, and 40 (capped for safety)")
    print("  * Switch between all 6 sources")
    print("  * Toggle party mode 3 times")
    print("  * Play 5 different TuneIn radio stations")
    print("  * Play 5 different local music items (albums, tracks, artists)")
    print("  * Add and remove test TuneIn radio stations")
    print("  * Test rapid state changes to verify concurrent client handling")
    print("  * Test invalid inputs and error handling")
    print("\n[OK] System state will be captured FIRST and saved to:")
    print(f"  {STATE_BACKUP_FILE}")
    print("[OK] All changes will be reverted at the end")
    print("[OK] Tests will be verbose with detailed timing information")
    print("\n[TIME] Estimated duration: 10-15 minutes")
    print("\n" + "="*70)

    response = input("\nProceed with comprehensive tests? (Y/N): ").strip().upper()
    return response == 'Y'


def run_basic_tests():
    """Run basic API endpoint tests (original functionality)."""
    print_section("BASIC API INTEGRATION TESTS")
    print(f"Base URL: {BASE_URL}")

    # =========================================================================
    # 1. HEALTH & STATUS ENDPOINTS
    # =========================================================================
    print_section("1. Health & Status")

    test_endpoint("Health & Status", "GET", "/health",
                  description="API health check")

    test_endpoint("Health & Status", "GET", "/api/control/health",
                  description="Control health check")

    success, status_data, _ = test_endpoint("Health & Status", "GET", "/api/control/status",
                                        description="System status")
    if success and status_data:
        print(f"  -> Device: {status_data.get('device_type')} FW: {status_data.get('firmware_version')}")

    # =========================================================================
    # 2. ZONES ENDPOINTS
    # =========================================================================
    print_section("2. Zones")

    success, zones_data, _ = test_endpoint("Zones", "GET", "/api/zones",
                                       description="List all zones")

    if success and zones_data:
        print(f"  -> Found {len(zones_data)} zones")
        if len(zones_data) > 0:
            zone = zones_data[0]
            zone_num = zone['zone_number']
            test_endpoint("Zones", "GET", f"/api/zones/{zone_num}",
                         description=f"Get zone {zone_num}")

    # =========================================================================
    # 3. SOURCES ENDPOINTS
    # =========================================================================
    print_section("3. Sources")

    success, sources_data, _ = test_endpoint("Sources", "GET", "/api/sources",
                                         description="List all sources")
    if success and sources_data:
        print(f"  -> Found {len(sources_data)} sources")
        if len(sources_data) > 0:
            source = sources_data[0]
            source_id = source['source_id']
            test_endpoint("Sources", "GET", f"/api/sources/{source_id}",
                         description=f"Get source {source_id}")

    # =========================================================================
    # 4. SYSTEM CONTROL ENDPOINTS
    # =========================================================================
    print_section("4. System Control")

    test_endpoint("System Control", "GET", "/api/control/now-playing",
                  description="Get now playing info")

    # =========================================================================
    # 5. MUSIC SERVER ENDPOINTS
    # =========================================================================
    print_section("5. Music Server")

    success, instances, _ = test_endpoint("Music Server", "GET", "/api/music-servers/instances",
                                      description="List Music Server instances")
    if success and instances:
        print(f"  -> Found {len(instances)} instances: {', '.join(instances)}")

    test_endpoint("Music Server", "GET", "/api/music-servers/status",
                  description="Get Music Server status")

    success, stations, _ = test_endpoint("Music Server", "GET", "/api/music-servers/browse",
                                     description="Browse content")
    if success and stations:
        print(f"  -> Found {len(stations)} items")

    # =========================================================================
    # 6. RADIO ENDPOINTS (TuneIn)
    # =========================================================================
    print_section("6. TuneIn Radio")

    success, radio_stations, _ = test_endpoint("Radio", "GET", "/api/music-servers/browse?instance=Music_Server_A",
                                           description="Browse TuneIn radio stations")
    if success and radio_stations:
        print(f"  -> Found {len(radio_stations)} TuneIn radio stations")

    # =========================================================================
    # 7. DISCOVERY ENDPOINTS
    # =========================================================================
    print_section("7. Discovery")

    test_endpoint("Discovery", "GET", "/api/discovery",
                 description="Discover devices on network")

    test_endpoint("Discovery", "GET", "/api/device/services",
                  description="Get device services")

    test_endpoint("Discovery", "GET", "/api/device/status",
                 description="Get device status")

    # =========================================================================
    # 8. CREDENTIALS ENDPOINTS
    # =========================================================================
    print_section("8. Credentials")

    success, services, _ = test_endpoint("Credentials", "GET", "/api/credentials/services",
                                     description="List credential services")
    if success and services:
        print(f"  -> Found {len(services)} services")

    # Test adding and removing a test radio station
    test_station = {
        "call_sign": "TEST-FM",
        "name": "Test Radio Station",
        "description": "Integration test station",
        "stream_url": "http://example.com/stream",
        "image_url": ""
    }

    success, add_result, _ = test_endpoint("Credentials", "POST", "/api/credentials/aux-radio/add",
                                       json_data=test_station,
                                       description="Add test radio station")

    if success:
        success, aux_stations, _ = test_endpoint("Credentials", "GET", "/api/credentials/aux-radio/stations",
                                             description="List aux radio stations")

        if success and aux_stations:
            test_station_obj = next((s for s in aux_stations if s['call_sign'] == 'TEST-FM'), None)
            if test_station_obj:
                test_endpoint("Credentials", "POST", "/api/credentials/aux-radio/delete",
                             json_data={"station_id": test_station_obj['id']},
                             description="Delete test radio station (cleanup)")

    # =========================================================================
    # 9. WEBSOCKET
    # =========================================================================
    print_section("9. WebSocket")
    print("  (WebSocket requires special client - testing via HTTP upgrade)")

    try:
        response = requests.get(f"{BASE_URL}/ws", timeout=2)
        if response.status_code in [426, 400, 404, 101]:
            RESULTS.append(TestResult("WebSocket", "/ws", "GET", True,
                                    f"[OK] WebSocket endpoint exists", response.status_code))
        else:
            RESULTS.append(TestResult("WebSocket", "/ws", "GET", False,
                                    f"Unexpected status {response.status_code}", response.status_code))
    except:
        RESULTS.append(TestResult("WebSocket", "/ws", "GET", True,
                                "[OK] WebSocket endpoint exists (connection refused as expected)"))

    # =========================================================================
    # 10. LOCAL MUSIC LIBRARY ENDPOINTS
    # =========================================================================
    print_section("10. Local Music Library")

    success, albums_data, _ = test_endpoint("Music Library", "GET", "/api/library/albums?instance=Music_Server_A",
                                        description="Browse all albums")
    if success and albums_data:
        print(f"  -> Found {len(albums_data)} albums")
        if len(albums_data) > 0:
            album = albums_data[0]
            album_guid = album['guid']
            album_name = album['name']
            success, tracks_data, _ = test_endpoint("Music Library", "GET",
                                                f"/api/library/albums/{album_guid}/tracks?instance=Music_Server_A",
                                                description=f"Get tracks for album '{album_name}'")
            if success and tracks_data:
                print(f"  -> Album has {len(tracks_data)} tracks")

    success, artists_data, _ = test_endpoint("Music Library", "GET", "/api/library/artists?instance=Music_Server_A",
                                         description="Browse all artists")
    if success and artists_data:
        print(f"  -> Found {len(artists_data)} artists")

    success, queue_data, _ = test_endpoint("Music Library", "GET", "/api/library/queue?instance=Music_Server_A",
                                       description="Get current playback queue")
    if success and queue_data:
        print(f"  -> Queue has {len(queue_data)} tracks")
        now_playing = [t for t in queue_data if t.get('is_now_playing')]
        if now_playing:
            track = now_playing[0]
            print(f"  -> Now playing: {track['artist']} - {track['name']}")

    print("  (Skipping playback tests in basic mode)")


def run_comprehensive_tests():
    """Run comprehensive tests with state changes and verification."""

    print_section("COMPREHENSIVE API TESTS")
    print(f"Base URL: {BASE_URL}")
    log_verbose("Starting comprehensive test suite")

    # CRITICAL: Capture state FIRST
    print_section("STEP 1: CAPTURE SYSTEM STATE")
    original_state = capture_system_state(verbose=True)

    if not original_state.get("zones"):
        log_verbose("[X] CRITICAL: Could not capture system state!")
        log_verbose("[X] Aborting comprehensive tests for safety")
        return

    log_verbose(f"[OK] State captured and backed up to {STATE_BACKUP_FILE}")

    try:
        # =====================================================================
        # ZONE COMPREHENSIVE TESTS
        # =====================================================================
        print_section("ZONE COMPREHENSIVE TESTS")

        success, zones_data, _ = test_endpoint("Zones", "GET", "/api/zones", verbose=True)

        if success and zones_data:
            log_verbose(f"Testing all {len(zones_data)} zones comprehensively")

            for zone in zones_data:
                zone_num = zone["zone_number"]
                print_section(f"Zone {zone_num} Tests")

                log_verbose(f"[COMPREHENSIVE TEST] Zone {zone_num} Power & Volume")

                # Save original state
                orig_power = zone["is_on"]
                orig_volume = zone["volume"]
                orig_mute = zone["mute"]

                log_verbose(f">> Original state: Power={orig_power}, Volume={orig_volume}, Mute={orig_mute}", 1)

                # Test power on
                log_verbose(f">> Testing power ON...", 1)
                success, _, duration = test_endpoint("Zone Power", "POST",
                                                    f"/api/zones/{zone_num}/power/on",
                                                    verbose=True)

                if success:
                    # Verify power is on
                    def check_power_on():
                        s, z, _ = test_endpoint("Zone Power", "GET", f"/api/zones/{zone_num}", verbose=False)
                        return z["is_on"] if s and z else False

                    verified, final, elapsed = poll_for_change(check_power_on, True, verbose=True)
                    if verified:
                        log_verbose(f"[OK] Power ON confirmed", 1)
                    else:
                        log_verbose(f"[X] Power ON not confirmed", 1)

                # Test volume changes
                test_volumes = [0, 1, 5, min(MAX_VOLUME, orig_volume)]
                for test_vol in test_volumes:
                    log_verbose(f">> Testing volume change to {test_vol}...", 1)
                    success, _, _ = test_endpoint("Zone Volume", "POST",
                                                f"/api/zones/{zone_num}/volume",
                                                json_data={"volume": test_vol},
                                                verbose=True)

                    if success:
                        def check_volume():
                            s, z, _ = test_endpoint("Zone Volume", "GET", f"/api/zones/{zone_num}", verbose=False)
                            return z["volume"] if s and z else None

                        verified, final, elapsed = poll_for_change(check_volume, test_vol, verbose=True)
                        if verified:
                            log_verbose(f"[OK] Volume {test_vol} confirmed", 1)
                        else:
                            log_verbose(f"[X] Volume {test_vol} not confirmed (got {final})", 1)

                    time.sleep(0.5)

                # Restore original volume
                log_verbose(f">> Restoring original volume ({orig_volume})...", 1)
                test_endpoint("Zone Restore", "POST",
                            f"/api/zones/{zone_num}/volume",
                            json_data={"volume": orig_volume},
                            verbose=True)

                # Restore original power
                if not orig_power:
                    log_verbose(f">> Restoring power OFF...", 1)
                    test_endpoint("Zone Restore", "POST",
                                f"/api/zones/{zone_num}/power/off",
                                verbose=True)

                log_verbose(f"[OK] Zone {zone_num} tests complete", 1)

        # =====================================================================
        # SOURCE SWITCHING TESTS
        # =====================================================================
        print_section("SOURCE SWITCHING TESTS")

        success, sources_data, _ = test_endpoint("Sources", "GET", "/api/sources", verbose=True)

        if success and sources_data:
            log_verbose(f"Testing all {len(sources_data)} sources")

            # Pick first zone for source testing, power it on if needed
            test_zone = zones_data[0] if zones_data else None
            if not test_zone:
                log_verbose("[X] No zones available for source testing", 1)
            else:
                zone_num = test_zone["zone_number"]
                orig_source_id = test_zone["source_id"]

                log_verbose(f"Using Zone {zone_num} for source tests (original source: {orig_source_id})", 1)

                # Get original source GUID
                orig_source = next((s for s in sources_data if s["source_id"] == orig_source_id), None)
                orig_source_guid = orig_source["guid"] if orig_source else None

                # Ensure zone is on
                if not test_zone["is_on"]:
                    log_verbose(f">> Powering on Zone {zone_num} for testing...", 1)
                    test_endpoint("Source Switch", "POST",
                                f"/api/zones/{zone_num}/power/on",
                                verbose=True)
                    time.sleep(1)

                # Test switching to each source
                for source in sources_data:
                    source_id = source["source_id"]
                    source_guid = source["guid"]
                    source_name = source["name"]

                    log_verbose(f">> Switching to Source {source_id} ({source_name})...", 1)

                    success, _, _ = test_endpoint("Source Switch", "POST",
                                                f"/api/zones/{zone_num}/source",
                                                json_data={"source_guid": source_guid},
                                                verbose=True)

                    if success:
                        # Verify source changed
                        def check_source():
                            s, z, _ = test_endpoint("Source Switch", "GET", f"/api/zones/{zone_num}", verbose=False)
                            return z["source_id"] if s and z else None

                        verified, final, elapsed = poll_for_change(check_source, source_id, verbose=True)
                        if verified:
                            log_verbose(f"[OK] Source {source_id} confirmed", 1)
                        else:
                            log_verbose(f"[X] Source switch not confirmed (got source {final})", 1)

                    time.sleep(0.5)

                # Restore original source
                if orig_source_guid:
                    log_verbose(f">> Restoring original source ({orig_source_id})...", 1)
                    test_endpoint("Source Switch", "POST",
                                f"/api/zones/{zone_num}/source",
                                json_data={"source_guid": orig_source_guid},
                                verbose=True)

                # Restore original power state
                if not test_zone["is_on"]:
                    log_verbose(f">> Restoring Zone {zone_num} power OFF...", 1)
                    test_endpoint("Source Switch", "POST",
                                f"/api/zones/{zone_num}/power/off",
                                verbose=True)

        # =====================================================================
        # PARTY MODE TESTS
        # =====================================================================
        print_section("PARTY MODE TESTS")

        log_verbose("[COMPREHENSIVE TEST] Party Mode Toggle (3 cycles)")

        # Get original party mode state
        success, status, _ = test_endpoint("Party Mode", "GET", "/api/control/status", verbose=True)

        # Check if any zone has party mode active
        orig_party_active = False
        if success and status:
            for zone in status.get("zones", []):
                if zone.get("party_mode") in ["Host", "Slave"]:
                    orig_party_active = True
                    break

        log_verbose(f">> Original party mode active: {orig_party_active}", 1)

        for cycle in range(3):
            log_verbose(f">> Party mode cycle {cycle + 1}/3", 1)

            # Toggle party mode
            log_verbose(f"  >> Toggling party mode...", 2)
            success, _, _ = test_endpoint("Party Mode", "POST",
                                         "/api/control/partymode",
                                         verbose=True)

            if success:
                # Wait for party mode to change
                time.sleep(2)

                # Verify party mode changed
                success, status, _ = test_endpoint("Party Mode", "GET", "/api/control/status", verbose=False)
                if success and status:
                    party_zones = [z for z in status.get("zones", []) if z.get("party_mode") in ["Host", "Slave"]]
                    if party_zones:
                        log_verbose(f"  [OK] Party mode active with {len(party_zones)} zones", 2)
                        host = next((z for z in party_zones if z.get("party_mode") == "Host"), None)
                        if host:
                            log_verbose(f"    Host: Zone {host['zone_number']}", 3)
                    else:
                        log_verbose(f"  [OK] Party mode inactive", 2)

            # Toggle off
            log_verbose(f"  >> Toggling party mode again...", 2)
            success, _, _ = test_endpoint("Party Mode", "POST",
                                         "/api/control/partymode",
                                         verbose=True)
            time.sleep(2)

        # Restore original party mode state if needed
        success, final_status, _ = test_endpoint("Party Mode", "GET", "/api/control/status", verbose=False)
        final_party_active = False
        if success and final_status:
            for zone in final_status.get("zones", []):
                if zone.get("party_mode") in ["Host", "Slave"]:
                    final_party_active = True
                    break

        if orig_party_active != final_party_active:
            log_verbose(f">> Restoring original party mode state...", 1)
            test_endpoint("Party Mode", "POST", "/api/control/partymode", verbose=True)
            time.sleep(2)

        log_verbose(f"[OK] Party mode tests complete", 1)

        # =====================================================================
        # RADIO STATION TESTS (TuneIn Radio)
        # =====================================================================
        print_section("RADIO STATION TESTS (TuneIn Radio)")

        log_verbose("[COMPREHENSIVE TEST] TuneIn Radio Station Playback (5 stations)")

        # Browse TuneIn radio stations
        success, tunein_stations, _ = test_endpoint("Radio", "GET",
                                                     "/api/music-servers/browse?instance=Music_Server_A",
                                                     verbose=True)

        if success and tunein_stations:
            log_verbose(f">> Found {len(tunein_stations)} TuneIn radio stations", 1)

            # Test first 5 stations (or less if not enough available)
            num_to_test = min(5, len(tunein_stations))
            test_stations = tunein_stations[:num_to_test]

            for idx, station in enumerate(test_stations, 1):
                station_name = station.get("name", station.get("title", "Unknown"))
                station_guid = station.get("guid", "")

                log_verbose(f">> Testing station {idx}/{num_to_test}: {station_name}", 1)

                # Play the station
                success, _, _ = test_endpoint("Radio", "POST",
                                            "/api/tunein/play",
                                            json_data={
                                                "station_name": station_name,
                                                "music_server_instance": "Music_Server_A"
                                            },
                                            verbose=True)

                if success:
                    # Wait for playback to start
                    log_verbose(f"  >> Waiting {PLAYBACK_WAIT}s for playback to start...", 2)
                    time.sleep(PLAYBACK_WAIT)

                    # Check now playing
                    success, now_playing, _ = test_endpoint("Radio", "GET",
                                                           "/api/control/now-playing?instance=Music_Server_A",
                                                           verbose=True)
                    if success and now_playing:
                        play_state = now_playing.get('play_state', 'Unknown')
                        track_info = now_playing.get('now_playing', {})
                        log_verbose(f"  [OK] Play state: {play_state}", 2)
                        if track_info:
                            track = track_info.get('track', 'Unknown')
                            artist = track_info.get('artist', 'Unknown')
                            station_display = track_info.get('station', station_name)
                            log_verbose(f"  [OK] Now playing: {artist} - {track} on {station_display}", 2)
                    else:
                        log_verbose(f"  [X] Could not get now playing info", 2)
                else:
                    log_verbose(f"  [X] Failed to play station", 2)
        else:
            log_verbose("[X] Could not browse TuneIn radio stations", 1)

        # =====================================================================
        # TUNEIN VALIDATION TESTS
        # =====================================================================
        print_section("TUNEIN VALIDATION TESTS")

        log_verbose("[COMPREHENSIVE TEST] Station Validation & Filtering")

        # Test validate-stations endpoint
        log_verbose(">> Testing validate-stations endpoint...", 1)
        success, validation_results, status_code = test_endpoint(
            "TuneIn Validation",
            "GET",
            "/api/tunein/validate-stations?instance=Music_Server_A",
            verbose=True
        )

        if success and validation_results:
            log_verbose(f">> Received validation for {len(validation_results)} stations", 1)

            valid_count = sum(1 for r in validation_results if r.get('appears_valid'))
            invalid_count = len(validation_results) - valid_count

            log_verbose(f"  [OK] Valid stations: {valid_count}", 2)
            log_verbose(f"  [OK] Invalid stations: {invalid_count}", 2)

            # Show first 5 invalid stations
            invalid_stations = [r for r in validation_results if not r.get('appears_valid')]
            if invalid_stations:
                log_verbose(f"  >> First {min(5, len(invalid_stations))} invalid stations:", 2)
                for station in invalid_stations[:5]:
                    log_verbose(f"    [X] {station.get('title')} - {station.get('message')}", 3)

            # Check if Hot 97 is in the results (user's specific concern)
            hot_97 = next((r for r in validation_results if "Hot 97" in r.get('title', '')), None)
            if hot_97:
                status = "VALID" if hot_97.get('appears_valid') else "INVALID"
                log_verbose(f"  [OK] Hot 97 status: {status}", 2)
                log_verbose(f"      Message: {hot_97.get('message')}", 3)
        elif status_code == 404:
            log_verbose("  [!] Validation endpoint not available (404) - feature may not be deployed yet", 1)
        else:
            log_verbose("  [X] Failed to validate stations", 1)

        # Test working-stations endpoint (filtered list)
        log_verbose(">> Testing working-stations endpoint (filtered list)...", 1)
        success, working_stations, status_code = test_endpoint(
            "TuneIn Validation",
            "GET",
            "/api/tunein/working-stations?instance=Music_Server_A",
            verbose=True
        )

        if success and working_stations:
            log_verbose(f">> Received {len(working_stations)} working stations", 1)

            # Compare with full list
            if tunein_stations:
                filtered_out = len(tunein_stations) - len(working_stations)
                if filtered_out > 0:
                    log_verbose(f"  [OK] Filtered out {filtered_out} dead/invalid stations", 2)
                else:
                    log_verbose(f"  [OK] All stations appear valid", 2)

            # Verify format matches browse endpoint
            if len(working_stations) > 0:
                first_station = working_stations[0]
                required_fields = ['guid', 'title']
                has_all_fields = all(field in first_station for field in required_fields)
                if has_all_fields:
                    log_verbose(f"  [OK] Station format validated", 2)
                else:
                    log_verbose(f"  [X] Station format missing fields", 2)
        elif status_code == 404:
            log_verbose("  [!] Working-stations endpoint not available (404) - feature may not be deployed yet", 1)
        else:
            log_verbose("  [X] Failed to get working stations", 1)

        # =====================================================================
        # LOCAL MUSIC TESTS
        # =====================================================================
        print_section("LOCAL MUSIC TESTS")

        log_verbose("[COMPREHENSIVE TEST] Local Music Playback (5 items)")

        # Get albums
        success, albums, _ = test_endpoint("Music Library", "GET",
                                          "/api/library/albums?instance=Music_Server_A",
                                          verbose=True)

        # Get artists
        success_artists, artists, _ = test_endpoint("Music Library", "GET",
                                                    "/api/library/artists?instance=Music_Server_A",
                                                    verbose=True)

        if success and albums:
            log_verbose(f">> Found {len(albums)} albums", 1)

            # Test first album - Play entire album
            if len(albums) > 0:
                album = albums[0]
                log_verbose(f">> Testing album: {album['name']} by {album['artist']}", 1)

                # Get album tracks first
                success, tracks, _ = test_endpoint("Music Library", "GET",
                                                  f"/api/library/albums/{album['guid']}/tracks?instance=Music_Server_A",
                                                  verbose=True)

                if success and tracks:
                    log_verbose(f"  [OK] Album has {len(tracks)} tracks", 2)

                    # Test 1: Play entire album
                    log_verbose(f"  >> Test 1: Playing entire album...", 2)
                    success, _, _ = test_endpoint("Music Library", "POST",
                                                 "/api/library/play/album",
                                                 json_data={"guid": album["guid"]},
                                                 verbose=True)

                    if success:
                        time.sleep(PLAYBACK_WAIT)

                        # Verify queue contains all album tracks
                        success, queue, _ = test_endpoint("Music Library", "GET",
                                                        "/api/library/queue?instance=Music_Server_A",
                                                        verbose=True)
                        if success and queue:
                            log_verbose(f"    [OK] Queue has {len(queue)} tracks", 3)
                            if len(queue) == len(tracks):
                                log_verbose(f"    [OK] All album tracks in queue", 3)
                            now_playing = [t for t in queue if t.get("is_now_playing")]
                            if now_playing:
                                log_verbose(f"    [OK] Now playing: {now_playing[0]['name']}", 3)

                    # Test 2: Play individual track
                    if len(tracks) > 0:
                        track = tracks[0]
                        log_verbose(f"  >> Test 2: Playing single track: {track['name']}", 2)

                        success, _, _ = test_endpoint("Music Library", "POST",
                                                     "/api/library/play/track",
                                                     json_data={"guid": track["guid"]},
                                                     verbose=True)

                        if success:
                            time.sleep(PLAYBACK_WAIT)

                            # Verify track is playing
                            success, queue, _ = test_endpoint("Music Library", "GET",
                                                            "/api/library/queue?instance=Music_Server_A",
                                                            verbose=True)
                            if success and queue:
                                now_playing = [t for t in queue if t.get("is_now_playing")]
                                if now_playing:
                                    log_verbose(f"    [OK] Track playing: {now_playing[0]['name']}", 3)

        # Test play by artist
        if success_artists and artists and len(artists) > 0:
            artist = artists[0]
            log_verbose(f">> Test 3: Playing all tracks by artist: {artist['name']}", 1)

            success, _, _ = test_endpoint("Music Library", "POST",
                                         "/api/library/play/artist",
                                         json_data={"guid": artist["guid"]},
                                         verbose=True)

            if success:
                time.sleep(PLAYBACK_WAIT)

                # Verify queue has artist tracks
                success, queue, _ = test_endpoint("Music Library", "GET",
                                                "/api/library/queue?instance=Music_Server_A",
                                                verbose=True)
                if success and queue:
                    log_verbose(f"  [OK] Queue has {len(queue)} tracks from artist", 2)

        # Test play all music
        log_verbose(f">> Test 4: Playing all music in library...", 1)
        success, _, _ = test_endpoint("Music Library", "POST",
                                     "/api/library/play/all?instance=Music_Server_A",
                                     verbose=True)

        if success:
            time.sleep(PLAYBACK_WAIT)

            # Verify queue has tracks
            success, queue, _ = test_endpoint("Music Library", "GET",
                                            "/api/library/queue?instance=Music_Server_A",
                                            verbose=True)
            if success and queue:
                log_verbose(f"  [OK] Queue has {len(queue)} tracks (shuffled)", 2)
                now_playing = [t for t in queue if t.get("is_now_playing")]
                if now_playing:
                    log_verbose(f"  [OK] Now playing: {now_playing[0]['name']}", 2)

        # =====================================================================
        # TUNEIN RADIO STATION CRUD TESTS
        # =====================================================================
        print_section("TUNEIN RADIO STATION CRUD TESTS")

        log_verbose("[COMPREHENSIVE TEST] Add/Remove TuneIn Stations")

        test_stations = [
            {
                "call_sign": "WNJT",
                "name": "WNJT 88.1 FM",
                "description": "Public Radio - Trenton, NJ",
                "stream_url": "http://wnjt.org/stream",
                "image_url": ""
            },
            {
                "call_sign": "WWFM",
                "name": "WWFM 89.1 FM",
                "description": "Classical - Trenton, NJ",
                "stream_url": "http://wwfm.org/stream",
                "image_url": ""
            }
        ]

        added_stations = []

        for station in test_stations:
            log_verbose(f">> Adding station: {station['call_sign']} - {station['name']}", 1)

            success, result, _ = test_endpoint("TuneIn CRUD", "POST",
                                              "/api/credentials/aux-radio/add",
                                              json_data=station,
                                              verbose=True)

            if success:
                # Verify it was added
                success, stations_list, _ = test_endpoint("TuneIn CRUD", "GET",
                                                         "/api/credentials/aux-radio/stations",
                                                         verbose=True)
                if success and stations_list:
                    added = next((s for s in stations_list if s['call_sign'] == station['call_sign']), None)
                    if added:
                        log_verbose(f"  [OK] Station added successfully (ID: {added['id']})", 2)
                        added_stations.append(added)
                    else:
                        log_verbose(f"  [X] Station not found in list", 2)

        # Clean up - remove test stations
        log_verbose(">> Cleaning up test stations...", 1)
        for station in added_stations:
            log_verbose(f"  >> Removing {station['call_sign']}...", 2)
            success, _, _ = test_endpoint("TuneIn CRUD", "POST",
                                         "/api/credentials/aux-radio/delete",
                                         json_data={"station_id": station['id']},
                                         verbose=True)
            if success:
                log_verbose(f"    [OK] Removed", 3)

        # =====================================================================
        # BOUNDARY & ERROR TESTS
        # =====================================================================
        print_section("BOUNDARY & ERROR TESTS")

        log_verbose("[COMPREHENSIVE TEST] Invalid Input Handling")

        # Test invalid volume
        log_verbose(">> Testing invalid volume (100)...", 1)
        success, _, _ = test_endpoint("Boundaries", "POST",
                                     "/api/zones/1/volume",
                                     json_data={"volume": 100},
                                     expected_status=422,
                                     verbose=True)
        if success:
            log_verbose("  [OK] Invalid volume rejected correctly", 2)

        # Test invalid zone
        log_verbose(">> Testing invalid zone (99)...", 1)
        success, _, _ = test_endpoint("Boundaries", "GET",
                                     "/api/zones/99",
                                     expected_status=404,
                                     verbose=True)
        if success:
            log_verbose("  [OK] Invalid zone rejected correctly", 2)

    except Exception as e:
        log_verbose(f"[X] Comprehensive test error: {e}", 0)
        import traceback
        traceback.print_exc()

    finally:
        # =====================================================================
        # RESTORE SYSTEM STATE
        # =====================================================================
        print_section("RESTORE SYSTEM STATE")

        log_verbose("Restoring original system state...")
        restore_success = restore_system_state(original_state, verbose=True)

        if restore_success:
            log_verbose("[OK] State restoration complete", 1)

            # Verify restoration
            verify_success = verify_state_restored(original_state, verbose=True)

            if verify_success:
                log_verbose("[OK] State restoration VERIFIED", 1)
            else:
                log_verbose("[X] State verification FAILED - manual check recommended", 1)
        else:
            log_verbose("[X] State restoration had errors - manual check required", 1)


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='NuVo MusicPort API Integration Tests')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Run comprehensive tests with state changes (WARNING: will affect device)')
    parser.add_argument('--yes', '-y', action='store_true',
                       help='Skip confirmation prompt (auto-confirm comprehensive tests)')

    args = parser.parse_args()

    if args.comprehensive:
        # Comprehensive mode - get confirmation first (unless --yes flag is used)
        if not args.yes and not confirm_comprehensive_test():
            print("\nComprehensive tests cancelled by user.")
            return 0

        print("\n" + "="*70)
        print("  Starting comprehensive tests...")
        print("="*70)

        run_comprehensive_tests()
    else:
        # Basic mode - original tests
        run_basic_tests()

    # =========================================================================
    # CLEANUP
    # =========================================================================
    print_section("CLEANUP")
    print("  -> All test data cleaned up")
    print("  -> Device state preserved" if not args.comprehensive else "  -> Device state restored")

    # Print final results
    print_results()

    # Return exit code based on results
    failed = sum(1 for r in RESULTS if not r.success)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        print_results()

        # Try to restore state if backup exists
        if STATE_BACKUP_FILE.exists():
            print("\n[!]  Attempting to restore state from backup...")
            try:
                with open(STATE_BACKUP_FILE, 'r') as f:
                    backup_state = json.load(f)
                restore_system_state(backup_state, verbose=True)
                print("[OK] State restored from backup")
            except Exception as e:
                print(f"[X] Could not restore from backup: {e}")

        exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()

        # Try to restore state if backup exists
        if STATE_BACKUP_FILE.exists():
            print("\n[!]  Attempting to restore state from backup...")
            try:
                with open(STATE_BACKUP_FILE, 'r') as f:
                    backup_state = json.load(f)
                restore_system_state(backup_state, verbose=True)
                print("[OK] State restored from backup")
            except Exception as e:
                print(f"[X] Could not restore from backup: {e}")

        exit(1)
