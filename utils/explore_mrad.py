#!/usr/bin/env python3
"""
Explore MRAD zone control commands
"""

import telnetlib
import time
import os

MUSICPORT_IP = "10.0.0.45"
TELNET_PORT = 23

def send_command(tn, command):
    """Send command and get response"""
    print(f"\n{'='*60}")
    print(f"Command: {command}")
    print('='*60)
    tn.write(command.encode('ascii') + b'\n')
    time.sleep(0.5)
    response = tn.read_very_eager().decode('ascii', errors='ignore')
    print(response)
    return response

def main():
    print("Connecting to MusicPort...")
    tn = telnetlib.Telnet(MUSICPORT_IP, TELNET_PORT, timeout=5)

    # Read banner
    time.sleep(0.5)
    tn.read_very_eager()

    # Try to find MRAD/zone commands
    commands = [
        # Try to get MRAD-specific settings
        "Get MRAD",

        # Try various zone-related commands
        "help zone",
        "help volume",
        "help power",
        "help mute",
        "help source",

        # Try direct commands
        "zone",
        "volume",

        # Get all available categories
        "Get AUDIO",
        "Get SERIAL",

        # Try to find what other commands exist
        "help *",
    ]

    all_output = []

    for cmd in commands:
        response = send_command(tn, cmd)
        all_output.append(f"\n{'='*60}\nCommand: {cmd}\n{'='*60}\n{response}")
        time.sleep(0.3)

    # Save to file
    output_file = r"C:\Users\Corey\PycharmProjects\musicport\tmp\mrad-exploration.txt"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(all_output))

    print(f"\n\nOutput saved to: {output_file}")

    tn.close()

if __name__ == "__main__":
    main()
