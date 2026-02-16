"""Test different MCS command sequences to find the right way to browse."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_browse_sequences():
    """Try different command sequences to get browse working."""

    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        print("=" * 60)
        print("TEST 1: Basic sequence (current approach)")
        print("=" * 60)

        await client.connect()
        await client.set_instance('Music_Server_A')

        try:
            items = await client.browse_pick_list()
            print(f"[OK] SUCCESS: Got {len(items)} items")
            if items:
                print(f"  First item: {items[0].title}")
        except Exception as e:
            print(f"[FAIL] FAILED: {e}")

        await client.disconnect()
        await asyncio.sleep(2.0)

        # ===== TEST 2: Try browsing instances first =====
        print("\n" + "=" * 60)
        print("TEST 2: Browse instances first")
        print("=" * 60)

        await client.connect()

        # Try BrowseInstancesEX
        print("Sending BrowseInstancesEX...")
        response = await client._execute_command("BrowseInstancesEX")
        print(f"Response: {response[:3] if len(response) > 3 else response}")

        await client.set_instance('Music_Server_A')

        try:
            items = await client.browse_pick_list()
            print(f"[OK] SUCCESS: Got {len(items)} items")
            if items:
                print(f"  First item: {items[0].title}")
        except Exception as e:
            print(f"[FAIL] FAILED: {e}")

        await client.disconnect()
        await asyncio.sleep(2.0)

        # ===== TEST 3: Try BrowseMain first =====
        print("\n" + "=" * 60)
        print("TEST 3: Try BrowseMain")
        print("=" * 60)

        await client.connect()
        await client.set_instance('Music_Server_A')

        print("Sending BrowseMain...")
        response = await client._execute_command("BrowseMain")
        print(f"Response: {response[:5] if len(response) > 5 else response}")

        try:
            items = await client.browse_pick_list()
            print(f"[OK] SUCCESS: Got {len(items)} items")
            if items:
                print(f"  First item: {items[0].title}")
        except Exception as e:
            print(f"[FAIL] FAILED: {e}")

        await client.disconnect()
        await asyncio.sleep(2.0)

        # ===== TEST 4: Try SetRadioFilter first =====
        print("\n" + "=" * 60)
        print("TEST 4: SetRadioFilter then BrowsePickList")
        print("=" * 60)

        await client.connect()
        await client.set_instance('Music_Server_A')

        print("Sending SetRadioFilter (empty)...")
        await client.set_radio_filter("")

        try:
            items = await client.browse_pick_list()
            print(f"[OK] SUCCESS: Got {len(items)} items")
            if items:
                print(f"  First item: {items[0].title}")
        except Exception as e:
            print(f"[FAIL] FAILED: {e}")

        await client.disconnect()
        await asyncio.sleep(2.0)

        # ===== TEST 5: Try navigating to radio menu =====
        print("\n" + "=" * 60)
        print("TEST 5: Navigate to TuneIn Radio menu")
        print("=" * 60)

        await client.connect()
        await client.set_instance('Music_Server_A')

        # First browse main menu
        print("Browsing main menu...")
        response = await client._execute_command("BrowseMain")
        print(f"Main menu response lines: {len(response)}")

        # Parse to find TuneIn
        import re
        for i, line in enumerate(response):
            if 'TuneIn' in line or 'Radio' in line:
                match = re.search(r'<PickListItem[^>]*>', line)
                if match:
                    print(f"Found at line {i}: {line[:100]}")

                    # Try to extract index
                    # Items are usually indexed starting at 0
                    # Try acknowledging item 0 or 1
                    for test_idx in [0, 1, 2]:
                        print(f"\nTrying AckPickItem {test_idx}...")
                        try:
                            await client.ack_pick_item(test_idx)
                            await asyncio.sleep(1.0)

                            items = await client.browse_pick_list()
                            print(f"[OK] SUCCESS: Got {len(items)} items after ack {test_idx}")
                            if items:
                                print(f"  First 3 items: {[item.title for item in items[:3]]}")
                            break
                        except Exception as e:
                            print(f"[FAIL] Failed with ack {test_idx}: {e}")
                    break

        await client.disconnect()

    except Exception as e:
        print(f"\n!!! TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client._connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_browse_sequences())
