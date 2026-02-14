#!/usr/bin/env python3
"""
Nuvo MusicPort TCP Proxy Sniffer
Acts as a man-in-the-middle proxy to capture traffic
No special drivers required - works on all platforms!

USAGE:
1. Run this script on your computer
2. Configure your iPhone app to connect to YOUR_COMPUTER_IP instead of 10.0.0.45
3. This proxy will forward traffic to the real MusicPort and log everything
"""

import socket
import threading
import datetime
import json
import sys

MUSICPORT_IP = "10.0.0.45"
PROXY_PORT = 8000  # Port to listen on (change this based on scanner results)
LOG_FILE = r"C:\Users\Corey\PycharmProjects\musicport\tmp\sniff-output.txt"

class ProxyConnection:
    def __init__(self, client_socket, client_addr, target_ip, target_port):
        self.client_socket = client_socket
        self.client_addr = client_addr
        self.target_ip = target_ip
        self.target_port = target_port
        self.log_data = []
        self.packet_count = 0

    def log_packet(self, direction, data):
        """Log captured packet"""
        self.packet_count += 1
        timestamp = datetime.datetime.now().isoformat()

        log_entry = {
            'timestamp': timestamp,
            'packet_num': self.packet_count,
            'direction': direction,
            'length': len(data),
            'hex': data.hex(),
            'ascii': data.decode('ascii', errors='ignore')
        }

        self.log_data.append(log_entry)

        # Print to console
        print(f"\n[{timestamp}] Packet #{self.packet_count}")
        print(f"  Direction: {direction}")
        print(f"  Length: {len(data)} bytes")
        print(f"  HEX: {data.hex()}")
        print(f"  ASCII: {data.decode('ascii', errors='ignore')[:100]}")

        # Save log
        self.save_log()

    def save_log(self):
        """Save log to file"""
        try:
            import os
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'w') as f:
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

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("Nuvo MusicPort TCP Proxy Sniffer")
        print("=" * 60)
        print("\nUsage: python proxy_sniffer.py <target_port> [listen_port]")
        print("\nExample:")
        print("  python proxy_sniffer.py 5004        # Listen on 8000, forward to 5004")
        print("  python proxy_sniffer.py 5006 5006   # Listen on 5006, forward to 5006")
        print("\nThis will:")
        print(f"  1. Listen on YOUR_COMPUTER:<listen_port> (default 8000)")
        print(f"  2. Forward to {MUSICPORT_IP}:<target_port>")
        print("  3. Log all traffic to proxy_capture.log")
        print("\nRun scanner.py first to find which port to use!")
        sys.exit(1)

    target_port = int(sys.argv[1])
    listen_port = int(sys.argv[2]) if len(sys.argv) > 2 else PROXY_PORT
    local_ip = get_local_ip()

    print("=" * 60)
    print("Nuvo MusicPort TCP Proxy Sniffer")
    print("=" * 60)
    print(f"\n[*] Listening on: {local_ip}:{listen_port}")
    print(f"[*] Forwarding to: {MUSICPORT_IP}:{target_port}")
    print(f"[*] Logging to: {LOG_FILE}")
    print("\n" + "=" * 60)
    print("IMPORTANT SETUP:")
    print("=" * 60)
    print(f"Configure your iPhone app to connect to:")
    print(f"  IP: {local_ip}")
    print(f"  Port: {listen_port}")
    print("\nProxy will forward to:")
    print(f"  IP: {MUSICPORT_IP}")
    print(f"  Port: {target_port}")
    print("=" * 60)
    print("\nWaiting for connections... (Press Ctrl+C to stop)\n")

    # Create listening socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(('0.0.0.0', listen_port))
        server_socket.listen(5)

        while True:
            client_socket, client_addr = server_socket.accept()

            # Handle connection in new thread
            proxy = ProxyConnection(
                client_socket,
                client_addr,
                MUSICPORT_IP,
                target_port
            )

            proxy_thread = threading.Thread(target=proxy.start)
            proxy_thread.daemon = True
            proxy_thread.start()

    except KeyboardInterrupt:
        print("\n\n[*] Shutting down proxy...")
        server_socket.close()
        print(f"[*] Capture saved to {LOG_FILE}")

    except Exception as e:
        print(f"\n[!] Error: {e}")
        server_socket.close()

if __name__ == "__main__":
    main()
