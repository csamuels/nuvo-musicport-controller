#!/usr/bin/env python3
"""
Nuvo MusicPort HTTP/API Explorer
Test if the device has an HTTP API
"""

import requests
import socket
from urllib.parse import urljoin

MUSICPORT_IP = "10.0.0.45"
COMMON_PORTS = [80, 8000, 8008, 8080, 8443, 443, 5000]
COMMON_PATHS = [
    "/",
    "/api",
    "/api/v1",
    "/api/status",
    "/status",
    "/info",
    "/device",
    "/control",
    "/zones",
    "/sources",
    "/volume",
    "/help",
    "/docs",
    "/swagger",
    "/api-docs",
    "/description.xml",  # UPnP
    "/MediaRenderer/desc.xml",  # UPnP
]

def check_port_open(ip, port, timeout=1):
    """Check if port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_http_endpoint(base_url, path):
    """Test an HTTP endpoint"""
    url = urljoin(base_url, path)
    try:
        # Try GET request
        response = requests.get(url, timeout=3)
        print(f"  [+] {path}")
        print(f"      Status: {response.status_code}")
        print(f"      Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"      Size: {len(response.content)} bytes")

        # Show preview of content
        if response.status_code == 200:
            content_preview = response.text[:200]
            print(f"      Preview: {content_preview}...")

        return True

    except requests.exceptions.RequestException:
        return False

def explore_http_api(ip, port):
    """Explore HTTP API on given port"""
    print(f"\n{'='*60}")
    print(f"Exploring HTTP on {ip}:{port}")
    print('='*60)

    # Try both HTTP and HTTPS
    for protocol in ['http', 'https']:
        base_url = f"{protocol}://{ip}:{port}"
        print(f"\nTrying {base_url}...")

        try:
            # Test root first
            response = requests.get(base_url, timeout=3, verify=False)
            print(f"\n[+] {protocol.upper()} is accessible!")
            print(f"    Status: {response.status_code}")
            print(f"    Server: {response.headers.get('Server', 'unknown')}")

            # Test common paths
            print(f"\n  Testing common API endpoints...")
            found_paths = []

            for path in COMMON_PATHS:
                if test_http_endpoint(base_url, path):
                    found_paths.append(path)

            if found_paths:
                print(f"\n  Found {len(found_paths)} accessible endpoint(s)")
            else:
                print(f"\n  No additional endpoints found")

            return True

        except requests.exceptions.SSLError:
            print(f"  [-] {protocol.upper()} SSL error (certificate issue)")
        except requests.exceptions.ConnectionError:
            print(f"  [-] {protocol.upper()} not accessible")
        except Exception as e:
            print(f"  [-] {protocol.upper()} error: {e}")

    return False

def check_upnp(ip):
    """Check for UPnP services"""
    print(f"\n{'='*60}")
    print("Checking for UPnP/DLNA")
    print('='*60)

    import socket
    from xml.dom import minidom

    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    SSDP_MX = 1
    SSDP_ST = "ssdp:all"

    msg = f"M-SEARCH * HTTP/1.1\r\n" \
          f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n" \
          f"MAN: \"ssdp:discover\"\r\n" \
          f"MX: {SSDP_MX}\r\n" \
          f"ST: {SSDP_ST}\r\n" \
          f"\r\n"

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(3)
        sock.sendto(msg.encode(), (SSDP_ADDR, SSDP_PORT))

        responses = []
        while True:
            try:
                data, addr = sock.recvfrom(65507)
                if addr[0] == ip:
                    responses.append(data.decode('utf-8', errors='ignore'))
            except socket.timeout:
                break

        if responses:
            print(f"[+] Found UPnP device!")
            for i, response in enumerate(responses, 1):
                print(f"\nResponse {i}:")
                print(response)
            return True
        else:
            print("[-] No UPnP response from device")
            return False

    except Exception as e:
        print(f"[-] UPnP check failed: {e}")
        return False

def main():
    print("="*60)
    print("Nuvo MusicPort HTTP/API Explorer")
    print("="*60)

    # Check which HTTP ports are open
    print(f"\nScanning for HTTP services on {MUSICPORT_IP}...")
    open_ports = []

    for port in COMMON_PORTS:
        if check_port_open(MUSICPORT_IP, port):
            print(f"  [+] Port {port} is OPEN")
            open_ports.append(port)
        else:
            print(f"  [-] Port {port} is closed")

    # Explore each open port
    if open_ports:
        for port in open_ports:
            explore_http_api(MUSICPORT_IP, port)
    else:
        print("\n[!] No HTTP ports found open")

    # Check for UPnP
    check_upnp(MUSICPORT_IP)

    print("\n" + "="*60)
    print("Exploration complete!")
    print("="*60)

if __name__ == "__main__":
    # Disable SSL warnings for self-signed certificates
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    main()
