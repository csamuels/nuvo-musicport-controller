#!/usr/bin/env python3
"""
Test the MCS Control Port 5004
"""

import socket
import time

MUSICPORT_IP = "10.0.0.45"
CONTROL_PORT = 5004

def test_connection():
    """Try to connect to control port"""
    try:
        print(f"Connecting to {MUSICPORT_IP}:{CONTROL_PORT}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((MUSICPORT_IP, CONTROL_PORT))
        print("[+] Connected!")

        # Try to receive initial data
        print("\nWaiting for initial data...")
        time.sleep(1)
        try:
            data = sock.recv(4096)
            if data:
                print(f"Received {len(data)} bytes:")
                print(f"  HEX: {data.hex()}")
                print(f"  ASCII: {data.decode('ascii', errors='ignore')}")
        except socket.timeout:
            print("No initial data received")

        # Try sending some test commands
        test_commands = [
            b"?\r\n",
            b"HELP\r\n",
            b"STATUS\r\n",
            b"VER\r\n",
        ]

        for cmd in test_commands:
            print(f"\nSending: {cmd}")
            sock.send(cmd)
            time.sleep(0.5)

            try:
                response = sock.recv(4096)
                if response:
                    print(f"Response ({len(response)} bytes):")
                    print(f"  HEX: {response.hex()}")
                    print(f"  ASCII: {response.decode('ascii', errors='ignore')}")
            except socket.timeout:
                print("  No response")

        sock.close()

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    test_connection()
