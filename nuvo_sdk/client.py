"""Main NuVo MusicPort client."""

import asyncio
import time
from typing import List, Optional, Callable
from .models import Zone, Source, SystemStatus, StateChangeEvent
from .protocol import (
    build_command,
    parse_zones_xml,
    parse_sources_xml,
    parse_state_changed,
    update_zones_from_status,
    parse_system_properties,
)
from .events import EventManager
from .exceptions import ConnectionError, ProtocolError, CommandError


class NuVoClient:
    """
    Async client for NuVo MusicPort MRAD protocol (port 5006).

    Example:
        >>> client = NuVoClient()
        >>> await client.connect("10.0.0.45")
        >>> zones = await client.get_zones()
        >>> await client.set_zone(zones[0].guid)
        >>> await client.set_volume(50)
        >>> await client.disconnect()
    """

    DEFAULT_PORT = 5006
    RECONNECT_DELAY = 5.0
    READ_TIMEOUT = 10.0
    COMMAND_TIMEOUT = 5.0

    def __init__(self, host: Optional[str] = None, port: int = DEFAULT_PORT):
        """
        Initialize NuVo client.

        Args:
            host: Device IP address (can be set later in connect())
            port: MRAD port (default: 5006)
        """
        self.host = host
        self.port = port

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._listener_task: Optional[asyncio.Task] = None
        self._event_manager = EventManager()

        # Response queue for command replies - listener puts responses here
        # Lazy-initialized to avoid event loop issues
        self._response_queue: Optional[asyncio.Queue] = None
        self._waiting_for_response = False

        # Lock to serialize command execution (prevent concurrent requests)
        # Lazy-initialized to avoid event loop issues
        self._command_lock: Optional[asyncio.Lock] = None

        # Active zone context (for commands that don't specify zone)
        self._active_zone: Optional[str] = None

    def _ensure_async_resources(self):
        """Ensure asyncio resources are created in the event loop context."""
        if self._response_queue is None:
            self._response_queue = asyncio.Queue()
        if self._command_lock is None:
            self._command_lock = asyncio.Lock()

    async def connect(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
        Connect to the NuVo device.

        Args:
            host: Device IP address (uses instance default if not provided)
            port: MRAD port (uses instance default if not provided)

        Raises:
            ConnectionError: If connection fails
        """
        # Ensure asyncio resources are initialized in event loop context
        self._ensure_async_resources()

        if host:
            self.host = host
        if port:
            self.port = port

        if not self.host:
            raise ConnectionError("Host address not provided")

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.COMMAND_TIMEOUT,
            )
            self._connected = True

            # Send initialization sequence
            await self._initialize()

            # Start background listener for events
            self._listener_task = asyncio.create_task(self._event_listener())

        except asyncio.TimeoutError:
            raise ConnectionError(f"Connection timeout to {self.host}:{self.port}")
        except OSError as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")

    async def disconnect(self) -> None:
        """Close connection to device."""
        self._connected = False

        # Cancel listener task
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        # Close connection
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except:
                pass
            self._writer = None
            self._reader = None

    async def _initialize(self) -> None:
        """Send initialization commands to device."""
        # Send wake-up command
        self._writer.write(b"*\r")
        await self._writer.drain()
        await asyncio.sleep(0.2)

        # Read welcome banner
        try:
            banner = await asyncio.wait_for(
                self._reader.readuntil(b"\x07"),  # Bell character at end of banner
                timeout=3.0,
            )
        except asyncio.TimeoutError:
            # If no banner, that's okay
            pass

        # Clear any remaining init data
        try:
            while True:
                line = await asyncio.wait_for(self._reader.readline(), timeout=0.1)
                if not line:
                    break
        except asyncio.TimeoutError:
            pass

        # Initialize protocol - send batch command
        init_cmd = "SetXMLMode Lists\rSubscribeEvents smart\r"
        self._writer.write(init_cmd.encode("utf-8"))
        await self._writer.drain()

        # Read init responses
        await asyncio.sleep(0.3)
        try:
            while True:
                line = await asyncio.wait_for(self._reader.readline(), timeout=0.2)
                if not line:
                    break
        except asyncio.TimeoutError:
            pass

    async def _send_command(self, command: str) -> None:
        """
        Send a command to the device.

        Args:
            command: Command string

        Raises:
            ConnectionError: If not connected
            CommandError: If send fails
        """
        if not self._connected or not self._writer:
            raise ConnectionError("Not connected to device")

        try:
            cmd_bytes = build_command(command)
            self._writer.write(cmd_bytes)
            await self._writer.drain()
        except OSError as e:
            self._connected = False
            raise CommandError(f"Failed to send command: {e}")

    async def _read_response(self, timeout: float = COMMAND_TIMEOUT) -> List[str]:
        """
        Read response lines from device via the queue populated by listener.

        Args:
            timeout: Read timeout in seconds

        Returns:
            List of response lines
        """
        # Signal listener that we're waiting for a command response
        self._waiting_for_response = True

        lines = []
        start_time = time.time()

        try:
            while time.time() - start_time < timeout:
                remaining = timeout - (time.time() - start_time)
                if remaining <= 0:
                    break

                try:
                    # Get lines from queue (populated by listener)
                    line = await asyncio.wait_for(
                        self._response_queue.get(),
                        timeout=min(remaining, 0.5)
                    )

                    if line is None:  # Sentinel for end of response
                        break

                    lines.append(line)

                    # Check if this looks like end of response
                    if line.endswith(">") or line == "Ok":
                        break

                except asyncio.TimeoutError:
                    # No more data available
                    if lines:
                        break
                    continue

        except Exception as e:
            raise ProtocolError(f"Failed to read response: {e}")
        finally:
            self._waiting_for_response = False

        return lines

    async def _execute_command(self, command: str, timeout: float = COMMAND_TIMEOUT) -> List[str]:
        """
        Execute a command with lock to prevent concurrent access.

        Args:
            command: Command string to send
            timeout: Read timeout in seconds

        Returns:
            List of response lines

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
            ProtocolError: If response parsing fails
        """
        # Ensure lock is initialized (should be done in connect, but just in case)
        if self._command_lock is None:
            self._ensure_async_resources()

        async with self._command_lock:
            await self._send_command(command)
            return await self._read_response(timeout)

    async def _event_listener(self) -> None:
        """
        Background task to listen for all incoming data.
        Routes command responses to queue and events to subscribers.
        """
        while self._connected:
            try:
                line = await self._reader.readline()
                if not line:
                    # Connection closed
                    self._connected = False
                    break

                decoded = line.decode("utf-8", errors="ignore").strip()
                if not decoded:
                    continue

                # Route based on content and whether we're waiting for response
                if decoded.startswith("StateChanged"):
                    # This is an event - always broadcast
                    event = parse_state_changed(decoded)
                    if event:
                        event.timestamp = time.time()
                        await self._event_manager.notify(event)

                elif self._waiting_for_response:
                    # This is part of a command response - put in queue
                    await self._response_queue.put(decoded)

                else:
                    # Unsolicited data (banner, prompts, etc.) - ignore or log
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in event listener: {e}")
                await asyncio.sleep(1.0)

    # Discovery methods

    async def get_zones(self) -> List[Zone]:
        """
        Get all zones from the device.

        Returns:
            List of Zone objects

        Raises:
            ConnectionError: If not connected
            ProtocolError: If response parsing fails
        """
        # Retry logic for reliability
        for attempt in range(3):
            try:
                response = await self._execute_command("BrowseZones", timeout=10.0)

                # Find XML response
                xml_data = "".join(response)
                if "<Zones" not in xml_data:
                    if attempt < 2:  # Retry if not last attempt
                        await asyncio.sleep(0.5)
                        continue
                    raise ProtocolError("No zones data in response")

                # Parse zones
                zones = parse_zones_xml(xml_data)

                # Get detailed status to fill in volume, mute, etc.
                status_response = await self._execute_command("GetStatus", timeout=5.0)

                # Update zones with status data
                update_zones_from_status(zones, status_response)

                return zones

            except asyncio.TimeoutError:
                if attempt < 2:
                    await asyncio.sleep(0.5)
                    continue
                raise ProtocolError("Timeout getting zones data")

        raise ProtocolError("Failed to get zones after 3 attempts")

    async def get_sources(self) -> List[Source]:
        """
        Get all sources from the device.

        Returns:
            List of Source objects

        Raises:
            ConnectionError: If not connected
            ProtocolError: If response parsing fails
        """
        # Retry logic for reliability
        for attempt in range(3):
            try:
                response = await self._execute_command("BrowseSources", timeout=10.0)

                # Find XML response
                xml_data = "".join(response)
                if "<Sources" not in xml_data:
                    if attempt < 2:  # Retry if not last attempt
                        await asyncio.sleep(0.5)
                        continue
                    raise ProtocolError("No sources data in response")

                return parse_sources_xml(xml_data)

            except asyncio.TimeoutError:
                if attempt < 2:
                    await asyncio.sleep(0.5)
                    continue
                raise ProtocolError("Timeout getting sources data")

        raise ProtocolError("Failed to get sources after 3 attempts")

    async def get_status(self) -> SystemStatus:
        """
        Get complete system status.

        Returns:
            SystemStatus object with all zones and sources

        Raises:
            ConnectionError: If not connected
            ProtocolError: If response parsing fails
        """
        # Get zones and sources
        zones = await self.get_zones()
        sources = await self.get_sources()

        # Get system properties
        status_response = await self._execute_command("GetStatus", timeout=3.0)
        system_props = parse_system_properties(status_response)

        return SystemStatus(
            device_type=system_props.get("DeviceType", "Unknown"),
            firmware_version=system_props.get("FirmwareVersion", "Unknown"),
            all_mute=system_props.get("AllMute", "False") == "True",
            all_off=system_props.get("AllOff", "False") == "True",
            active_zone=system_props.get("ActiveZone", ""),
            active_source=system_props.get("ActiveSource", ""),
            zones=zones,
            sources=sources,
        )

    # Zone control methods

    async def set_zone(self, zone_guid: str) -> None:
        """
        Set the active zone context.

        Args:
            zone_guid: Zone GUID to activate

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
        """
        async with self._command_lock:
            await self._send_command(f"setZone {zone_guid}")
            self._active_zone = zone_guid
            # Small delay for command to process
            await asyncio.sleep(0.1)

    async def power_on(self, zone_number: int) -> None:
        """
        Turn on a zone by number.

        Args:
            zone_number: Zone number (1-6)

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
        """
        async with self._command_lock:
            await self._send_command(f"Power On {zone_number}")
            await asyncio.sleep(0.1)

    async def power_off(self, zone_number: int) -> None:
        """
        Turn off a zone by number.

        Args:
            zone_number: Zone number (1-6)

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
        """
        async with self._command_lock:
            await self._send_command(f"Power Off {zone_number}")
            await asyncio.sleep(0.1)

    async def set_volume(self, volume: int, zone_number: Optional[int] = None) -> None:
        """
        Set volume for current zone or specified zone.

        Args:
            volume: Volume level (0-79)
            zone_number: Optional zone number (uses active zone if not specified)

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
            ValueError: If volume out of range
        """
        if not 0 <= volume <= 79:
            raise ValueError("Volume must be between 0 and 79")

        async with self._command_lock:
            if zone_number:
                await self._send_command(f"Volume {volume} {zone_number}")
            else:
                await self._send_command(f"Volume {volume}")
            await asyncio.sleep(0.1)

    async def mute_toggle(self, zone_number: Optional[int] = None) -> None:
        """
        Toggle mute for current zone or specified zone.

        Args:
            zone_number: Optional zone number

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
        """
        async with self._command_lock:
            if zone_number:
                await self._send_command(f"Mute Toggle {zone_number}")
            else:
                await self._send_command("Mute Toggle")
            await asyncio.sleep(0.1)

    # Source control methods

    async def set_source(self, source_guid: str) -> None:
        """
        Set source for active zone.

        Args:
            source_guid: Source GUID to activate

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
        """
        async with self._command_lock:
            await self._send_command(f"setSource {source_guid}")
            await asyncio.sleep(0.1)

    # System control methods

    async def party_mode_toggle(self) -> None:
        """
        Toggle party mode (all zones play same source).

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
        """
        async with self._command_lock:
            await self._send_command("PartyMode Toggle")
            await asyncio.sleep(0.1)

    async def all_off(self) -> None:
        """
        Turn off all zones.

        Raises:
            ConnectionError: If not connected
            CommandError: If command fails
        """
        async with self._command_lock:
            await self._send_command("AllOff")
            await asyncio.sleep(0.1)

    # Event subscription

    def subscribe(self, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Subscribe to state change events.

        Args:
            callback: Function to call with StateChangeEvent
                     Can be sync or async function
        """
        self._event_manager.subscribe(callback)

    def unsubscribe(self, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Unsubscribe from state change events.

        Args:
            callback: Function to remove
        """
        self._event_manager.unsubscribe(callback)

    # Context manager support

    async def __aenter__(self):
        """Async context manager entry."""
        if not self._connected:
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
