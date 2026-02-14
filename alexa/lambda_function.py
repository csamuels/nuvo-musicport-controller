"""
AWS Lambda function for NuVo MusicPort Alexa skill.

Deploy to AWS Lambda and connect to your Alexa skill.
"""

import json
import os
from typing import Dict, Any
import urllib.request
import urllib.error

# Configuration - set these as Lambda environment variables
API_URL = os.environ.get('NUVO_API_URL', 'http://your-api-server:8000')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for Alexa requests."""

    request_type = event['request']['type']

    if request_type == 'LaunchRequest':
        return handle_launch()
    elif request_type == 'IntentRequest':
        intent_name = event['request']['intent']['name']
        return handle_intent(intent_name, event['request']['intent'])
    elif request_type == 'SessionEndedRequest':
        return handle_session_end()

    return error_response("Unknown request type")


def handle_launch() -> Dict[str, Any]:
    """Handle skill launch."""
    speech = ("Welcome to NuVo MusicPort control. "
              "You can say things like, turn on the living room, "
              "or set master bedroom volume to 50.")
    return response(speech, should_end_session=False)


def handle_intent(intent_name: str, intent: Dict[str, Any]) -> Dict[str, Any]:
    """Route intent to appropriate handler."""

    handlers = {
        'PowerOnIntent': handle_power_on,
        'PowerOffIntent': handle_power_off,
        'SetVolumeIntent': handle_set_volume,
        'VolumeUpIntent': handle_volume_up,
        'VolumeDownIntent': handle_volume_down,
        'MuteIntent': handle_mute,
        'UnmuteIntent': handle_unmute,
        'SetSourceIntent': handle_set_source,
        'PartyModeIntent': handle_party_mode,
        'AllOffIntent': handle_all_off,
        'AMAZON.HelpIntent': handle_help,
        'AMAZON.StopIntent': handle_stop,
        'AMAZON.CancelIntent': handle_stop,
    }

    handler = handlers.get(intent_name)
    if handler:
        return handler(intent)

    return error_response("I don't know how to do that.")


# Intent Handlers

def handle_power_on(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Turn zone on."""
    zone_name = get_slot_value(intent, 'ZoneName')
    if not zone_name:
        return error_response("Which zone would you like to turn on?")

    zone_number = zone_name_to_number(zone_name)
    if not zone_number:
        return error_response(f"I couldn't find a zone named {zone_name}")

    try:
        api_request('POST', f'/api/zones/{zone_number}/power/on')
        return response(f"{zone_name} is now on")
    except Exception as e:
        return error_response(f"Sorry, I couldn't turn on {zone_name}")


