#!/usr/bin/env python3
"""
Nuvo MusicPort TCP Proxy Sniffer
Acts as a man-in-the-middle proxy to capture traffic
No special drivers required - works on all platforms!

USAGE:
1. Run this script on your computer
2. Configure your iPhone app to connect to YOUR_COMPUTER_IP instead of 10.0.0.45
3. This proxy will forward traffic to the real MusicPort and log everything

MULTI-PORT SUPPORT:
python proxy_sniffer.py 5006 5004 --log-dir ./logs
- Listens on ports 5006 and 5004
- Forwards each port to the same port on target device
- Creates separate log files for each port in ./logs directory
"""

import socket
import threading
import datetime
import json
import sys
import os
import argparse

MUSICPORT_IP = "10.0.0.45"

class ProxyConnection:
    def __init__(self, client_socket, client_addr, target_ip, target_port, log_file, listen_port):
        self.client_socket = client_socket
        self.client_addr = client_addr
        self.target_ip = target_ip
        self.target_port = target_port
        self.listen_port = listen_port
        self.log_file = log_file
        self.log_data = []
        self.packet_count = 0

    def log_packet(self, direction, data):
        """Log captured packet"""
        self.packet_count += 1
        timestamp = datetime.datetime.now().isoformat()

        log_entry = {
            'timestamp': timestamp,
            'port': self.target_port,
            'listen_port': self.listen_port,
            'packet_num': self.packet_count,
            'direction': direction,
            'length': len(data),
            'hex': data.hex(),
            'ascii': data.decode('ascii', errors='ignore')
        }

        self.log_data.append(log_entry)

        # Print to console with port info
        print(f"\n[{timestamp}] Port {self.target_port} - Packet #{self.packet_count}")
        print(f"  Direction: {direction}")
        print(f"  Length: {len(data)} bytes")
        print(f"  HEX: {data.hex()}")
        print(f"  ASCII: {data.decode('ascii', errors='ignore')[:100]}")

        # Save log
        self.save_log()

    def save_log(self):
        """Save log to file"""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'w') as f:
                json.dump(self.log_data, f, indent=2)
        except Exception as e:
            print(f"[!] Warning: Could not save log: {e}")

    def handle_client_to_server(self, target_socket):
        """Forward data from client (iPhone) to server (MusicPort)"""
        try:
            while True:
                data = self.client_socket.recv(4096)
                if not data:
                    break

                self.log_packet("CLIENT -> SERVER", data)
                target_socket.send(data)

        except Exception as e:
            print(f"[!] Client->Server error: {e}")
        finally:
            target_socket.close()
            self.client_socket.close()

    def handle_server_to_client(self, target_socket):
        """Forward data from server (MusicPort) to client (iPhone)"""
        try:
            while True:
                data = target_socket.recv(4096)
                if not data:
                    break

                self.log_packet("SERVER -> CLIENT", data)
                self.client_socket.send(data)

        except Exception as e:
            print(f"[!] Server->Client error: {e}")
        finally:
            target_socket.close()
            self.client_socket.close()

    def start(self):
        """Start proxying"""
        try:
            # Connect to target (MusicPort)
            print(f"\n[*] New connection from {self.client_addr}")
            print(f"[*] Connecting to {self.target_ip}:{self.target_port}...")

            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((self.target_ip, self.target_port))

            print(f"[*] Connected! Proxying traffic...")

            # Start forwarding in both directions
            client_to_server = threading.Thread(
                target=self.handle_client_to_server,
                args=(target_socket,)
            )
            server_to_client = threading.Thread(
                target=self.handle_server_to_client,
                args=(target_socket,)
            )

            client_to_server.daemon = True
            server_to_client.daemon = True

            client_to_server.start()
            server_to_client.start()

            client_to_server.join()
            server_to_client.join()

        except Exception as e:
            print(f"[!] Proxy error: {e}")
            self.client_socket.close()

def get_local_ip():
    """Get local IP address"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "YOUR_COMPUTER_IP"

def start_proxy_listener(port, target_ip, log_file, local_ip):
    """Start a proxy listener for a specific port"""
    print(f"[*] Starting listener on port {port} -> {target_ip}:{port}")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)

        while True:
            client_socket, client_addr = server_socket.accept()

            # Handle connection in new thread
            proxy = ProxyConnection(
                client_socket,
                client_addr,
                target_ip,
                port,
                log_file,
                port
            )

            proxy_thread = threading.Thread(target=proxy.start)
            proxy_thread.daemon = True
            proxy_thread.start()

    except Exception as e:
        print(f"\n[!] Error on port {port}: {e}")
        server_socket.close()

def main():
    parser = argparse.ArgumentParser(
        description='Nuvo MusicPort Multi-Port TCP Proxy Sniffer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python proxy_sniffer.py 5004                    # Single port (listen on 5004, forward to 5004)
  python proxy_sniffer.py 5006 5004               # Multiple ports
  python proxy_sniffer.py 5006 5004 --log-dir ./logs  # Custom log directory
  python proxy_sniffer.py 5006 5004 --target 10.0.0.45  # Custom target IP

The proxy will:
  - Listen on each specified port
  - Forward to the same port number on the target device
  - Create separate log files for each port (e.g., port-5006.json, port-5004.json)
        """
    )

    parser.add_argument('ports', nargs='+', type=int,
                        help='Port(s) to listen on and forward to')
    parser.add_argument('--target', default=MUSICPORT_IP,
                        help=f'Target device IP (default: {MUSICPORT_IP})')
    parser.add_argument('--log-dir', default='./logs',
                        help='Directory for log files (default: ./logs)')

    args = parser.parse_args()

    local_ip = get_local_ip()
    target_ip = args.target
    log_dir = args.log_dir
    ports = args.ports

    # Create log directory
    os.makedirs(log_dir, exist_ok=True)

    print("=" * 70)
    print("Nuvo MusicPort Multi-Port TCP Proxy Sniffer")
    print("=" * 70)
    print(f"\n[*] Local IP: {local_ip}")
    print(f"[*] Target Device: {target_ip}")
    print(f"[*] Log Directory: {os.path.abspath(log_dir)}")
    print(f"\n[*] Ports to proxy:")
    for port in ports:
        log_file = os.path.join(log_dir, f"port-{port}.json")
        print(f"    Port {port} -> {target_ip}:{port} (log: {log_file})")

    print("\n" + "=" * 70)
    print("SETUP INSTRUCTIONS:")
    print("=" * 70)
    print(f"Configure your app to connect to: {local_ip}")
    print(f"Using ports: {', '.join(map(str, ports))}")
    print("=" * 70)
    print("\nWaiting for connections... (Press Ctrl+C to stop)\n")

    # Start a listener thread for each port
    listener_threads = []
    for port in ports:
        log_file = os.path.join(log_dir, f"port-{port}.json")
        thread = threading.Thread(
            target=start_proxy_listener,
            args=(port, target_ip, log_file, local_ip),
            daemon=True
        )
        thread.start()
        listener_threads.append(thread)

    try:
        # Keep main thread alive
        for thread in listener_threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n\n[*] Shutting down proxy...")
        print(f"[*] Captures saved to {os.path.abspath(log_dir)}")
        print(f"    Files: {', '.join([f'port-{p}.json' for p in ports])}")

if __name__ == "__main__":
    main()
