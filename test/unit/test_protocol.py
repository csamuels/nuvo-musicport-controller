"""Unit tests for protocol parsing."""

import pytest
from nuvo_sdk.protocol import (
    build_command,
    parse_zones_xml,
    parse_sources_xml,
    parse_state_changed,
    parse_report_state,
    update_zones_from_status,
)
from nuvo_sdk.models import Zone
from nuvo_sdk.exceptions import ProtocolError


class TestBuildCommand:
    """Test command building."""

    def test_adds_carriage_return(self):
        """Test that \r is added if missing."""
        result = build_command("BrowseZones")
        assert result == b"BrowseZones\r"

    def test_preserves_existing_carriage_return(self):
        """Test that existing \r is not duplicated."""
        result = build_command("BrowseZones\r")
        assert result == b"BrowseZones\r"

    def test_with_parameters(self):
        """Test command with parameters."""
        result = build_command("Power On 1")
        assert result == b"Power On 1\r"


class TestParseZonesXml:
    """Test zone XML parsing."""

    @pytest.fixture
    def zones_xml(self):
        """Sample zones XML from captured data."""
        return '''<Zones total="6" more="false">
            <Zone guid="00010000-84e4-4cf5-b0bc-ab828737ac30"
                  name="Master Bedroom"
                  dna="name"
                  id="Zone_1"
                  isOn="False"
                  sourceId="0"
                  sourceName=""
                  gId="00000001-0000-0000-0000-000000000000"
                  gName="ZG_1"
                  gPwr="0"
                  gVol="0"
                  gSrc="0"
                  sId="0"
                  sGuid="00000000-0000-0000-0000-000000000000"
                  m1="" m2="" m3="" m4="" mArt="" />
            <Zone guid="00030000-84e4-4cf5-b0bc-ab828737ac30"
                  name="Living Room"
                  dna="name"
                  id="Zone_3"
                  isOn="True"
                  sourceId="5"
                  sourceName="Source 5"
                  gId="00000000-0005-0000-0000-000000000000"
                  gName="ZG_3"
                  gPwr="0"
                  gVol="0"
                  gSrc="0"
                  sId="5"
                  sGuid="00000005-84e4-4cf5-b0bc-ab828737ac30"
                  m1="" m2="" m3="Source 5" m4="" mArt="" />
        </Zones>'''

    def test_parse_basic_zones(self, zones_xml):
        """Test parsing zone XML."""
        zones = parse_zones_xml(zones_xml)

        assert len(zones) == 2
        assert zones[0].name == "Master Bedroom"
        assert zones[0].zone_number == 1
        assert zones[0].is_on is False
        assert zones[1].name == "Living Room"
        assert zones[1].zone_number == 3
        assert zones[1].is_on is True

    def test_parse_invalid_xml(self):
        """Test error handling for invalid XML."""
        with pytest.raises(ProtocolError):
            parse_zones_xml("<Zones>invalid</Zones")  # Missing closing >


class TestParseSourcesXml:
    """Test source XML parsing."""

    @pytest.fixture
    def sources_xml(self):
        """Sample sources XML from captured data."""
        return '''<Sources total="6" more="false">
            <Source guid="00000001-84e4-4cf5-b0bc-ab828737ac30"
                    name="Music Server A"
                    dna="name"
                    smart="1"
                    nnet="0"
                    znCount="0"
                    znList=""
                    sId="1"
                    sGuid="00000001-84e4-4cf5-b0bc-ab828737ac30"
                    m1="Ready" m2="" m3="" m4="" mArt="" />
            <Source guid="00000005-84e4-4cf5-b0bc-ab828737ac30"
                    name="Source 5"
                    dna="name"
                    smart="0"
                    nnet="1"
                    znCount="1"
                    znList="Living Room"
                    sId="5"
                    sGuid="00000005-84e4-4cf5-b0bc-ab828737ac30"
                    m1="" m2="" m3="Source 5" m4="" mArt="" />
        </Sources>'''

    def test_parse_basic_sources(self, sources_xml):
        """Test parsing source XML."""
        sources = parse_sources_xml(sources_xml)

        assert len(sources) == 2
        assert sources[0].name == "Music Server A"
        assert sources[0].source_id == 1
        assert sources[0].is_smart is True
        assert sources[0].is_network is False
        assert sources[1].name == "Source 5"
        assert sources[1].source_id == 5
        assert sources[1].is_smart is False
        assert sources[1].is_network is True
        assert sources[1].zone_count == 1


class TestParseStateChanged:
    """Test StateChanged event parsing."""

    def test_parse_volume_change(self):
        """Test parsing volume change event."""
        event = parse_state_changed("StateChanged Zone_2 Volume=50")

        assert event is not None
        assert event.target == "Zone_2"
        assert event.property == "Volume"
        assert event.value == "50"

    def test_parse_power_change(self):
        """Test parsing power state change."""
        event = parse_state_changed("StateChanged Zone_3 PowerOn=True")

        assert event is not None
        assert event.target == "Zone_3"
        assert event.property == "PowerOn"
        assert event.value == "True"

    def test_parse_zone_group_change(self):
        """Test parsing zone group change."""
        event = parse_state_changed("StateChanged ZG_1 Volume=79")

        assert event is not None
        assert event.target == "ZG_1"
        assert event.property == "Volume"
        assert event.value == "79"

    def test_parse_invalid_format(self):
        """Test handling of invalid format."""
        event = parse_state_changed("SomeOtherEvent Zone_1")
        assert event is None


class TestParseReportState:
    """Test ReportState parsing."""

    def test_parse_basic_report(self):
        """Test parsing ReportState line."""
        result = parse_report_state("ReportState Zone_1 Volume=79")

        assert result is not None
        target, prop, value = result
        assert target == "Zone_1"
        assert prop == "Volume"
        assert value == "79"

    def test_parse_boolean_value(self):
        """Test parsing boolean ReportState."""
        result = parse_report_state("ReportState Zone_3 PowerOn=True")

        assert result is not None
        target, prop, value = result
        assert target == "Zone_3"
        assert prop == "PowerOn"
        assert value == "True"


class TestUpdateZonesFromStatus:
    """Test updating zones from GetStatus."""

    def test_update_zone_properties(self):
        """Test that zone properties are updated correctly."""
        zone = Zone(
            guid="00010000-84e4-4cf5-b0bc-ab828737ac30",
            name="Master Bedroom",
            zone_id="Zone_1",
            zone_number=1,
            is_on=False,
            volume=0,
            mute=False,
            source_id=0,
            source_name="",
            source_guid="",
            party_mode="Off",
            max_volume=79,
            min_volume=0,
            zone_group_name="ZG_1",
            zone_group_id="",
        )

        status_lines = [
            "ReportState Zone_1 Volume=65",
            "ReportState Zone_1 PowerOn=True",
            "ReportState Zone_1 Mute=True",
            "ReportState Zone_1 PartyMode=On",
        ]

        update_zones_from_status([zone], status_lines)

        assert zone.volume == 65
        assert zone.is_on is True
        assert zone.mute is True
        assert zone.party_mode == "On"
