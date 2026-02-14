# NuVo MusicPort API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### System Status

#### GET /health
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "device": "10.0.0.45"
}
```

#### GET /api/control/status
Get complete system status.

**Response:**
```json
{
    "device_type": "NV-I8G",
    "firmware_version": "2.66",
    "all_mute": false,
    "all_off": false,
    "active_zone": "Zone_1",
    "active_source": "Source_0",
    "zones": [...],
    "sources": [...]
}
```

### Zones

#### GET /api/zones
List all zones with current status.

**Response:**
```json
[
    {
        "guid": "00010000-84e4-4cf5-b0bc-ab828737ac30",
        "name": "Master Bedroom",
        "zone_id": "Zone_1",
        "zone_number": 1,
        "is_on": false,
        "volume": 79,
        "mute": false,
        "source_id": 0,
        "source_name": "",
        "party_mode": "Off",
        "max_volume": 79,
        "min_volume": 0
    }
]
```

#### GET /api/zones/{zone_number}
Get specific zone by number.

**Parameters:**
- `zone_number` (path): Zone number (1-6)

#### POST /api/zones/{zone_number}/power/on
Turn zone on.

**Response:**
```json
{
    "success": true,
    "message": "Zone 1 powered on"
}
```

#### POST /api/zones/{zone_number}/power/off
Turn zone off.

#### POST /api/zones/{zone_number}/volume
Set zone volume.

**Request Body:**
```json
{
    "volume": 50
}
```

**Response:**
```json
{
    "success": true,
    "message": "Zone 1 volume set to 50"
}
```

#### POST /api/zones/{zone_number}/mute
Toggle zone mute.

#### POST /api/zones/{zone_number}/source
Change zone source.

**Request Body:**
```json
{
    "source_guid": "00000001-84e4-4cf5-b0bc-ab828737ac30"
}
```

### Sources

#### GET /api/sources
List all available sources.

**Response:**
```json
[
    {
        "guid": "00000001-84e4-4cf5-b0bc-ab828737ac30",
        "name": "Music Server A",
        "source_id": 1,
        "is_smart": true,
        "is_network": false,
        "zone_count": 0
    }
]
```

#### GET /api/sources/{source_id}
Get specific source by ID.

### System Control

#### POST /api/control/partymode
Toggle party mode (all zones play same source).

**Response:**
```json
{
    "success": true,
    "message": "Party mode toggled"
}
```

#### POST /api/control/alloff
Turn off all zones.

## WebSocket

### WS /ws
Connect to receive real-time state change events.

**Event Format:**
```json
{
    "type": "state_change",
    "target": "Zone_1",
    "property": "Volume",
    "value": "50",
    "timestamp": 1234567890.123
}
```

**Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`${data.target} ${data.property} = ${data.value}`);
};
```

## Interactive Documentation

FastAPI provides interactive API documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Running the Server

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration

Set environment variables or create `.env` file:

```bash
NUVO_HOST=10.0.0.45
NUVO_PORT=5006
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```
