#!/usr/bin/env python3
"""
Media Control Server (MCS) Interactive Client
Port 5004 - Main control interface
"""

import telnetlib
import sys
import time
import os

MUSICPORT_IP = "10.0.0.45"
MCS_PORT = 5004
LOG_FILE = r"C:\Users\Corey\PycharmProjects\musicport\tmp\mcs-commands.txt"

class MCSClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.tn = None
        self.log_data = []

    def connect(self):
        """Connect to MCS server"""
        try:
            print(f"[*] Connecting to {self.host}:{self.port}...")
            self.tn = telnetlib.Telnet(self.host, self.port, timeout=5)

            # Read welcome banner
            time.sleep(0.5)
            banner = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print("\n" + "="*60)
            print("MEDIA CONTROL SERVER CONNECTED")
            print("="*60)
            print(banner)
            print("="*60 + "\n")

            return True
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False

    def send_command(self, command):
        """Send command and get response"""
        try:
            timestamp = time.time()

            # Send command
            self.tn.write(command.encode('ascii') + b'\r\n')

            # Wait for response
            time.sleep(0.3)
            response = self.tn.read_very_eager().decode('ascii', errors='ignore')

            # Log
            self.log_data.append({
                'timestamp': timestamp,
                'command': command,
                'response': response
            })

            # Print
            print(response)

            # Save log
            self.save_log()

            return response

        except Exception as e:
            print(f"[!] Error: {e}")
            return None

    def save_log(self):
        """Save command log"""
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'w') as f:
                f.write("MCS COMMAND LOG\n")
                f.write("="*60 + "\n\n")
                for entry in self.log_data:
                    f.write(f"Time: {entry['timestamp']}\n")
                    f.write(f"Command: {entry['command']}\n")
                    f.write(f"Response:\n{entry['response']}\n")
                    f.write("-"*60 + "\n\n")
        except:
            pass

    def interactive_mode(self):
        """Interactive command shell"""
        print("\n" + "="*60)
        print("Interactive MCS Mode")
        print("="*60)
        print("Type commands and press Enter")
        print("Common commands:")
        print("  GetStatus      - Get current status")
        print("  Mute True      - Mute audio")
        print("  Play           - Play")
        print("  Pause          - Pause")
        print("  help <cmd>     - Get help on command")
        print("  ?              - List all commands")
        print("  quit           - Exit")
        print("="*60 + "\n")

        while True:
            try:
                command = input("MCS> ").strip()

                if not command:
                    continue

                if command.lower() == 'quit':
                    break

                self.send_command(command)

            except KeyboardInterrupt:
                print("\n")
                break
            except EOFError:
                break

    def close(self):
        """Close connection"""
        if self.tn:
            self.tn.close()
        print(f"\n[*] Connection closed")
        print(f"[*] Log saved to: {LOG_FILE}")

def main():
    print("="*60)
    print("Media Control Server (MCS) Client")
    print("="*60)
    print()

    client = MCSClient(MUSICPORT_IP, MCS_PORT)

    if client.connect():
        # Try GetStatus first
        print("[*] Getting system status...\n")
        client.send_command("GetStatus")
        time.sleep(0.5)

        # Enter interactive mode
        client.interactive_mode()
        client.close()

if __name__ == "__main__":
    main()
