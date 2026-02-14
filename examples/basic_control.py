#!/usr/bin/env python3
"""
Basic control example for NuVo MusicPort SDK.

This example demonstrates:
- Connecting to device
- Discovering zones and sources
- Controlling zones (power, volume)
- Subscribing to events
"""

import asyncio
from nuvo_sdk import NuVoClient, StateChangeEvent

# Configure your device
DEVICE_IP = "10.0.0.45"


async def on_state_change(event: StateChangeEvent):
    """Handle state change events."""
    print(f"Event: {event.target} {event.property}={event.value}")


async def main():
    """Main control flow."""
    # Create client
    client = NuVoClient(DEVICE_IP)

    try:
        # Connect to device
        print(f"Connecting to {DEVICE_IP}...")
        await client.connect()
        print("Connected!")

        # Subscribe to state change events
        client.subscribe(on_state_change)

        # Get system status
        print("\n--- System Status ---")
        status = await client.get_status()
        print(f"Device: {status.device_type}")
        print(f"Firmware: {status.firmware_version}")
        print(f"Zones: {len(status.zones)}")
        print(f"Sources: {len(status.sources)}")

        # List zones
        print("\n--- Zones ---")
        zones = await client.get_zones()
        for zone in zones:
            power_state = "ON" if zone.is_on else "OFF"
            print(f"{zone.zone_number}. {zone.name:20s} [{power_state}] Vol: {zone.volume:2d}")

        # List sources
        print("\n--- Sources ---")
        sources = await client.get_sources()
        for source in sources:
            source_type = "Smart" if source.is_smart else "Standard"
            print(f"{source.source_id}. {source.name:20s} [{source_type}]")

        # Example: Control first zone
        if zones:
            zone = zones[0]
            print(f"\n--- Controlling {zone.name} ---")

            # Set active zone
            await client.set_zone(zone.guid)
            print(f"Set active zone to: {zone.name}")

            # Turn on
            print("Turning on...")
            await client.power_on(zone.zone_number)
            await asyncio.sleep(1.0)

            # Set volume to 50
            print("Setting volume to 50...")
            await client.set_volume(50, zone.zone_number)
            await asyncio.sleep(1.0)

            # Set source (if available)
            if sources:
                print(f"Changing source to: {sources[0].name}")
                await client.set_source(sources[0].guid)
                await asyncio.sleep(1.0)

            # Mute toggle
            print("Toggling mute...")
            await client.mute_toggle(zone.zone_number)
            await asyncio.sleep(1.0)

            # Unmute
            print("Unmuting...")
            await client.mute_toggle(zone.zone_number)
            await asyncio.sleep(1.0)

            # Turn off
            print("Turning off...")
            await client.power_off(zone.zone_number)

        # Wait a bit to see events
        print("\nWaiting for events...")
        await asyncio.sleep(2.0)

    finally:
        # Disconnect
        print("\nDisconnecting...")
        await client.disconnect()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
