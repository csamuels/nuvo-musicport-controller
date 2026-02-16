#!/usr/bin/env python3
"""
Nuvo MusicPort Packet Sniffer
Captures and analyzes network traffic to/from the MusicPort device
Requires: pip install scapy
"""

from scapy.all import sniff, IP, TCP, UDP, Raw, conf
import datetime
import json
import sys
import platform

MUSICPORT_IP = "10.0.0.45"
CAPTURE_FILE = "musicport_capture.pcap"
LOG_FILE = r"C:\Users\Corey\PycharmProjects\musicport\tmp\sniff-output.txt"

class PacketAnalyzer:
    def __init__(self):
        self.packet_count = 0
        self.connections = {}
        self.log_data = []

    def packet_callback(self, packet):
        """Process each captured packet"""
        self.packet_count += 1

        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst

            # Only process packets to/from MusicPort
            if src_ip != MUSICPORT_IP and dst_ip != MUSICPORT_IP:
                return

            timestamp = datetime.datetime.now().isoformat()
            direction = "TO" if dst_ip == MUSICPORT_IP else "FROM"

            log_entry = {
                'timestamp': timestamp,
                'packet_num': self.packet_count,
                'direction': direction,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'protocol': packet[IP].proto
            }

            # TCP packet
            if TCP in packet:
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                log_entry['protocol_name'] = 'TCP'
                log_entry['src_port'] = src_port
                log_entry['dst_port'] = dst_port
                log_entry['flags'] = packet[TCP].flags

                # Extract payload
                if Raw in packet:
                    payload = bytes(packet[Raw].load)
                    log_entry['payload_length'] = len(payload)
                    log_entry['payload_hex'] = payload.hex()
                    log_entry['payload_ascii'] = payload.decode('ascii', errors='ignore')

                    # Print interesting packets
                    print(f"\n[{timestamp}] Packet #{self.packet_count}")
                    print(f"  Direction: {direction} MusicPort")
                    print(f"  {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
                    print(f"  Payload ({len(payload)} bytes):")
                    print(f"    HEX: {payload.hex()}")
                    print(f"    ASCII: {payload.decode('ascii', errors='ignore')}")

            # UDP packet
            elif UDP in packet:
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
                log_entry['protocol_name'] = 'UDP'
                log_entry['src_port'] = src_port
                log_entry['dst_port'] = dst_port

                # Extract payload
                if Raw in packet:
                    payload = bytes(packet[Raw].load)
                    log_entry['payload_length'] = len(payload)
                    log_entry['payload_hex'] = payload.hex()
                    log_entry['payload_ascii'] = payload.decode('ascii', errors='ignore')

                    print(f"\n[{timestamp}] Packet #{self.packet_count}")
                    print(f"  Direction: {direction} MusicPort")
                    print(f"  {src_ip}:{src_port} -> {dst_ip}:{dst_port} (UDP)")
                    print(f"  Payload ({len(payload)} bytes):")
                    print(f"    HEX: {payload.hex()}")
                    print(f"    ASCII: {payload.decode('ascii', errors='ignore')}")

            self.log_data.append(log_entry)

            # Save log every 10 packets
            if self.packet_count % 10 == 0:
                self.save_log()

    def save_log(self):
        """Save captured data to JSON log"""
        import os
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'w') as f:
            json.dump(self.log_data, f, indent=2)

    def print_summary(self):
        """Print capture summary"""
        print("\n" + "=" * 60)
        print(f"Capture Summary: {self.packet_count} packets captured")
        print(f"Log saved to: {LOG_FILE}")
        print("=" * 60)

def main():
    print("=" * 60)
    print("Nuvo MusicPort Packet Sniffer")
    print("=" * 60)
    print(f"Monitoring traffic to/from: {MUSICPORT_IP}")
    print("Press Ctrl+C to stop capture\n")

    # Configure scapy for Windows without Npcap (Layer 3 only)
    if platform.system() == 'Windows':
        print("[*] Windows detected - using Layer 3 socket mode")
        print("[*] Note: This mode works without Npcap but may miss some packets")
        print("[*] For best results, install Npcap from https://npcap.com/\n")
        conf.L3socket = conf.L3socket  # Use Layer 3 socket

    analyzer = PacketAnalyzer()

    try:
        # Start sniffing
        # filter: capture only packets to/from MusicPort IP
        filter_str = f"host {MUSICPORT_IP}"

        print(f"Starting packet capture (filter: {filter_str})...")
        print("Use your iPhone app now to generate traffic!\n")

        # Use Layer 3 socket on Windows
        if platform.system() == 'Windows':
            sniff(
                filter=filter_str,
                prn=analyzer.packet_callback,
                store=True,
                L3socket=conf.L3socket
            )
        else:
            sniff(
                filter=filter_str,
                prn=analyzer.packet_callback,
                store=True
            )

    except KeyboardInterrupt:
        print("\n\nStopping capture...")
        analyzer.save_log()
        analyzer.print_summary()

    except PermissionError:
        print("\n[!] Error: Permission denied. Try running as Administrator.")
        sys.exit(1)

if __name__ == "__main__":
    main()
