# Home Assistant Integration Guide

## Installation

### Method 1: HACS (Recommended)

1. Install [HACS](https://hacs.xyz/) if not already installed
2. Add this repository as a custom repository in HACS
3. Search for "NuVo MusicPort" and install
4. Restart Home Assistant

### Method 2: Manual

Copy the `custom_components/nuvo_musicport` folder to your Home Assistant `config/custom_components/` directory:

```bash
cp -r homeassistant/custom_components/nuvo_musicport \
    /config/custom_components/
```

Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "NuVo MusicPort"
4. Enter your API server details:
   - **API Host**: IP address of your API server (e.g., `10.0.0.45`)
   - **API Port**: API port (default: `8000`)
5. Click **Submit**

The integration will auto-discover all zones and create entities.

## Entities Created

### Media Players
One media player entity per zone:
- `media_player.master_bedroom`
- `media_player.master_bath`
- `media_player.living_room`
- `media_player.hall_bath`
- `media_player.kitchen`
- `media_player.guest_bedroom`

### Switches
- `switch.party_mode` - Party mode control

## Usage

### In Dashboards

Add media player cards to your dashboard:

```yaml
type: media-control
entity: media_player.living_room
```

Or create a custom card with all zones:

```yaml
type: entities
title: NuVo Audio System
entities:
  - media_player.master_bedroom
  - media_player.living_room
  - media_player.kitchen
  - switch.party_mode
```

### In Automations

Turn on zone when motion detected:

```yaml
automation:
  - alias: "Living Room Audio on Motion"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_motion
        to: "on"
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.living_room
      - service: media_player.volume_set
        target:
          entity_id: media_player.living_room
        data:
          volume_level: 0.5
```

Start party mode at specific time:

```yaml
automation:
  - alias: "Party Mode at 7 PM"
    trigger:
      - platform: time
        at: "19:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.party_mode
```

### Services

All standard media player services are supported:

- `media_player.turn_on`
- `media_player.turn_off`
- `media_player.volume_set`
- `media_player.volume_up`
- `media_player.volume_down`
- `media_player.volume_mute`
- `media_player.select_source`

## Voice Control

Use with Home Assistant voice assistants:

- "Turn on living room audio"
- "Set kitchen volume to 50 percent"
- "Play music server A in master bedroom"

## Requirements

- Home Assistant 2023.1 or later
- NuVo MusicPort API server running and accessible
- Network connectivity between Home Assistant and API server

## Troubleshooting

### Integration not found
- Ensure custom_components folder is in the correct location
- Restart Home Assistant after copying files

### Cannot connect
- Check API server is running: `curl http://YOUR_IP:8000/health`
- Verify network connectivity
- Check firewall rules

### Entities not updating
- Check API server logs for errors
- Integration polls every 30 seconds
- Try reloading the integration

## Advanced Configuration

### Customize entity names

In `configuration.yaml`:

```yaml
homeassistant:
  customize:
    media_player.master_bedroom:
      friendly_name: "Master Suite Audio"
      icon: mdi:speaker
```
