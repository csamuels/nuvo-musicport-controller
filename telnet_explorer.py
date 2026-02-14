#!/usr/bin/env python3
"""
Nuvo MusicPort Telnet Explorer
Interactive telnet client to explore and log commands
"""

import telnetlib
import sys
import time
import os
from datetime import datetime

MUSICPORT_IP = "10.0.0.45"
TELNET_PORT = 23
LOG_FILE = r"C:\Users\Corey\PycharmProjects\musicport\tmp\telnet-commands.txt"

class TelnetExplorer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.tn = None
        self.log_data = []

    def connect(self):
        """Connect to telnet server"""
        try:
            print(f"[*] Connecting to {self.host}:{self.port}...")
            self.tn = telnetlib.Telnet(self.host, self.port, timeout=5)

            # Read welcome banner
            time.sleep(0.5)
            banner = self.tn.read_very_eager().decode('ascii', errors='ignore')
            print("\n" + "="*60)
            print("BANNER:")
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
            timestamp = datetime.now().isoformat()

            # Send command
            self.tn.write(command.encode('ascii') + b'\n')

            # Wait for response
            time.sleep(0.3)
            response = self.tn.read_very_eager().decode('ascii', errors='ignore')

            # Log command and response
            log_entry = {
                'timestamp': timestamp,
                'command': command,
                'response': response
            }
            self.log_data.append(log_entry)

            # Print to terminal
            print(f"\n> {command}")
            print(response)

            # Save log
            self.save_log()

            return response

        except Exception as e:
            print(f"[!] Error sending command: {e}")
            return None

    def save_log(self):
        """Save command log"""
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            with open(LOG_FILE, 'w') as f:
                f.write("TELNET COMMAND LOG\n")
                f.write("="*60 + "\n\n")
                for entry in self.log_data:
                    f.write(f"Time: {entry['timestamp']}\n")
                    f.write(f"Command: {entry['command']}\n")
                    f.write(f"Response:\n{entry['response']}\n")
                    f.write("-"*60 + "\n\n")
        except Exception as e:
            print(f"[!] Warning: Could not save log: {e}")

    def interactive_mode(self):
        """Interactive command shell"""
        print("\n" + "="*60)
        print("Interactive Telnet Mode")
        print("="*60)
        print("Type commands and press Enter")
        print("Special commands:")
        print("  ?           - Get help from device")
        print("  help        - Get help from device")
        print("  quit        - Exit this tool")
        print("  discover    - Auto-discover common commands")
        print("="*60 + "\n")

        while True:
            try:
                command = input("MusicPort> ").strip()

                if not command:
                    continue

                if command.lower() == 'quit':
                    break

                if command.lower() == 'discover':
                    self.discover_commands()
                    continue

                self.send_command(command)

            except KeyboardInterrupt:
                print("\n")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"[!] Error: {e}")

    def discover_commands(self):
        """Try common commands to discover functionality"""
        print("\n[*] Auto-discovering commands...\n")

        common_commands = [
            "?",
            "help",
            "help volume",
            "help zone",
            "help source",
            "status",
            "version",
            "info",
            "get",
            "set",
            "list",
            "zones",
            "sources",
            "volume",
        ]

        for cmd in common_commands:
            print(f"\nTrying: {cmd}")
            self.send_command(cmd)
            time.sleep(0.5)

    def close(self):
        """Close connection"""
        if self.tn:
            self.tn.close()
        print(f"\n[*] Connection closed")
        print(f"[*] Commands saved to: {LOG_FILE}")

def quick_commands():
    """Test some quick commands automatically"""
    explorer = TelnetExplorer(MUSICPORT_IP, TELNET_PORT)

    if not explorer.connect():
        return

    print("[*] Getting help information...")
    explorer.send_command("?")
    time.sleep(1)

    print("\n[*] Trying 'help'...")
    explorer.send_command("help")
    time.sleep(1)

    explorer.close()

def main():
    print("="*60)
    print("Nuvo MusicPort Telnet Explorer")
    print("="*60)
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_commands()
    else:
        explorer = TelnetExplorer(MUSICPORT_IP, TELNET_PORT)

        if explorer.connect():
            # Auto-run help command first
            print("[*] Getting available commands...\n")
            explorer.send_command("?")
            time.sleep(0.5)

            # Enter interactive mode
            explorer.interactive_mode()
            explorer.close()

if __name__ == "__main__":
    main()
