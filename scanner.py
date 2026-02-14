#!/usr/bin/env python3
"""
Nuvo MusicPort Network Scanner
Scans the MusicPort device for open ports and services
"""

import socket
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

MUSICPORT_IP = "10.0.0.45"
COMMON_PORTS = [
    20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
    3389, 5000, 5001, 8000, 8008, 8080, 8443, 8888, 9000,
    # Audio/streaming specific ports
    554, 1755, 5353, 6000, 7000, 8001, 9001, 50000
]

def scan_port(ip, port, timeout=1):
    """Scan a single port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return port, result == 0
    except socket.error:
        return port, False

def get_service_name(port):
    """Get common service name for port"""
    try:
        return socket.getservbyport(port)
    except:
        return "unknown"

def scan_device(ip, ports, max_workers=50):
    """Scan device for open ports"""
    print(f"Scanning {ip} for open ports...")
    print(f"Testing {len(ports)} ports\n")

    open_ports = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_port = {executor.submit(scan_port, ip, port): port for port in ports}

        for future in as_completed(future_to_port):
            port, is_open = future.result()
            if is_open:
                service = get_service_name(port)
                open_ports.append((port, service))
                print(f"[+] Port {port} is OPEN - {service}")

    return open_ports

def try_connect_and_banner(ip, port):
    """Try to grab banner from open port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ip, port))

        # Try to receive banner
        try:
            banner = sock.recv(1024)
            print(f"\n[*] Banner from port {port}:")
            print(banner.decode('utf-8', errors='ignore'))
        except:
            # Try sending HTTP request for web services
            if port in [80, 443, 8000, 8008, 8080, 8443]:
                sock.send(b"GET / HTTP/1.1\r\nHost: " + ip.encode() + b"\r\n\r\n")
                response = sock.recv(4096)
                print(f"\n[*] HTTP Response from port {port}:")
                print(response.decode('utf-8', errors='ignore')[:500])

        sock.close()
    except Exception as e:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print("Nuvo MusicPort Network Scanner")
    print("=" * 60)

    # Scan common ports
    open_ports = scan_device(MUSICPORT_IP, COMMON_PORTS)

    if not open_ports:
        print("\n[!] No open ports found. The device may be offline or filtered.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"Summary: Found {len(open_ports)} open port(s)")
    print("=" * 60)

    for port, service in open_ports:
        print(f"  {port}/{service}")

    # Try to grab banners
    print("\n" + "=" * 60)
    print("Attempting to grab banners...")
    print("=" * 60)

    for port, service in open_ports:
        try_connect_and_banner(MUSICPORT_IP, port)