def handle_power_off(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Turn zone off."""
    zone_name = get_slot_value(intent, 'ZoneName')
    if not zone_name:
        return error_response("Which zone would you like to turn off?")

    zone_number = zone_name_to_number(zone_name)
    if not zone_number:
        return error_response(f"I couldn't find a zone named {zone_name}")

    try:
        api_request('POST', f'/api/zones/{zone_number}/power/off')
        return response(f"{zone_name} is now off")
    except Exception as e:
        return error_response(f"Sorry, I couldn't turn off {zone_name}")


def handle_set_volume(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Set zone volume to specific level."""
    zone_name = get_slot_value(intent, 'ZoneName')
    volume = get_slot_value(intent, 'VolumeLevel')

    if not zone_name:
        return error_response("Which zone's volume would you like to set?")
    if not volume:
        return error_response("What volume level?")

    try:
        volume_int = int(volume)
        if not 0 <= volume_int <= 79:
            return error_response("Volume must be between 0 and 79")
    except ValueError:
        return error_response("I didn't understand that volume level")

    zone_number = zone_name_to_number(zone_name)
    if not zone_number:
        return error_response(f"I couldn't find a zone named {zone_name}")

    try:
        api_request('POST', f'/api/zones/{zone_number}/volume',
                   {'volume': volume_int})
        return response(f"Set {zone_name} volume to {volume_int}")
    except Exception as e:
        return error_response(f"Sorry, I couldn't set the volume")


def handle_volume_up(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Increase zone volume."""
    zone_name = get_slot_value(intent, 'ZoneName')
    if not zone_name:
        return error_response("Which zone's volume would you like to increase?")

    zone_number = zone_name_to_number(zone_name)
    if not zone_number:
        return error_response(f"I couldn't find a zone named {zone_name}")

    try:
        # Get current volume
        zone = api_request('GET', f'/api/zones/{zone_number}')
        new_volume = min(zone['volume'] + 5, 79)

        api_request('POST', f'/api/zones/{zone_number}/volume',
                   {'volume': new_volume})
        return response(f"Increased {zone_name} volume")
    except Exception as e:
        return error_response("Sorry, I couldn't change the volume")


def handle_volume_down(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Decrease zone volume."""
    zone_name = get_slot_value(intent, 'ZoneName')
    if not zone_name:
        return error_response("Which zone's volume would you like to decrease?")

    zone_number = zone_name_to_number(zone_name)
    if not zone_number:
        return error_response(f"I couldn't find a zone named {zone_name}")

    try:
        zone = api_request('GET', f'/api/zones/{zone_number}')
        new_volume = max(zone['volume'] - 5, 0)

        api_request('POST', f'/api/zones/{zone_number}/volume',
                   {'volume': new_volume})
        return response(f"Decreased {zone_name} volume")
    except Exception as e:
        return error_response("Sorry, I couldn't change the volume")


def handle_mute(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Mute zone."""
    zone_name = get_slot_value(intent, 'ZoneName')
    if not zone_name:
        return error_response("Which zone would you like to mute?")

    zone_number = zone_name_to_number(zone_name)
    if not zone_number:
        return error_response(f"I couldn't find a zone named {zone_name}")

    try:
        api_request('POST', f'/api/zones/{zone_number}/mute')
        return response(f"Muted {zone_name}")
    except Exception as e:
        return error_response("Sorry, I couldn't mute that zone")


def handle_unmute(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Unmute zone."""
    return handle_mute(intent)  # Toggle mute


def handle_set_source(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Change zone source."""
    zone_name = get_slot_value(intent, 'ZoneName')
    source_name = get_slot_value(intent, 'SourceName')

    if not zone_name or not source_name:
        return error_response("Which zone and source?")

    zone_number = zone_name_to_number(zone_name)
    if not zone_number:
        return error_response(f"I couldn't find a zone named {zone_name}")

    try:
        sources = api_request('GET', '/api/sources')
        source = next((s for s in sources
                      if source_name.lower() in s['name'].lower()), None)

        if not source:
            return error_response(f"I couldn't find a source named {source_name}")

        api_request('POST', f'/api/zones/{zone_number}/source',
                   {'source_guid': source['guid']})
        return response(f"Changed {zone_name} to {source['name']}")
    except Exception as e:
        return error_response("Sorry, I couldn't change the source")


def handle_party_mode(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Toggle party mode."""
    try:
        api_request('POST', '/api/control/partymode')
        return response("Party mode toggled")
    except Exception as e:
        return error_response("Sorry, I couldn't toggle party mode")


def handle_all_off(intent: Dict[str, Any]) -> Dict[str, Any]:
    """Turn all zones off."""
    try:
        api_request('POST', '/api/control/alloff')
        return response("All zones are now off")
    except Exception as e:
        return error_response("Sorry, I couldn't turn off all zones")


def handle_help() -> Dict[str, Any]:
    """Provide help."""
    speech = ("You can control your NuVo MusicPort by saying things like: "
              "turn on the living room, "
              "set master bedroom volume to 50, "
              "volume up in the kitchen, "
              "or start party mode.")
    return response(speech, should_end_session=False)


def handle_stop() -> Dict[str, Any]:
    """Handle stop/cancel."""
    return response("Goodbye", should_end_session=True)


def handle_session_end() -> Dict[str, Any]:
    """Handle session end."""
    return response("", should_end_session=True)


# Utility Functions

def zone_name_to_number(zone_name: str) -> int:
    """Convert zone name to number."""
    zone_map = {
        'master bedroom': 1,
        'master bath': 2,
        'living room': 3,
        'hall bath': 4,
        'kitchen': 5,
        'guest bedroom': 6,
    }
    return zone_map.get(zone_name.lower(), 0)


def get_slot_value(intent: Dict[str, Any], slot_name: str) -> str:
    """Extract slot value from intent."""
    slots = intent.get('slots', {})
    slot = slots.get(slot_name, {})
    return slot.get('value', '')


def api_request(method: str, endpoint: str, data: Dict = None) -> Any:
    """Make request to API server."""
    url = f"{API_URL}{endpoint}"

    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')

    if data:
        req.data = json.dumps(data).encode('utf-8')

    with urllib.request.urlopen(req, timeout=5) as response:
        if method == 'GET' or response.status == 200:
            return json.loads(response.read().decode('utf-8'))

    raise Exception(f"API request failed: {method} {endpoint}")


def response(speech: str, should_end_session: bool = True) -> Dict[str, Any]:
    """Build Alexa response."""
    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech
            },
            'shouldEndSession': should_end_session
        }
    }


def error_response(message: str) -> Dict[str, Any]:
    """Build error response."""
    return response(f"Sorry, {message}", should_end_session=True)
