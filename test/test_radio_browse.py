"""Test radio-specific browse commands."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_radio_browse():
    """Try different radio browse commands."""

    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        # Test radio browse commands
        radio_commands = [
            "BrowseRadioStations",
            "BrowseRadio",
            "GetRadioStations",
            "ListRadioStations",
            "BrowseServices",
            "BrowseTuneIn",
        ]

        for cmd in radio_commands:
            print("=" * 60)
            print(f"Testing: {cmd}")
            print("=" * 60)

            try:
                response = await client._execute_command(cmd, retry_on_error=False)
                if response and "Error" not in response[0]:
                    print(f"[OK] SUCCESS! Got {len(response)} lines")
                    print(f"First 5 lines:")
                    for line in response[:5]:
                        print(f"  {line[:100]}")

                    # Check if it has XML
                    xml_data = '\n'.join(response)
                    if '<PickListItem' in xml_data:
                        print("\n[OK] Contains PickListItem XML!")
                        # Try to parse
                        import re
                        matches = list(re.finditer(r'<PickListItem[^>]*>', xml_data))
                        print(f"[OK] Found {len(matches)} items")
                        if matches:
                            for i, match in enumerate(matches[:3]):
                                item_str = match.group(0)
                                title = re.search(r'title="([^"]*)"', item_str)
                                if title:
                                    print(f"  Item {i}: {title.group(1)}")

                    # If we found a working command, try to use it
                    if len(response) > 2 and "Error" not in response[0]:
                        print(f"\n[OK] {cmd} WORKS! This is the command we need!")
                        break
                else:
                    print(f"[FAIL] Error: {response[0] if response else 'No response'}")

            except Exception as e:
                print(f"[FAIL] Exception: {e}")

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
    asyncio.run(test_radio_browse())
