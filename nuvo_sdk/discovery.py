"""Network discovery for NuVo MusicPort devices."""

import asyncio
import ipaddress
import socket
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class DiscoveredDevice:
    """Discovered NuVo MusicPort device."""

    ip: str
    hostname: Optional[str] = None
    mrad_port: int = 5006  # Multi-room control
    mcs_port: int = 5004   # Music control
    responds_to_mrad: bool = False
    responds_to_mcs: bool = False
    device_info: Optional[str] = None


async def scan_port(ip: str, port: int, timeout: float = 1.0) -> bool:
    """
    Check if a port is open on an IP address.

    Args:
        ip: IP address to scan
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if port is open, False otherwise
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False


async def probe_mrad_port(ip: str, port: int = 5006, timeout: float = 2.0) -> Optional[str]:
    """
    Probe MRAD port and try to identify device.

    Args:
        ip: IP address
        port: MRAD port (default 5006)
        timeout: Connection timeout

    Returns:
        Device info string if successful, None otherwise
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port),
            timeout=timeout
        )

        # Send wake-up command
        writer.write(b"*\r")
        await writer.drain()

        # Try to read banner
        try:
            banner = await asyncio.wait_for(
                reader.readuntil(b"\x07"),  # Bell character
                timeout=1.0
            )
            device_info = banner.decode("utf-8", errors="ignore")

            # Look for NuVo identification
            if "NuVo" in device_info or "Autonomic" in device_info:
                writer.close()
                await writer.wait_closed()
                return device_info.strip()

        except asyncio.TimeoutError:
            pass

        writer.close()
        await writer.wait_closed()
        return "Unknown device"

    except Exception:
        return None


async def scan_device(ip: str) -> Optional[DiscoveredDevice]:
    """
    Scan a single IP for NuVo MusicPort.

    Args:
        ip: IP address to scan

    Returns:
        DiscoveredDevice if found, None otherwise
    """
    # Check both ports
    mrad_open = await scan_port(ip, 5006, timeout=0.5)
    mcs_open = await scan_port(ip, 5004, timeout=0.5)

    if not (mrad_open or mcs_open):
        return None

    # If MRAD port is open, try to identify device
    device_info = None
    if mrad_open:
        device_info = await probe_mrad_port(ip, timeout=1.0)

    # Get hostname
    hostname = None
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except:
        pass

    return DiscoveredDevice(
        ip=ip,
        hostname=hostname,
        mrad_port=5006,
        mcs_port=5004,
        responds_to_mrad=mrad_open,
        responds_to_mcs=mcs_open,
        device_info=device_info,
    )


async def discover_devices(
    network: str = "192.168.1.0/24",
    max_concurrent: int = 50,
) -> List[DiscoveredDevice]:
    """
    Discover NuVo MusicPort devices on the network.

    Args:
        network: Network CIDR (e.g., "192.168.1.0/24")
        max_concurrent: Maximum concurrent scans

    Returns:
        List of discovered devices

    Example:
        >>> devices = await discover_devices("192.168.1.0/24")
        >>> for device in devices:
        >>>     print(f"Found NuVo at {device.ip}")
    """
    # Parse network
    try:
        net = ipaddress.ip_network(network, strict=False)
    except ValueError as e:
        raise ValueError(f"Invalid network: {e}")

    # Get all host IPs
    hosts = [str(ip) for ip in net.hosts()]

    # Scan in batches
    devices = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def scan_with_semaphore(ip: str):
        async with semaphore:
            return await scan_device(ip)

    # Scan all hosts
    tasks = [scan_with_semaphore(ip) for ip in hosts]
    results = await asyncio.gather(*tasks)

    # Filter out None results
    devices = [d for d in results if d is not None]

    return devices


def get_local_network() -> str:
    """
    Get the local network CIDR.

    Returns:
        Network CIDR string (e.g., "192.168.1.0/24")
    """
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        # Assume /24 network
        parts = local_ip.split(".")
        parts[-1] = "0"
        network = ".".join(parts) + "/24"

        return network
    except:
        return "192.168.1.0/24"


# CLI interface
async def main():
    """CLI for device discovery."""
    import sys

    print("NuVo MusicPort Network Discovery")
    print("=" * 50)

    # Get network to scan
    if len(sys.argv) > 1:
        network = sys.argv[1]
    else:
        network = get_local_network()
        print(f"Auto-detected network: {network}")

    print(f"\nScanning {network} for NuVo devices...")
    print("This may take a minute...\n")

    devices = await discover_devices(network, max_concurrent=100)

    if not devices:
        print("[!] No NuVo MusicPort devices found")
        return

    print(f"[+] Found {len(devices)} device(s):\n")

    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.ip}")
        if device.hostname:
            print(f"   Hostname: {device.hostname}")
        print(f"   MRAD (5006): {'[Y]' if device.responds_to_mrad else '[N]'}")
        print(f"   MCS (5004):  {'[Y]' if device.responds_to_mcs else '[N]'}")
        if device.device_info:
            # Clean up device info
            info = device.device_info.replace("\r\n", " ").replace("\n", " ")
            if "NuVo" in info or "Autonomic" in info:
                # Extract version info
                import re
                match = re.search(r"version\s+([\d.]+)", info, re.IGNORECASE)
                if match:
                    print(f"   Version: {match.group(1)}")
        print()

    print("To connect to a device:")
    print(f"  python -c 'from nuvo_sdk import NuVoClient; import asyncio; asyncio.run(NuVoClient(\"{devices[0].ip}\").connect())'")


if __name__ == "__main__":
    asyncio.run(main())
