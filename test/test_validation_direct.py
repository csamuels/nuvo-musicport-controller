"""Direct test of validation endpoint."""

import asyncio
import sys
sys.path.insert(0, 'C:/Users/Corey/PycharmProjects/musicport')

from api.routes.tunein import validate_all_stations, get_working_stations
from nuvo_sdk.mcs_client_simple import SimpleMCSClient


async def main():
    """Test validation directly."""
    client = SimpleMCSClient('10.0.0.45', 5004)

    try:
        await client.connect()
        print("[TEST] Connected to MCS")

        print("\n[TEST] Testing validate_all_stations function...")
        results = await validate_all_stations(instance="Music_Server_A", mcs_client=client)

        print(f"\n[TEST] Got {len(results)} validation results:")
        for r in results:
            status = "[OK] VALID" if r.appears_valid else "[X] INVALID"
            print(f"  {status} | {r.title}")
            if not r.appears_valid:
                print(f"           | {r.message}")

        # Check Hot 97 specifically
        hot_97 = [r for r in results if "Hot 97" in r.title]
        if hot_97:
            r = hot_97[0]
            print(f"\n[TEST] Hot 97 Status: {'VALID' if r.appears_valid else 'INVALID'}")
            print(f"[TEST] Message: {r.message}")

        await client.disconnect()

    except Exception as e:
        print(f"[TEST] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
