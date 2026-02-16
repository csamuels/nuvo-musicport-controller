"""Integration tests for NuVo client (requires real device)."""

import pytest
import asyncio
from nuvo_sdk import NuVoClient, StateChangeEvent

# Configure your device IP here
DEVICE_IP = "10.0.0.45"
DEVICE_PORT = 5006

# Mark all tests as requiring device
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    """Create and connect client for testing."""
    client = NuVoClient(DEVICE_IP, DEVICE_PORT)
    await client.connect()
    yield client
    await client.disconnect()


class TestConnection:
    """Test basic connection operations."""

    async def test_connect_disconnect(self):
        """Test connecting and disconnecting."""
        client = NuVoClient(DEVICE_IP, DEVICE_PORT)
        await client.connect()
        assert client._connected is True
        await client.disconnect()
        assert client._connected is False

    async def test_context_manager(self):
        """Test async context manager usage."""
        async with NuVoClient(DEVICE_IP, DEVICE_PORT) as client:
            assert client._connected is True
        assert client._connected is False


class TestDiscovery:
    """Test discovery methods."""

    async def test_get_zones(self, client):
        """Test retrieving zones."""
        zones = await client.get_zones()

        assert len(zones) > 0
        assert all(z.name for z in zones)
        assert all(z.zone_id for z in zones)
        assert all(z.guid for z in zones)

        # Check expected zones
        zone_names = [z.name for z in zones]
        assert "Master Bedroom" in zone_names
        assert "Living Room" in zone_names

        # Validate data structure
        for zone in zones:
            assert 0 <= zone.volume <= 79
            assert zone.zone_number > 0
            assert isinstance(zone.is_on, bool)
            assert isinstance(zone.mute, bool)

    async def test_get_sources(self, client):
        """Test retrieving sources."""
        sources = await client.get_sources()

        assert len(sources) > 0
        assert all(s.name for s in sources)
        assert all(s.guid for s in sources)

        # Check expected sources
        source_names = [s.name for s in sources]
        assert any("Music Server" in name for name in source_names)

    async def test_get_status(self, client):
        """Test retrieving full system status."""
        status = await client.get_status()

        assert status.device_type
        assert status.firmware_version
        assert len(status.zones) > 0
        assert len(status.sources) > 0
        assert status.active_zone
        assert isinstance(status.all_mute, bool)
        assert isinstance(status.all_off, bool)


class TestZoneControl:
    """Test zone control commands."""

    async def test_set_zone(self, client):
        """Test setting active zone."""
        zones = await client.get_zones()
        first_zone = zones[0]

        await client.set_zone(first_zone.guid)
        # If no exception, command succeeded

    async def test_power_control(self, client):
        """Test power on/off."""
        zones = await client.get_zones()
        test_zone = zones[0]

        # Turn on
        await client.power_on(test_zone.zone_number)
        await asyncio.sleep(0.5)  # Allow state to update

        # Turn off
        await client.power_off(test_zone.zone_number)
        await asyncio.sleep(0.5)

    async def test_volume_control(self, client):
        """Test volume setting."""
        zones = await client.get_zones()
        test_zone = zones[0]

        # Set specific volume
        await client.set_volume(50, test_zone.zone_number)
        await asyncio.sleep(0.5)

    async def test_volume_validation(self, client):
        """Test volume range validation."""
        with pytest.raises(ValueError):
            await client.set_volume(100)  # Too high

        with pytest.raises(ValueError):
            await client.set_volume(-1)  # Too low

    async def test_mute_toggle(self, client):
        """Test mute toggle."""
        zones = await client.get_zones()
        test_zone = zones[0]

        await client.mute_toggle(test_zone.zone_number)
        await asyncio.sleep(0.5)


class TestSourceControl:
    """Test source control commands."""

    async def test_set_source(self, client):
        """Test setting source."""
        zones = await client.get_zones()
        sources = await client.get_sources()

        # Set zone first
        await client.set_zone(zones[0].guid)
        await asyncio.sleep(0.2)

        # Set source
        await client.set_source(sources[0].guid)
        await asyncio.sleep(0.5)


class TestSystemControl:
    """Test system-wide commands."""

    async def test_party_mode(self, client):
        """Test party mode toggle."""
        await client.party_mode_toggle()
        await asyncio.sleep(0.5)

        # Toggle back off
        await client.party_mode_toggle()
        await asyncio.sleep(0.5)

    async def test_all_off(self, client):
        """Test all off command."""
        await client.all_off()
        await asyncio.sleep(0.5)


class TestEventSubscription:
    """Test event subscription system."""

    async def test_receive_events(self, client):
        """Test receiving state change events."""
        events_received = []

        def event_handler(event: StateChangeEvent):
            events_received.append(event)

        # Subscribe to events
        client.subscribe(event_handler)

        # Trigger a state change
        zones = await client.get_zones()
        await client.set_volume(60, zones[0].zone_number)

        # Wait for event
        await asyncio.sleep(1.0)

        # Should have received at least one event
        assert len(events_received) > 0

        # Check event structure
        event = events_received[0]
        assert event.target
        assert event.property
        assert event.value
        assert event.timestamp

        # Cleanup
        client.unsubscribe(event_handler)

    async def test_async_event_handler(self, client):
        """Test async event handler."""
        events_received = []

        async def async_handler(event: StateChangeEvent):
            await asyncio.sleep(0.01)  # Simulate async work
            events_received.append(event)

        client.subscribe(async_handler)

        # Trigger event
        zones = await client.get_zones()
        await client.set_volume(55, zones[0].zone_number)

        await asyncio.sleep(1.0)

        assert len(events_received) > 0

        client.unsubscribe(async_handler)
