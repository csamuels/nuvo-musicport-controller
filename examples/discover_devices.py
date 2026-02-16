#!/usr/bin/env python3
"""
Example: Discover NuVo MusicPort devices on your network.
"""

import asyncio
from nuvo_sdk.discovery import discover_devices, get_local_network


async def main():
    """Discover and display NuVo devices."""

    # Auto-detect local network
    network = get_local_network()
    print(f"Scanning {network} for NuVo MusicPort devices...")

    # Discover devices
    devices = await discover_devices(network)

    if not devices:
        print("No devices found!")
        return

    print(f"\nFound {len(devices)} device(s):\n")

    for device in devices:
        print(f"[*] {device.ip}")
        if device.hostname:
            print(f"   Name: {device.hostname}")
        print(f"   MRAD Port: {device.responds_to_mrad}")
        print(f"   MCS Port: {device.responds_to_mcs}")
        if device.device_info:
            print(f"   Info: {device.device_info[:60]}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())
