"""Test BrowseRadioStations and parse full response."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_full_radio():
    """Get full BrowseRadioStations response."""

    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        print("=" * 60)
        print("BrowseRadioStations - Full Response")
        print("=" * 60)

        response = await client._execute_command("BrowseRadioStations", retry_on_error=False)

        print(f"Got {len(response)} lines\n")

        # Join all lines
        xml_data = '\n'.join(response)
        print("Full XML:")
        print(xml_data)

        print("\n" + "=" * 60)
        print("Parsing Radio Stations")
        print("=" * 60)

        # Parse with regex
        import re
        import xml.etree.ElementTree as ET

        try:
            # Try to parse as XML
            root = ET.fromstring(xml_data)
            print(f"Root tag: {root.tag}")
            print(f"Root attributes: {root.attrib}")

            # Find all RadioStation children
            for station in root.findall('.//RadioStation'):
                name = station.get('name', 'Unknown')
                guid = station.get('guid', '')
                print(f"  - {name} (guid: {guid[:30]}...)")

        except ET.ParseError as e:
            print(f"XML parse error: {e}")

            # Fall back to regex
            print("\nTrying regex parsing...")
            matches = re.finditer(r'<RadioStation[^>]*>', xml_data)
            for i, match in enumerate(matches):
                item_str = match.group(0)
                name_match = re.search(r'name="([^"]*)"', item_str)
                guid_match = re.search(r'guid="([^"]*)"', item_str)

                if name_match:
                    name = name_match.group(1)
                    guid = guid_match.group(1) if guid_match else ""
                    print(f"  {i+1}. {name}")
                    print(f"     GUID: {guid[:50]}...")

        await client.disconnect()

    except Exception as e:
        print(f"\n!!! ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client._connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_full_radio())
