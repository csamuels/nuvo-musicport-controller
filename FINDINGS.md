# Nuvo MusicPort Reverse Engineering - Findings

## Device Information
- **IP Address**: 10.0.0.45
- **Manufacturer**: Autonomic Controls (NuVo Technologies)
- **Model**: MusicPort MPS4
- **Software Version**: 5.0.15934.4

## Open Ports Discovered

### Port 23 - Telnet Configuration Interface
- **Purpose**: System configuration and settings
- **Access**: Telnet (no authentication required)
- **Commands**: Get/Set system settings, browse sources, network config
- **Usage**: `python telnet_explorer.py`

**Key Commands:**
- `Get` - View all system settings
- `Set <category> <name> <value>` - Change settings
- `BrowseSources` - List audio sources
- `Reboot` - Reboot the system

### Port 80 - HTTP Web Interface
- **Purpose**: Flash-based web UI
- **URL**: http://10.0.0.45/MusicPort/
- **Note**: Old Flash interface, not useful for automation

### Port 5004 - Media Control Server (MCS)
- **Purpose**: Control music playback, sources, playlists
- **Access**: Telnet/TCP
- **Usage**: `python mcs_client.py`

**Key Commands:**
- `GetStatus` - Get complete playback status
- `Play` / `Pause` - Transport controls
- `Mute <True|False|Toggle>` - Mute control
- `Volume` - Volume control (supports direct and up/down)
- `BrowseInstances` - List sources (Music_Server_A, B, C, D)
- `SetInstance <name>` - Select source

**Current Status** (from GetStatus):
```
Volume=50
Mute=False
PlayState=Paused
MRADServer=10.0.0.45:5006
MRADSource=1
```

### Port 5006 - MRAD (Multi-Room Audio Distribution) Server
- **Purpose**: Zone control (THIS IS WHAT THE IPHONE APP USES!)
- **Protocol**: Likely NuVo proprietary protocol over TCP
- **Status**: Commands not yet decoded - NEEDS PACKET CAPTURE

## Audio Sources
The MusicPort has 4 configured sources:
1. **Music_Server_A** (Source 1)
2. **Music_Server_B** (Source 2)
3. **Music_Server_C** (Source 3)
4. **Music_Server_D** (Source 4)

## Serial Control
- **COM1**: NuVo serial protocol at 9600 baud
- The MusicPort translates network commands to serial commands for NuVo zones

## Next Steps - CAPTURE IPHONE APP TRAFFIC!

Since we found that Port 5006 (MRAD) is the zone control port but haven't decoded the protocol yet, the best approach is to capture traffic from your iPhone app.

### Recommended Method: Use the Proxy Sniffer

1. **Run the proxy sniffer:**
   ```bash
   python proxy_sniffer.py 5006
   ```

2. **Configure your iPhone app:**
   - Change the MusicPort IP from `10.0.0.45` to YOUR_COMPUTER_IP
   - Keep the same port

3. **Use your iPhone app** to:
   - Change volume
   - Switch zones
   - Change sources
   - Power zones on/off
   - Mute/unmute

4. **Check the captured data:**
   - Look at terminal output (real-time)
   - Check `tmp\sniff-output.txt`

5. **Analyze the protocol:**
   - Look for patterns in the hex data
   - Identify command structures
   - Map actions to hex commands

## Alternative: Packet Capture
If you can't modify the iPhone app settings, use Wireshark:
1. Install Wireshark
2. Start capture on your network interface
3. Filter: `ip.addr == 10.0.0.45 && tcp.port == 5006`
4. Use iPhone app
5. Analyze captured TCP streams

## What We Can Already Control

### Via Port 5004 (MCS) - Music Playback:
- ✅ Play/Pause
- ✅ Mute
- ✅ Source selection
- ✅ Browse music library
- ✅ Play specific tracks/artists/albums

### Via Port 23 (Telnet) - System Config:
- ✅ View/change system settings
- ✅ Network configuration
- ✅ Source configuration

### Via Port 5006 (MRAD) - Zone Control:
- ❓ Unknown protocol - needs capture!
- This is where volume, zone power, zone source selection happens

## Example Python Code

### Connect to MCS and Control Playback
```python
import telnetlib

tn = telnetlib.Telnet('10.0.0.45', 5004)
tn.read_until(b'Type')  # Wait for banner

# Play
tn.write(b'Play\r\n')
print(tn.read_very_eager())

# Mute
tn.write(b'Mute True\r\n')
print(tn.read_very_eager())

# Get status
tn.write(b'GetStatus\r\n')
print(tn.read_very_eager())

tn.close()
```

### Change System Settings
```python
import telnetlib

tn = telnetlib.Telnet('10.0.0.45', 23)
tn.read_until(b'logged in')  # Wait for login

# Get all settings
tn.write(b'Get\r\n')
print(tn.read_very_eager())

# Change system name
tn.write(b'Set SYSTEM NAME MyMusicPort\r\n')
tn.write(b'Save\r\n')  # Save changes

tn.close()
```

## Files Created

- `scanner.py` - Port scanner
- `telnet_explorer.py` - Telnet config interface
- `mcs_client.py` - Media Control Server client (port 5004)
- `mrad_client.py` - MRAD client (port 5006) - needs protocol decoding
- `proxy_sniffer.py` - TCP proxy to capture iPhone app traffic
- `http_explorer.py` - HTTP API explorer
- `client.py` - Generic TCP/UDP client for testing

## Summary

We've successfully reverse-engineered most of the MusicPort's interfaces. The final piece is decoding the MRAD protocol on port 5006, which requires capturing traffic from the iPhone app.

**NEXT ACTION**: Run `python proxy_sniffer.py 5006` and use your iPhone app to capture zone control commands!
