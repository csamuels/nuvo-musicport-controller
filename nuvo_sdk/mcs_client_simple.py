"""
Simplified Media Control Server (MCS) client for NuVo MusicPort.

Based on Flash app reverse engineering - uses simple request-response pattern
instead of persistent background listeners.
"""

import asyncio
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class MusicServer:
    """Represents a Music Server instance."""
    name: str
    running: bool
    supported_types: List[str]
    supports_music: bool
    supports_radio: bool
    volume: int
    mute: bool
    play_state: str
    now_playing: Optional[Dict[str, str]] = None


@dataclass
class PickListItem:
    """Represents an item in a browse menu/pick list."""
    index: int
    title: str
    guid: str
    item_type: str
    metadata: Dict[str, str]


class SimpleMCSClient:
    """
    Simplified async MCS client - matches Flash app's architecture.

    Key differences from complex version:
    - No persistent background listener task
    - Direct request-response pattern
    - Simple reconnection: close everything, wait, reconnect fresh
    - Only reads when expecting response
    """

    DEFAULT_PORT = 5004
    COMMAND_TIMEOUT = 10.0
    CONNECT_TIMEOUT = 5.0

    def __init__(self, host: Optional[str] = None, port: int = DEFAULT_PORT):
        """Initialize simple MCS client."""
        self.host = host
        self.port = port

        # Simple state
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._current_instance: Optional[str] = None

        # Single command lock to prevent concurrent commands
        self._command_lock: Optional[asyncio.Lock] = None

    def _ensure_lock(self):
        """Ensure command lock exists."""
        if self._command_lock is None:
            self._command_lock = asyncio.Lock()

    async def connect(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Connect to MCS server with initialization.

        Simple connect: open socket, send init commands, done.
        No background tasks.
        """
        if host:
            self.host = host
        if port:
            self.port = port

        if not self.host:
            raise ValueError("Host must be provided")

        print(f"[SimpleMCS] Connecting to {self.host}:{self.port}")

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.CONNECT_TIMEOUT
            )

            # Send initialization commands and consume their responses
            # NOTE: Not subscribing to events for now - they interfere with command responses
            # TODO: Add proper event handling with separate event queue
            init_commands = [
                f"SetHost {self.host}",
                "SetXMLMode Lists",
                'SetClientType "Python"',
                "SetEncoding 65001",
                "SetPickListCount 100",
                # "SubscribeEvents"  # Disabled - causes StateChanged to flood responses
            ]

            for cmd in init_commands:
                self._writer.write(f"{cmd}\r\n".encode('utf-8'))
                await self._writer.drain()

            # Wait for all init responses and consume them
            # Each command generates a response
            print("[SimpleMCS] Consuming init responses...")
            await asyncio.sleep(1.0)  # Give time for responses to arrive

            consumed = 0
            try:
                while consumed < 20:  # Max 20 lines to prevent infinite loop
                    line = await asyncio.wait_for(self._reader.readline(), timeout=0.2)
                    if not line:
                        break
                    text = line.decode('utf-8', errors='ignore').strip()
                    if text:
                        print(f"[SimpleMCS] Init response: {text}")
                        consumed += 1
            except asyncio.TimeoutError:
                pass  # No more data

            print(f"[SimpleMCS] Consumed {consumed} init response lines")

            self._connected = True
            print(f"[SimpleMCS] Connected successfully")

        except Exception as e:
            self._connected = False
            self._reader = None
            self._writer = None
            raise ConnectionError(f"Failed to connect: {e}")

    async def disconnect(self) -> None:
        """Disconnect from MCS server."""
        print("[SimpleMCS] Disconnecting")
        self._connected = False

        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except:
                pass

        self._writer = None
        self._reader = None

    async def reconnect(self) -> None:
        """
        Reconnect to MCS server after connection loss.

        Simple reconnection: disconnect cleanly, wait briefly, then connect fresh.
        """
        print("[SimpleMCS] Reconnecting...")

        # Save current instance to restore after reconnect
        saved_instance = self._current_instance

        # Disconnect cleanly
        await self.disconnect()

        # Brief wait to ensure clean socket closure
        await asyncio.sleep(0.5)

        # Reconnect
        await self.connect()

        # Restore instance if we had one
        if saved_instance:
            print(f"[SimpleMCS] Restoring instance: {saved_instance}")
            await self.set_instance(saved_instance)

        print("[SimpleMCS] Reconnection complete")

    async def _write_line(self, command: str) -> None:
        """Write a command line to the server."""
        if not self._writer:
            raise ConnectionError("Not connected")

        self._writer.write(f"{command}\r\n".encode('utf-8'))
        await self._writer.drain()

    async def _read_response(self, timeout: float = COMMAND_TIMEOUT) -> List[str]:
        """
        Read response lines until we get a completion marker or timeout.

        Filters out event notifications (StateChanged) to get actual command responses.
        """
        if not self._reader:
            raise ConnectionError("Not connected")

        lines = []
        deadline = asyncio.get_event_loop().time() + timeout

        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break

            try:
                line = await asyncio.wait_for(
                    self._reader.readline(),
                    timeout=min(0.5, remaining)
                )

                if not line:
                    break

                text = line.decode('utf-8', errors='ignore').strip()
                if text:
                    lines.append(text)

                # Check for completion markers
                if any(marker in text for marker in ['=Done', 'Ok', '</']) or len(lines) > 100:
                    break

            except asyncio.TimeoutError:
                if lines:  # Got some response, that's OK
                    break

        return lines

    async def _execute_command(self, command: str, retry_on_error: bool = True) -> List[str]:
        """
        Execute a command with simple error handling.

        Pattern: send → read response → if error, reconnect and retry once
        """
        self._ensure_lock()

        async with self._command_lock:
            try:
                # Check if connected
                if not self._connected or not self._writer:
                    print(f"[SimpleMCS] Not connected, connecting for command: {command}")
                    await self.connect()

                # Send command
                await self._write_line(command)

                # Read response immediately
                response = await self._read_response()
                return response

            except (ConnectionError, BrokenPipeError, OSError, asyncio.TimeoutError,
                    ConnectionResetError, ConnectionAbortedError, Exception) as e:
                # Catch all connection-related errors including Windows-specific ones
                # (WinError 10054: connection forcibly closed)
                print(f"[SimpleMCS] Command '{command}' failed: {type(e).__name__}: {e}")

                # Mark as disconnected
                self._connected = False

                # Retry once if allowed
                if retry_on_error:
                    print(f"[SimpleMCS] Retrying after reconnect...")

                    # Clean disconnect
                    await self.disconnect()

                    # Wait for device to settle
                    await asyncio.sleep(2.0)

                    # Reconnect fresh
                    await self.connect()

                    # Restore instance if one was set
                    if self._current_instance:
                        print(f"[SimpleMCS] Restoring instance: {self._current_instance}")
                        await self._write_line(f"SetInstance {self._current_instance}")
                        await asyncio.sleep(1.0)

                    # Retry the command (no retry this time to avoid infinite loop)
                    await self._write_line(command)
                    response = await self._read_response()
                    return response
                else:
                    raise

    # ==================== CONFIGURATION ====================

    async def set_instance(self, instance_name: str) -> None:
        """
        Select which Music Server instance to control.

        Args:
            instance_name: e.g., "Music_Server_A", "Music_Server_B", etc.
        """
        await self._execute_command(f"SetInstance {instance_name}")
        self._current_instance = instance_name

    # ==================== BROWSING ====================

    async def browse_instances(self) -> List[str]:
        """
        Get list of available Music Server instances.

        Returns:
            List of instance names (e.g., ["Music_Server_A", "Music_Server_B"])
        """
        response = await self._execute_command("BrowseInstancesEX")

        instances = []
        xml_data = '\n'.join(response)

        try:
            root = ET.fromstring(xml_data)
            # Find all InstanceInfoEx elements
            for instance in root.findall('.//InstanceInfoEx'):
                instance_name = instance.get('instance', '')
                if instance_name:
                    instances.append(instance_name)
        except Exception as e:
            print(f"[SimpleMCS] Error parsing instances: {e}")

        return instances

    async def browse_pick_list(self) -> List[PickListItem]:
        """
        Browse radio stations from the currently selected Music Server instance.
        Uses BrowseRadioStations command.
        Returns list of radio station items.
        """
        # Use _execute_command for proper reconnection handling
        response = await self._execute_command("BrowseRadioStations")

        items = []

        # Parse XML response
        xml_data = '\n'.join(response)
        print(f"[SimpleMCS] BrowseRadioStations response: {len(response)} lines")

        try:
            # Parse using ElementTree
            root = ET.fromstring(xml_data)

            # Find all RadioStation elements
            for station in root.findall('.//RadioStation'):
                name = station.get('name', 'Unknown')
                guid = station.get('guid', '')
                desc = station.get('desc', name)

                items.append(PickListItem(
                    index=len(items),
                    title=name,
                    guid=guid,
                    item_type="RadioStation",
                    metadata={'desc': desc}
                ))

        except Exception as e:
            print(f"[SimpleMCS] Error parsing radio stations: {e}")
            import traceback
            traceback.print_exc()

        print(f"[SimpleMCS] Parsed {len(items)} radio stations")
        if items:
            print(f"[SimpleMCS] First station: {items[0].title}")

        return items

    # ==================== PLAYBACK ====================

    async def play_radio_station(self, guid: str) -> None:
        """
        Play a Pandora radio station by GUID.

        Args:
            guid: Station GUID from BrowseRadioStations
        """
        await self._execute_command(f"PlayRadioStation {guid}")

    async def play_radio_station_by_name(self, name: str) -> None:
        """
        Play a Pandora radio station by name.

        Args:
            name: Station name
        """
        await self._execute_command(f'PlayRadioStation "{name}"')

    # ==================== LOCAL MUSIC LIBRARY ====================

    async def browse_now_playing(self) -> List[Dict[str, Any]]:
        """
        Browse the current queue/now playing list.

        Returns:
            List of tracks with metadata (name, artist, album, guid, duration, etc.)
        """
        response = await self._execute_command("BrowseNowPlaying")

        tracks = []
        xml_data = '\n'.join(response)

        try:
            root = ET.fromstring(xml_data)

            # Find all Title elements
            for title in root.findall('.//Title'):
                track = {
                    'guid': title.get('guid', ''),
                    'name': title.get('name', 'Unknown'),
                    'artist': title.get('artist', ''),
                    'album': title.get('album', ''),
                    'album_guid': title.get('albumGuid', ''),
                    'duration': title.get('duration', '00:00:00'),
                    'track_number': int(title.get('track', 0)),
                    'queue_index': int(title.get('npIndex', 0)),
                    'is_now_playing': title.get('np', '') == '1'
                }
                tracks.append(track)

        except Exception as e:
            print(f"[SimpleMCS] Error parsing now playing: {e}")

        return tracks

    async def browse_albums(self) -> List[Dict[str, str]]:
        """
        Browse all albums in the local music library.

        Returns:
            List of albums with name and GUID
        """
        response = await self._execute_command("BrowseAlbums")

        albums = []
        xml_data = '\n'.join(response)

        try:
            root = ET.fromstring(xml_data)

            # Find all Album elements
            for album in root.findall('.//Album'):
                albums.append({
                    'guid': album.get('guid', ''),
                    'name': album.get('name', 'Unknown Album'),
                    'artist': album.get('artist', ''),
                    'unique_name': album.get('unique', '')
                })

        except Exception as e:
            print(f"[SimpleMCS] Error parsing albums: {e}")

        return albums

    async def browse_artists(self) -> List[Dict[str, str]]:
        """
        Browse all artists in the local music library.

        Returns:
            List of artists with name and GUID
        """
        response = await self._execute_command("BrowseArtists")

        artists = []
        xml_data = '\n'.join(response)

        try:
            root = ET.fromstring(xml_data)

            # Find all Artist elements
            for artist in root.findall('.//Artist'):
                artists.append({
                    'guid': artist.get('guid', ''),
                    'name': artist.get('name', 'Unknown Artist')
                })

        except Exception as e:
            print(f"[SimpleMCS] Error parsing artists: {e}")

        return artists

    async def browse_album_titles(self, album_guid: str) -> List[Dict[str, Any]]:
        """
        Browse tracks in a specific album.

        Args:
            album_guid: Album GUID

        Returns:
            List of tracks in the album
        """
        response = await self._execute_command(f"BrowseAlbumTitles {album_guid}")

        tracks = []
        xml_data = '\n'.join(response)

        try:
            root = ET.fromstring(xml_data)

            # Find all Title elements
            for title in root.findall('.//Title'):
                tracks.append({
                    'guid': title.get('guid', ''),
                    'name': title.get('name', 'Unknown'),
                    'artist': title.get('artist', ''),
                    'album': title.get('album', ''),
                    'duration': title.get('duration', '00:00:00'),
                    'track_number': int(title.get('track', 0))
                })

        except Exception as e:
            print(f"[SimpleMCS] Error parsing album titles: {e}")

        return tracks

    async def play_title(self, guid: str) -> None:
        """
        Play a specific track by GUID.

        Args:
            guid: Track GUID
        """
        await self._execute_command(f"PlayTitle {guid}")

    async def play_album(self, guid: str) -> None:
        """
        Play an entire album by GUID.

        Args:
            guid: Album GUID
        """
        await self._execute_command(f"PlayAlbum {guid}")

    async def play_artist(self, guid: str) -> None:
        """
        Play all tracks by an artist.

        Args:
            guid: Artist GUID
        """
        await self._execute_command(f"PlayArtist {guid}")

    async def play_all_music(self) -> None:
        """Play all music in the library."""
        await self._execute_command("PlayAllMusic")

    # ==================== NAVIGATION ====================

    async def ack_pick_item(self, index: int) -> None:
        """
        Select/acknowledge a pick list item by index.
        Used to navigate into menus or play items.
        """
        await self._execute_command(f"AckPickItem {index}")

    async def set_radio_filter(self, filter_text: str) -> None:
        """Set radio station filter text."""
        import base64
        # Base64 encode the filter text
        encoded = base64.b64encode(filter_text.encode('utf-8')).decode('ascii')
        await self._execute_command(f"SetRadioFilter {encoded}")

    # ==================== STATUS ====================

    async def get_status(self) -> Dict[str, Any]:
        """Get current MCS status."""
        response = await self._execute_command("GetStatus")

        status = {
            'volume': 0,
            'mute': False,
            'play_state': 'Unknown',
            'now_playing': {},
        }

        # Parse status response
        # GetStatus returns lines like: "ReportState Music_Server_A Volume=50"
        for line in response:
            if '=' not in line:
                continue

            # Handle "ReportState Instance_Name Key=Value" format
            if line.startswith('ReportState'):
                parts = line.split(None, 2)  # Split on whitespace, max 2 splits
                if len(parts) >= 3:
                    key_value = parts[2]  # Extract "Key=Value" part
                else:
                    continue
            else:
                key_value = line

            # Now extract key and value
            if '=' in key_value:
                key, value = key_value.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Parse known fields
                if key == 'Volume':
                    try:
                        status['volume'] = int(value)
                    except:
                        pass
                elif key == 'Mute':
                    status['mute'] = value.lower() == 'true'
                elif key == 'PlayState':
                    status['play_state'] = value
                elif key == 'TrackName':
                    status['now_playing']['track'] = value
                elif key == 'ArtistName':
                    status['now_playing']['artist'] = value
                elif key == 'MediaName':
                    status['now_playing']['album'] = value
                elif key == 'StationName':
                    status['now_playing']['station'] = value

        return status
