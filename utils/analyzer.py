#!/usr/bin/env python3
"""
Nuvo MusicPort Protocol Analyzer
Analyzes captured packet logs to identify command patterns
"""

import json
import re
from collections import Counter, defaultdict

LOG_FILE = "musicport_packets.log"

class ProtocolAnalyzer:
    def __init__(self, log_file):
        with open(log_file, 'r') as f:
            self.packets = json.load(f)

    def analyze_payload_patterns(self):
        """Identify common patterns in payloads"""
        print("\n" + "=" * 60)
        print("Payload Pattern Analysis")
        print("=" * 60)

        payloads_to_device = []
        payloads_from_device = []

        for pkt in self.packets:
            if 'payload_hex' in pkt:
                if pkt['direction'] == 'TO':
                    payloads_to_device.append(pkt)
                else:
                    payloads_from_device.append(pkt)

        print(f"\nCommands TO device: {len(payloads_to_device)}")
        print(f"Responses FROM device: {len(payloads_from_device)}")

        # Analyze commands TO device
        if payloads_to_device:
            print("\n--- Commands Sent TO MusicPort ---")
            for i, pkt in enumerate(payloads_to_device[:20]):  # Show first 20
                print(f"\n[{i+1}] {pkt['timestamp']}")
                print(f"  HEX:   {pkt['payload_hex']}")
                print(f"  ASCII: {pkt['payload_ascii'][:80]}")
                print(f"  Bytes: {pkt['payload_length']}")

        # Analyze responses FROM device
        if payloads_from_device:
            print("\n--- Responses FROM MusicPort ---")
            for i, pkt in enumerate(payloads_from_device[:20]):  # Show first 20
                print(f"\n[{i+1}] {pkt['timestamp']}")
                print(f"  HEX:   {pkt['payload_hex']}")
                print(f"  ASCII: {pkt['payload_ascii'][:80]}")
                print(f"  Bytes: {pkt['payload_length']}")

    def find_common_headers(self):
        """Identify common header bytes"""
        print("\n" + "=" * 60)
        print("Common Header Analysis")
        print("=" * 60)

        headers = []
        for pkt in self.packets:
            if 'payload_hex' in pkt and pkt['direction'] == 'TO':
                # Get first 8 bytes (16 hex chars)
                header = pkt['payload_hex'][:16]
                if header:
                    headers.append(header)

        if headers:
            header_counts = Counter(headers)
            print("\nMost common command headers:")
            for header, count in header_counts.most_common(10):
                print(f"  {header}: {count} times")

    def group_by_connection(self):
        """Group packets by connection (port pairs)"""
        print("\n" + "=" * 60)
        print("Connection Analysis")
        print("=" * 60)

        connections = defaultdict(list)
        for pkt in self.packets:
            if 'src_port' in pkt and 'dst_port' in pkt:
                conn_key = f"{pkt['src_port']}-{pkt['dst_port']}"
                connections[conn_key].append(pkt)

        print(f"\nFound {len(connections)} unique connection pairs:")
        for conn, packets in connections.items():
            print(f"\n  Connection {conn}: {len(packets)} packets")
            if packets and 'protocol_name' in packets[0]:
                print(f"    Protocol: {packets[0]['protocol_name']}")

    def identify_ascii_commands(self):
        """Look for ASCII/text-based commands"""
        print("\n" + "=" * 60)
        print("ASCII Command Detection")
        print("=" * 60)

        ascii_commands = []
        for pkt in self.packets:
            if 'payload_ascii' in pkt and pkt['direction'] == 'TO':
                ascii = pkt['payload_ascii'].strip()
                # Check if mostly printable ASCII
                if len(ascii) > 3 and sum(c.isprintable() for c in ascii) / len(ascii) > 0.7:
                    ascii_commands.append(ascii)

        if ascii_commands:
            print("\nPossible ASCII commands found:")
            unique_commands = set(ascii_commands)
            for cmd in list(unique_commands)[:30]:
                print(f"  {repr(cmd)}")
        else:
            print("\nNo clear ASCII commands detected (may be binary protocol)")

    def export_unique_commands(self):
        """Export unique command patterns"""
        commands = {}
        cmd_id = 1

        for pkt in self.packets:
            if 'payload_hex' in pkt and pkt['direction'] == 'TO':
                hex_payload = pkt['payload_hex']
                if hex_payload not in commands:
                    commands[hex_payload] = {
                        'id': cmd_id,
                        'hex': hex_payload,
                        'ascii': pkt.get('payload_ascii', ''),
                        'length': pkt['payload_length'],
                        'timestamp': pkt['timestamp']
                    }
                    cmd_id += 1

        # Save to file
        with open('commands.json', 'w') as f:
            json.dump(list(commands.values()), f, indent=2)

        print(f"\nExported {len(commands)} unique commands to commands.json")

def main():
    print("=" * 60)
    print("Nuvo MusicPort Protocol Analyzer")
    print("=" * 60)

    try:
        analyzer = ProtocolAnalyzer(LOG_FILE)

        print(f"\nLoaded {len(analyzer.packets)} packets from {LOG_FILE}")

        analyzer.group_by_connection()
        analyzer.identify_ascii_commands()
        analyzer.find_common_headers()
        analyzer.analyze_payload_patterns()
        analyzer.export_unique_commands()

        print("\n" + "=" * 60)
        print("Analysis Complete!")
        print("=" * 60)

    except FileNotFoundError:
        print(f"\n[!] Error: {LOG_FILE} not found.")
        print("Run sniffer.py first to capture packets.")

if __name__ == "__main__":
    main()
