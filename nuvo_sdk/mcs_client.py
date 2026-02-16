"""Media Control Server (MCS) client for NuVo MusicPort."""

import asyncio
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class MusicServer:
    """Represents a Music Server instance."""
    name: str
    running: bool
    supported_types: List[str]  # e.g., ['Sirius', 'Pandora', 'Spotify', ...]
    supports_music: bool
    supports_radio: bool
    volume: int
    mute: bool
    play_state: str  # 'Playing', 'Paused', 'Stopped'
    now_playing: Optional[Dict[str, str]] = None


@dataclass
class PickListItem:
    """Represents an item in a browse menu/pick list."""
    index: int
    title: str
    guid: str
    item_type: str  # 'Station', 'Album', 'Playlist', 'Track', etc.
    metadata: Dict[str, str]


class MCSClient:
    """
    Async client for NuVo MusicPort Media Control Server (MCS) protocol (port 5004).

    Used for controlling Music Servers (A, B, C, D) - browsing content,
    playing radio stations, Spotify, Pandora, etc.

    Example:
        >>> mcs = MCSClient()
        >>> await mcs.connect("10.0.0.45")
        >>> servers = await mcs.get_servers()
        >>> await mcs.set_instance("Music_Server_A")
        >>> items = await mcs.browse_pick_list()
        >>> await mcs.ack_pick_item(0)  # Select first item
    """

    DEFAULT_PORT = 5004
    READ_TIMEOUT = 15.0  # Increased for slow devices
    COMMAND_TIMEOUT = 10.0  # Increased for slow devices

    def __init__(self, host: Optional[str] = None, port: int = DEFAULT_PORT):
        """
        Initialize MCS client.

        Args:
            host: Device IP address
            port: MCS port (default: 5004)
        """
        self.host = host
        self.port = port

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._current_instance: Optional[str] = None

        # Async resources (created in event loop)
        self._response_queue: Optional[asyncio.Queue] = None
        self._command_lock: Optional[asyncio.Lock] = None
        self._reconnect_lock: Optional[asyncio.Lock] = None
        self._listen_task: Optional[asyncio.Task] = None
        self._is_reconnecting: bool = False

    def _ensure_async_resources(self):
        """Ensure asyncio resources are created in the event loop context."""
        if self._response_queue is None:
            self._response_queue = asyncio.Queue()
        if self._command_lock is None:
            self._command_lock = asyncio.Lock()
        if self._reconnect_lock is None:
            self._reconnect_lock = asyncio.Lock()

    async def connect(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Connect to MCS server.

        Args:
            host: Device IP address (uses self.host if not provided)
            port: MCS port (uses self.port if not provided)
        """
        self._ensure_async_resources()

        if host:
            self.host = host
        if port:
            self.port = port

        if not self.host:
            raise ValueError("Host must be provided")

        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.host, self.port
            )
            self._connected = True

            # Start listener task
            self._listen_task = asyncio.create_task(self._listen())

            # Initialize connection
            await self._send_command(f"SetHost {self.host}")
            await self._send_command("SetXMLMode Lists")
            await self._send_command('SetClientType "Python"')
            await self._send_command("SetEncoding 65001")
            await self._send_command("SetPickListCount 100")
            await self._send_command("SubscribeEvents")

        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MCS server: {e}")

    async def disconnect(self) -> None:
        """Disconnect from MCS server."""
        self._connected = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()

    async def reconnect(self) -> None:
        """Reconnect to MCS server after connection loss."""
        if self._reconnect_lock is None:
            self._ensure_async_resources()

        # Use lock to prevent multiple simultaneous reconnections
        async with self._reconnect_lock:
            # If already reconnecting, wait
            if self._is_reconnecting:
                print("[MCS] Already reconnecting, waiting...")
                for _ in range(10):
                    await asyncio.sleep(0.5)
                    if self._connected:
                        print("[MCS] Reconnection completed by another thread")
                        return
                raise ConnectionError("Reconnection timeout - another reconnection in progress")

            if self._connected:
                print("[MCS] Already connected, no reconnection needed")
                return

            self._is_reconnecting = True
            print("[MCS] Attempting to reconnect...")

            try:
                # THOROUGH cleanup of old connection state
                self._connected = False

                # Cancel and wait for listener task to fully stop
                if self._listen_task and not self._listen_task.done():
                    print("[MCS] Stopping old listener task...")
                    self._listen_task.cancel()
                    try:
                        await asyncio.wait_for(self._listen_task, timeout=2.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        pass
                self._listen_task = None

                # Close writer and wait for it
                if self._writer and not self._writer.is_closing():
                    print("[MCS] Closing old writer...")
                    try:
                        self._writer.close()
                        await asyncio.wait_for(self._writer.wait_closed(), timeout=2.0)
                    except asyncio.TimeoutError:
                        print("[MCS] Writer close timed out")
                        pass
                self._writer = None
                self._reader = None

                # Clear any stale responses from queue
                if self._response_queue:
                    while not self._response_queue.empty():
                        try:
                            self._response_queue.get_nowait()
                        except:
                            break

                # Wait for device to settle (old devices need time)
                print("[MCS] Waiting 3s for device to settle...")
                await asyncio.sleep(3.0)

                # Reconnect with fresh state
                print("[MCS] Creating new connection...")
                await self.connect()
                print("[MCS] Reconnected successfully")

                # Give connection time to stabilize before use (old device needs lots of time!)
                print("[MCS] Waiting 3s for connection to stabilize...")
                await asyncio.sleep(3.0)

                # Restore instance if one was set
                if self._current_instance:
                    print(f"[MCS] Restoring instance: {self._current_instance}")
                    # Use _send_command directly to avoid recursion
                    self._writer.write(f"SetInstance {self._current_instance}\r\n".encode('utf-8'))
                    await self._writer.drain()
                    await asyncio.sleep(1.0)

            except Exception as e:
                print(f"[MCS] Reconnection failed: {e}")
                import traceback
                traceback.print_exc()
                self._is_reconnecting = False
                self._connected = False
                raise
            finally:
                self._is_reconnecting = False

    async def _send_command(self, command: str) -> None:
        """Send a command to the server."""
        if not self._writer:
            raise ConnectionError("Not connected")

        self._writer.write(f"{command}\r\n".encode('utf-8'))
        await self._writer.drain()

    async def _listen(self) -> None:
        """Background task to listen for server responses."""
        try:
            while self._connected and self._reader:
                line = await asyncio.wait_for(
                    self._reader.readline(),
                    timeout=self.READ_TIMEOUT
                )

                if not line:
                    break

                text = line.decode('utf-8', errors='ignore').strip()
                if text:
                    await self._response_queue.put(text)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            import traceback
            print(f"MCS listen error: {type(e).__name__}: {e}")
            traceback.print_exc()

            # Mark connection as broken
            self._connected = False

            # Auto-reconnect after a delay
            print("[MCS] Connection lost in listener, will auto-reconnect on next command")
            # Don't reconnect here to avoid conflicts - let the next command trigger reconnect

    async def _read_response(self, timeout: float = COMMAND_TIMEOUT) -> List[str]:
        """Read response lines from queue."""
        lines = []
        deadline = asyncio.get_event_loop().time() + timeout

        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                break

            try:
                line = await asyncio.wait_for(
                    self._response_queue.get(),
                    timeout=min(0.5, remaining)
                )
                lines.append(line)

                # Check for completion markers
                if any(marker in line for marker in ['=Done', 'Ok', '</']) or len(lines) > 100:
                    break

            except asyncio.TimeoutError:
                if lines:  # Got some response, that's OK
                    break

        return lines

    async def _execute_command(self, command: str, timeout: float = COMMAND_TIMEOUT, retry: bool = True) -> List[str]:
        """Execute command and get response with automatic reconnection on failure."""
        if self._command_lock is None:
            self._ensure_async_resources()

        async with self._command_lock:
            # Check if connection is alive, reconnect if needed (but not if already reconnecting!)
            if not self._is_reconnecting and (not self._connected or not self._writer or self._writer.is_closing()):
                if retry:
                    print(f"[MCS] Connection not alive before command '{command}', reconnecting...")
                    try:
                        await self.reconnect()
                    except Exception as e:
                        print(f"[MCS] Pre-command reconnection failed: {e}")
                        raise ConnectionError(f"MCS connection is down and reconnection failed: {e}")
                else:
                    raise ConnectionError("MCS connection is not alive")
            elif self._is_reconnecting:
                # If reconnection is in progress, wait for it
                print(f"[MCS] Waiting for reconnection to complete before '{command}'...")
                for _ in range(20):
                    await asyncio.sleep(0.5)
                    if not self._is_reconnecting and self._connected:
                        break
                if not self._connected:
                    raise ConnectionError("Reconnection did not complete in time")

            try:
                # Clear queue
                while not self._response_queue.empty():
                    self._response_queue.get_nowait()

                await self._send_command(command)
                return await self._read_response(timeout)

            except (ConnectionResetError, ConnectionError, BrokenPipeError, OSError) as e:
                if not retry:
                    raise

                print(f"[MCS] Connection error during command '{command}': {e}")
                print("[MCS] Attempting to reconnect and retry...")

                try:
                    await self.reconnect()
                    # Retry the command once after reconnecting
                    while not self._response_queue.empty():
                        self._response_queue.get_nowait()
                    await self._send_command(command)
                    return await self._read_response(timeout)
                except Exception as retry_error:
                    print(f"[MCS] Retry after reconnection failed: {retry_error}")
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

    async def set_pick_list_count(self, count: int) -> None:
        """Set number of items returned in browse lists."""
        await self._execute_command(f"SetPickListCount {count}")

    # ==================== BROWSING ====================

    async def browse_instances(self) -> List[str]:
        """Get list of available Music Server instances."""
        response = await self._execute_command("BrowseInstancesEX")
        # Parse XML response to get instance names
        instances = []
        for line in response:
            if '<Instance' in line:
                try:
                    # Extract instance name from XML
                    import re
                    match = re.search(r'name="([^"]+)"', line)
                    if match:
                        instances.append(match.group(1))
                except:
                    pass
        return instances

    async def browse_pick_list(self) -> List[PickListItem]:
        """
        Browse current menu/pick list items.
        Returns list of items (stations, albums, playlists, etc.).
        """
        response = await self._execute_command("BrowsePickList")
        items = []

        # Parse XML response
        xml_data = '\n'.join(response)
        print(f"[MCS] BrowsePickList response lines: {len(response)}")
        if len(response) > 0:
            print(f"[MCS] First response line: {response[0][:100] if response[0] else 'EMPTY'}")
        try:
            # Simple parsing for pick list items
            import re
            matches = re.finditer(r'<PickListItem[^>]*>', xml_data)
            for i, match in enumerate(matches):
                item_str = match.group(0)

                # Extract attributes
                title = re.search(r'title="([^"]*)"', item_str)
                guid = re.search(r'guid="([^"]*)"', item_str)
                item_type = re.search(r'type="([^"]*)"', item_str)

                items.append(PickListItem(
                    index=i,
                    title=title.group(1) if title else f"Item {i}",
                    guid=guid.group(1) if guid else "",
                    item_type=item_type.group(1) if item_type else "Unknown",
                    metadata={}
                ))
        except:
            pass

        return items

    async def browse_now_playing(self) -> List[Dict[str, Any]]:
        """Browse now playing queue."""
        response = await self._execute_command("BrowseNowPlaying")
        # TODO: Parse queue items from response
        return []

    # ==================== FILTERS ====================

    async def set_radio_filter(self, filter_value: str = "") -> None:
        """
        Set radio station filter/search.

        Args:
            filter_value: Search term or filter (empty to clear)
        """
        if filter_value:
            await self._execute_command(f"SetRadioFilter {filter_value}")
        else:
            await self._execute_command("SetRadioFilter Clear")

    async def set_music_filter(self, filter_value: str = "") -> None:
        """Set music library filter/search."""
        if filter_value:
            await self._execute_command(f"SetMusicFilter {filter_value}")
        else:
            await self._execute_command("SetMusicFilter Clear")

    # ==================== PLAYBACK ====================

    async def ack_pick_item(self, index: int) -> None:
        """
        Select/acknowledge an item from the pick list.
        This is how you select a radio station, playlist, album, etc.

        Args:
            index: Index of item in the pick list (0-based)
        """
        await self._execute_command(f"AckPickItem {index}")

    async def play_album(self, guid: str) -> None:
        """Play a specific album by GUID."""
        await self._execute_command(f"PlayAlbum {guid}")

    async def play_all_music(self) -> None:
        """Play all music."""
        await self._execute_command("PlayAllMusic")

    async def jump_to_now_playing_item(self, index: int) -> None:
        """Jump to specific item in now playing queue."""
        await self._execute_command(f"JumpToNowPlayingItem {index}")

    # ==================== QUEUE MANAGEMENT ====================

    async def add_to_queue(self, guid: str) -> None:
        """Add item to now playing queue."""
        await self._execute_command(f"AddToQueue {guid}")

    async def add_list_to_queue(self) -> None:
        """Add entire current list to queue."""
        await self._execute_command("AddListToQueue")

    async def clear_now_playing(self) -> None:
        """Clear the now playing queue."""
        await self._execute_command("ClearNowPlaying")

    async def remove_now_playing_item(self, index: int) -> None:
        """Remove specific item from queue."""
        await self._execute_command(f"RemoveNowPlayingItem {index}")

    async def save_playlist(self, name: str) -> None:
        """Save current queue as a playlist."""
        await self._execute_command(f"SavePlaylist {name}")

    # ==================== CONTROL ====================

    async def set_volume(self, volume: int) -> None:
        """
        Set Music Server volume (0-100).

        Args:
            volume: Volume level 0-100
        """
        await self._execute_command(f"SetVolume {volume}")

    # ==================== STATUS ====================

    async def get_status(self) -> Dict[str, Any]:
        """
        Get full Music Server status.
        Returns dict with server state, now playing info, etc.
        """
        response = await self._execute_command("GetMCEStatus", timeout=10.0)

        status = {
            'server_name': None,
            'instance_name': None,
            'running': False,
            'volume': 50,
            'mute': False,
            'play_state': 'Stopped',
            'now_playing': {},
            'supported_types': [],
        }

        # Parse response lines
        for line in response:
            if 'ServerName=' in line:
                status['server_name'] = line.split('=', 1)[1].strip()
            elif 'InstanceName=' in line:
                status['instance_name'] = line.split('=', 1)[1].strip()
            elif 'Running=' in line:
                status['running'] = 'True' in line
            elif 'Volume=' in line:
                try:
                    status['volume'] = int(line.split('=', 1)[1].strip())
                except:
                    pass
            elif 'Mute=' in line:
                status['mute'] = 'True' in line
            elif 'PlayState=' in line:
                status['play_state'] = line.split('=', 1)[1].strip()
            elif 'SupportedAudioTypes=' in line:
                types_str = line.split('=', 1)[1].strip()
                status['supported_types'] = types_str.split(',')
            elif 'TrackName=' in line:
                status['now_playing']['track'] = line.split('=', 1)[1].strip()
            elif 'ArtistName=' in line:
                status['now_playing']['artist'] = line.split('=', 1)[1].strip()
            elif 'StationName=' in line:
                status['now_playing']['station'] = line.split('=', 1)[1].strip()

        return status
