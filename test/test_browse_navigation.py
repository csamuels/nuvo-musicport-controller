"""Test correct browse commands for menu navigation."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_browse_navigation():
    """Test browsing menus vs browsing Pandora stations."""

    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        # Test different browse commands
        browse_commands = [
            ("BrowseServices", "Browse available services"),
            ("BrowseMain", "Browse main menu"),
            ("GetServices", "Get services list"),
            ("BrowsePickList", "Browse current pick list"),
            ("BrowsePickListStart 0 100", "Browse pick list with pagination"),
        ]

        for cmd, desc in browse_commands:
            print("=" * 60)
            print(f"{desc}: {cmd}")
            print("=" * 60)

            try:
                response = await client._execute_command(cmd, retry_on_error=False)
                if response and "Error" not in response[0]:
                    xml = '\n'.join(response)
                    print(f"[OK] Got response ({len(response)} lines)")
                    print(f"First 200 chars: {xml[:200]}")

                    # Check what kind of items we got
                    if '<Service' in xml:
                        print("  Contains: Service items")
                    elif '<PickListItem' in xml:
                        print("  Contains: PickListItem items")
                    elif '<RadioStation' in xml:
                        print("  Contains: RadioStation items")
                    else:
                        print(f"  Contains: {xml[:100]}")
                else:
                    print(f"[FAIL] {response[0] if response else 'No response'}")
            except Exception as e:
                print(f"[FAIL] {e}")

            print()

        await client.disconnect()

    except Exception as e:
        print(f"\n!!! ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client._connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_browse_navigation())
