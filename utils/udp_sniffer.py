#!/usr/bin/env python3
"""
Nuvo MusicPort UDP Sniffer
Captures UDP traffic by binding to a port and logging all data
Works without any special drivers!
"""

import socket
import datetime
import json
import sys
import os

LOG_FILE = r"C:\Users\Corey\PycharmProjects\musicport\tmp\sniff-output.txt"

class UDPSniffer:
    def __init__(self, port):
        self.port = port
        self.log_data = []
        self.packet_count = 0

    def log_packet(self, data, addr):
        """Log captured packet"""
        self.packet_count += 1
        timestamp = datetime.datetime.now().isoformat()

        log_entry = {
            'timestamp': timestamp,
            'packet_num': self.packet_count,
            'source_ip': addr[0],
            'source_port': addr[1],
            'length': len(data),
            'hex': data.hex(),
            'ascii': data.decode('ascii', errors='ignore')
        }

        self.log_data.append(log_entry)

        # Print to console
        print(f"\n[{timestamp}] Packet #{self.packet_count}")
        print(f"  From: {addr[0]}:{addr[1]}")
        print(f"  Length: {len(data)} bytes")
        print(f"  HEX: {data.hex()}")
        print(f"  ASCII: {data.decode('ascii', errors='ignore')[:100]}")

        # Save log every 5 packets
        if self.packet_count % 5 == 0:
            self.save_log()

    def save_log(self):
        """Save log to file"""
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'w') as f:
                json.dump(self.log_data, f, indent=2)
        except Exception as e:
            print(f"[!] Warning: Could not save log: {e}")

    def start(self):
        """Start listening for UDP packets"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(('0.0.0.0', self.port))
            print(f"[*] Listening for UDP packets on port {self.port}...")
            print("[*] Send data from your iPhone app or MusicPort")
            print("[*] Press Ctrl+C to stop\n")

            while True:
                data, addr = sock.recvfrom(65535)
                self.log_packet(data, addr)

        except KeyboardInterrupt:
            print("\n\n[*] Stopping capture...")
            self.save_log()
            print(f"[*] Captured {self.packet_count} packets")
            print(f"[*] Log saved to {LOG_FILE}")

        except Exception as e:
            print(f"\n[!] Error: {e}")

        finally:
            sock.close()

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Nuvo MusicPort UDP Sniffer")
        print("=" * 60)
        print("\nUsage: python udp_sniffer.py <port>")
        print("\nExample:")
        print("  python udp_sniffer.py 5353")
        print("\nThis will listen for UDP packets on the specified port")
        print("Run scanner.py first to find which UDP ports to monitor!")
        sys.exit(1)

    port = int(sys.argv[1])

    print("=" * 60)
    print("Nuvo MusicPort UDP Sniffer")
    print("=" * 60)
    print()

    sniffer = UDPSniffer(port)
    sniffer.start()

if __name__ == "__main__":
    main()
