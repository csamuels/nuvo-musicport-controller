"""Diagnose MRAD connection issues."""

import asyncio
import sys
sys.path.insert(0, 'C:/Users/Corey/PycharmProjects/musicport')

from nuvo_sdk import NuVoClient


async def test_mrad_connection():
    """Test direct MRAD connection."""
    print("=" * 60)
    print("MRAD CONNECTION DIAGNOSTIC")
    print("=" * 60)

    client = NuVoClient('10.0.0.45', 5006)

    try:
        print("\n[1] Attempting to connect to MRAD (10.0.0.45:5006)...")
        await client.connect()
        print("[OK] Connected successfully!")
        print(f"    Connected: {client._connected}")

        print("\n[2] Testing get_zones command...")
        zones = await client.get_zones()
        print(f"[OK] Got {len(zones)} zones")
        for z in zones[:3]:
            print(f"    Zone {z.zone_number}: {z.name}")

        print("\n[3] Disconnecting...")
        await client.disconnect()
        print("[OK] Disconnected")

        print("\n[SUCCESS] MRAD connection is working!")
        return True

    except Exception as e:
        print(f"\n[ERROR] Connection failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mrad_connection())
    sys.exit(0 if success else 1)
