"""Query MCS server for available commands and try variations."""

import asyncio
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def test_mcs_help():
    """Test help commands and BrowsePickList variations."""

    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        await client.set_instance('Music_Server_A')

        # Test 1: Get help
        print("=" * 60)
        print("Getting MCS command help...")
        print("=" * 60)
        response = await client._execute_command("?")
        for line in response[:20]:
            print(line)

        print("\n" + "=" * 60)
        print("Getting help for BrowsePickList...")
        print("=" * 60)
        response = await client._execute_command("help BrowsePickList")
        for line in response:
            print(line)

        # Test 2: Try BrowsePickList with a GUID parameter
        print("\n" + "=" * 60)
        print("Try BrowsePickList with root GUID...")
        print("=" * 60)
        # Try with empty GUID or root GUID
        for guid in ["", "00000000-0000-0000-0000-000000000000", "root", "/"]:
            print(f"\nTrying BrowsePickList {guid}...")
            try:
                response = await client._execute_command(f"BrowsePickList {guid}")
                if "Error" not in response[0]:
                    print(f"[OK] Got response: {response[:3]}")
                    break
                else:
                    print(f"[FAIL] Error: {response[0]}")
            except Exception as e:
                print(f"[FAIL] Exception: {e}")

        # Test 3: Try Browse command without PickList
        print("\n" + "=" * 60)
        print("Try Browse command...")
        print("=" * 60)
        response = await client._execute_command("Browse")
        print(f"Response: {response[:3] if len(response) > 3 else response}")

        # Test 4: Try GetMenu
        print("\n" + "=" * 60)
        print("Try GetMenu command...")
        print("=" * 60)
        response = await client._execute_command("GetMenu")
        print(f"Response: {response[:3] if len(response) > 3 else response}")

        # Test 5: Try GetNavigationState
        print("\n" + "=" * 60)
        print("Try GetNavigationState...")
        print("=" * 60)
        response = await client._execute_command("GetNavigationState")
        for line in response[:10]:
            print(line)

        await client.disconnect()

    except Exception as e:
        print(f"\n!!! ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if client._connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_mcs_help())
