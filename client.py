#!/usr/bin/env python3
"""
Nuvo MusicPort Client
Send commands to the MusicPort device once protocol is understood
"""

import socket
import sys
import time

MUSICPORT_IP = "10.0.0.45"

class MusicPortClient:
    def __init__(self, ip, port, protocol='tcp'):
        self.ip = ip
        self.port = port
        self.protocol = protocol.lower()
        self.socket = None

    def connect(self):
        """Connect to the MusicPort"""
        try:
            if self.protocol == 'tcp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5)
                print(f"Connecting to {self.ip}:{self.port} (TCP)...")
                self.socket.connect((self.ip, self.port))
                print("Connected!")
                return True
            elif self.protocol == 'udp':
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                print(f"UDP socket created for {self.ip}:{self.port}")
                return True
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False

    def send_hex(self, hex_string):
        """Send command as hex string (e.g., '0a1b2c3d')"""
        try:
            # Remove spaces and convert to bytes
            hex_clean = hex_string.replace(' ', '').replace(':', '')
            data = bytes.fromhex(hex_clean)

            print(f"\nSending {len(data)} bytes:")
            print(f"  HEX: {data.hex()}")
            print(f"  ASCII: {data.decode('ascii', errors='ignore')}")

            if self.protocol == 'tcp':
                self.socket.send(data)
            else:
                self.socket.sendto(data, (self.ip, self.port))

            # Try to receive response
            return self.receive()

        except Exception as e:
            print(f"[!] Send failed: {e}")
            return None

    def send_ascii(self, text):
        """Send command as ASCII text"""
        try:
            data = text.encode('ascii')

            print(f"\nSending {len(data)} bytes:")
            print(f"  ASCII: {text}")
            print(f"  HEX: {data.hex()}")

            if self.protocol == 'tcp':
                self.socket.send(data)
            else:
                self.socket.sendto(data, (self.ip, self.port))

            # Try to receive response
            return self.receive()

        except Exception as e:
            print(f"[!] Send failed: {e}")
            return None

    def receive(self, buffer_size=4096):
        """Receive response from device"""
        try:
            self.socket.settimeout(2)
            if self.protocol == 'tcp':
                data = self.socket.recv(buffer_size)
            else:
                data, addr = self.socket.recvfrom(buffer_size)

            if data:
                print(f"\nReceived {len(data)} bytes:")
                print(f"  HEX: {data.hex()}")
                print(f"  ASCII: {data.decode('ascii', errors='ignore')}")
                return data
            else:
                print("No response received")
                return None

        except socket.timeout:
            print("No response (timeout)")
            return None
        except Exception as e:
            print(f"[!] Receive error: {e}")
            return None

    def close(self):
        """Close connection"""
        if self.socket:
            self.socket.close()
            print("Connection closed")

def interactive_mode(client):
    """Interactive command shell"""
    print("\n" + "=" * 60)
    print("Interactive Mode")
    print("=" * 60)
    print("Commands:")
    print("  hex <hexstring>  - Send hex command (e.g., hex 0a1b2c3d)")
    print("  ascii <text>     - Send ASCII command")
    print("  quit             - Exit")
    print("=" * 60)

    while True:
        try:
            cmd = input("\n> ").strip()

            if not cmd:
                continue

            if cmd == 'quit':
                break

            parts = cmd.split(' ', 1)
            if len(parts) < 2:
                print("Invalid command")
                continue

            cmd_type, payload = parts

            if cmd_type == 'hex':
                client.send_hex(payload)
            elif cmd_type == 'ascii':
                client.send_ascii(payload)
            else:
                print("Unknown command type")

            time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

def main():
    print("=" * 60)
    print("Nuvo MusicPort Client")
    print("=" * 60)

    if len(sys.argv) < 3:
        print("\nUsage:")
        print("  python client.py <port> <protocol>")
        print("\nExample:")
        print("  python client.py 8000 tcp")
        print("  python client.py 5353 udp")
        sys.exit(1)

    port = int(sys.argv[1])
    protocol = sys.argv[2]

    client = MusicPortClient(MUSICPORT_IP, port, protocol)

    if client.connect():
        interactive_mode(client)
        client.close()

if __name__ == "__main__":
    main()
