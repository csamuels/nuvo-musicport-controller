# Network Discovery Guide

## Auto-Discovery of NuVo MusicPort Devices

The system includes automatic network discovery to find NuVo MusicPort devices on your local network.

## Features

- ✅ **Automatic scanning** of local network
- ✅ **Port detection** (5006 MRAD, 5004 MCS)
- ✅ **Device identification** via protocol probing
- ✅ **Hostname resolution**
- ✅ **API endpoint** for programmatic discovery
- ✅ **CLI tool** for manual discovery
- ✅ **Web UI integration** with server selector

## Usage

### Python SDK

```python
from nuvo_sdk import discover_devices, get_local_network

# Discover on local network
network = get_local_network()  # Auto-detect (e.g., "192.168.1.0/24")
devices = await discover_devices(network)

for device in devices:
    print(f"Found NuVo at {device.ip}")
    if device.device_info:
        print(f"  Info: {device.device_info}")
```

### CLI Tool

```bash
# Auto-detect local network
python -m nuvo_sdk.discovery

# Specify network
python -m nuvo_sdk.discovery 10.0.0.0/24

# Or use example script
python examples/discover_devices.py
```

**Output:**
```
NuVo MusicPort Network Discovery
==================================================
Auto-detected network: 10.0.0.0/24

Scanning 10.0.0.0/24 for NuVo devices...
This may take a minute...

[+] Found 1 device(s):

1. 10.0.0.45
   Hostname: MUSIC-PORT
   MRAD (5006): [Y]
   MCS (5004):  [Y]
   Version: 3.0.16725.0
```

### REST API

```bash
# Discover devices via API
curl http://localhost:8000/api/discovery

# Response:
[
  {
    "ip": "10.0.0.45",
    "hostname": "MUSIC-PORT",
    "mrad_port": 5006,
    "mcs_port": 5004,
    "responds_to_mrad": true,
    "responds_to_mcs": true,
    "device_info": "Autonomic Controls NuVo Bridge version 3.0.16725.0"
  }
]
```

### Web UI

The web interface automatically discovers devices on startup:

1. **Single device**: Auto-connects immediately
2. **Multiple devices**: Shows dropdown to select server
3. **No devices**: Option to enter IP manually

Server selection is saved in localStorage for future visits.

## How It Works

### 1. Network Scanning

```python
# Scans all IPs in CIDR range
network = "192.168.1.0/24"  # 254 possible hosts
devices = await discover_devices(network, max_concurrent=50)
```

### 2. Port Detection

Tests each IP for open ports:
- **Port 5006** (MRAD) - Multi-room audio control
- **Port 5004** (MCS) - Music control service

### 3. Device Identification

For devices with port 5006 open:
1. Connects to TCP socket
2. Sends wake-up command (`*\r`)
3. Reads device banner
4. Checks for "NuVo" or "Autonomic" identification
5. Extracts version information

### 4. Results

Returns list of `DiscoveredDevice` objects:
```python
@dataclass
class DiscoveredDevice:
    ip: str
    hostname: Optional[str]
    mrad_port: int
    mcs_port: int
    responds_to_mrad: bool
    responds_to_mcs: bool
    device_info: Optional[str]
```

## Performance

- **Concurrent scanning**: Up to 100 IPs simultaneously
- **Timeouts**: 0.5s for port check, 1.0s for identification
- **Typical scan time**:
  - Single device: 1-2 seconds
  - Full /24 network: 10-30 seconds

## Network Requirements

- **Same subnet**: Device and scanner must be on same network
- **No firewall blocking**: Ports 5006/5004 must be accessible
- **No port isolation**: Some switches isolate ports (disable if needed)

## Troubleshooting

### No devices found

```bash
# 1. Verify device is reachable
ping 10.0.0.45

# 2. Check ports are open
telnet 10.0.0.45 5006

# 3. Verify network range
python -m nuvo_sdk.discovery 10.0.0.0/24
```

### Slow scanning

```python
# Increase concurrent scans (use with caution)
devices = await discover_devices(network, max_concurrent=200)
```

### Behind router/firewall

If device is on different subnet, discovery won't work. Options:
1. Use VPN to same network
2. Enter IP manually
3. Use port forwarding (not recommended for security)

## Advanced Usage

### Custom Network Range

```python
# Scan specific range
devices = await discover_devices("192.168.1.100-192.168.1.150")

# Multiple subnets
import asyncio

networks = ["192.168.1.0/24", "10.0.0.0/24"]
results = await asyncio.gather(*[
    discover_devices(net) for net in networks
])
devices = [d for sublist in results for d in sublist]
```

### Filter Results

```python
devices = await discover_devices("192.168.1.0/24")

# Only devices with MRAD
mrad_devices = [d for d in devices if d.responds_to_mrad]

# Only NuVo devices (not generic TCP servers)
nuvo_devices = [d for d in devices
                if d.device_info and "NuVo" in d.device_info]
```

### Integration in Apps

```python
# Auto-discover and connect to first device
from nuvo_sdk import discover_devices, NuVoClient

devices = await discover_devices()
if devices:
    client = NuVoClient(devices[0].ip)
    await client.connect()
else:
    print("No devices found")
```

## Security Considerations

- Discovery sends minimal data (wake-up command only)
- No credentials transmitted
- Read-only operation
- Safe to run on production networks
- Does not disrupt device operation

## API Integration

Add discovery endpoint to your application:

```python
from fastapi import APIRouter
from nuvo_sdk.discovery import discover_devices

router = APIRouter()

@router.get("/discover")
async def discover():
    devices = await discover_devices()
    return [{"ip": d.ip, "name": d.hostname} for d in devices]
```

## Future Enhancements

Planned features:
- [ ] mDNS/Bonjour discovery
- [ ] UPnP discovery
- [ ] Device capability detection
- [ ] Firmware version checking
- [ ] Health monitoring
