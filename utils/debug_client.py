#!/usr/bin/env python3
"""Debug script to test basic client communication."""

import asyncio

DEVICE_IP = "10.0.0.45"
DEVICE_PORT = 5006


async def test_raw_connection():
    """Test raw TCP connection without SDK."""
    print(f"Connecting to {DEVICE_IP}:{DEVICE_PORT}...")

    reader, writer = await asyncio.open_connection(DEVICE_IP, DEVICE_PORT)

    # Send wake-up command first (as seen in packet capture)
    print("\n--- Sending wake-up (*) ---")
    writer.write(b"*\r")
    await writer.drain()
    await asyncio.sleep(0.3)

    # Read banner
    print("\n--- Reading banner ---")
    try:
        banner = await asyncio.wait_for(reader.readuntil(b"\x07"), timeout=3.0)
        print(banner.decode("utf-8", errors="ignore"))
    except asyncio.TimeoutError:
        print("Banner timeout - reading what's available...")
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=0.5)
            print(data.decode("utf-8", errors="ignore"))
        except:
            pass

    # Send init commands (exactly as in packet capture)
    commands = [
        "setHost 10.0.0.25\rSetXMLMode Lists\rSubscribeEvents smart\rBrowseZones\rGetStatus\r",
    ]

    for cmd in commands:
        print(f"\n--- Sending: {cmd.strip()} ---")
        writer.write(cmd.encode("utf-8"))
        await writer.drain()
        await asyncio.sleep(0.2)

        # Read response
        print("Reading response...")
        lines = []
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 2.0:
            try:
                line = await asyncio.wait_for(reader.readline(), timeout=0.5)
                if not line:
                    break
                decoded = line.decode("utf-8", errors="ignore").strip()
                if decoded:
                    print(f"  {decoded}")
                    lines.append(decoded)
                    if decoded.endswith(">") or decoded == "Ok":
                        break
            except asyncio.TimeoutError:
                if lines:
                    break

    # Close
    writer.close()
    await writer.wait_closed()
    print("\nDisconnected")


if __name__ == "__main__":
    asyncio.run(test_raw_connection())
