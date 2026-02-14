"""Protocol parser for NuVo MusicPort MRAD protocol."""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from .models import Zone, Source, StateChangeEvent
from .exceptions import ProtocolError


def build_command(command: str) -> bytes:
    """
    Build a command string with proper line ending.

    Args:
        command: Command string (e.g., "BrowseZones", "Power On 1")

    Returns:
        Command as bytes with \r line ending
    """
    if not command.endswith("\r"):
        command += "\r"
    return command.encode("utf-8")


def parse_zones_xml(xml_data: str) -> List[Zone]:
    """
    Parse BrowseZones XML response into Zone objects.

    Args:
        xml_data: XML string from BrowseZones command

    Returns:
        List of Zone objects

    Raises:
        ProtocolError: If XML parsing fails
    """
    try:
        root = ET.fromstring(xml_data)
        zones = []

        for zone_elem in root.findall("Zone"):
            # Parse boolean values
            is_on = zone_elem.get("isOn", "False") == "True"
            mute = False  # Will be set from GetStatus
            do_not_disturb = False
            is_locked = False

            zone = Zone(
                guid=zone_elem.get("guid", ""),
                name=zone_elem.get("name", ""),
                zone_id=zone_elem.get("id", ""),
                zone_number=int(zone_elem.get("id", "Zone_0").split("_")[1]),
                is_on=is_on,
                volume=0,  # Will be set from GetStatus
                mute=mute,
                source_id=int(zone_elem.get("sourceId", "0")),
                source_name=zone_elem.get("sourceName", ""),
                source_guid=zone_elem.get("sGuid", ""),
                party_mode="Off",  # Will be set from GetStatus
                max_volume=79,  # Default, will be set from GetStatus
                min_volume=0,
                zone_group_name=zone_elem.get("gName", ""),
                zone_group_id=zone_elem.get("gId", ""),
                do_not_disturb=do_not_disturb,
                is_locked=is_locked,
            )
            zones.append(zone)

        return zones

    except ET.ParseError as e:
        raise ProtocolError(f"Failed to parse zones XML: {e}")
    except (ValueError, KeyError, IndexError) as e:
        raise ProtocolError(f"Invalid zone data in XML: {e}")


def parse_sources_xml(xml_data: str) -> List[Source]:
    """
    Parse BrowseSources XML response into Source objects.

    Args:
        xml_data: XML string from BrowseSources command

    Returns:
        List of Source objects

    Raises:
        ProtocolError: If XML parsing fails
    """
    try:
        root = ET.fromstring(xml_data)
        sources = []

        for source_elem in root.findall("Source"):
            source = Source(
                guid=source_elem.get("guid", ""),
                name=source_elem.get("name", ""),
                source_id=int(source_elem.get("sId", "0")),
                is_smart=source_elem.get("smart", "0") == "1",
                is_network=source_elem.get("nnet", "0") == "1",
                zone_count=int(source_elem.get("znCount", "0")),
                zone_list=source_elem.get("znList", ""),
                metadata1=source_elem.get("m1", ""),
                metadata2=source_elem.get("m2", ""),
                metadata3=source_elem.get("m3", ""),
                metadata4=source_elem.get("m4", ""),
                metadata_art=source_elem.get("mArt", ""),
            )
            sources.append(source)

        return sources

    except ET.ParseError as e:
        raise ProtocolError(f"Failed to parse sources XML: {e}")
    except (ValueError, KeyError) as e:
        raise ProtocolError(f"Invalid source data in XML: {e}")


def parse_state_changed(line: str) -> Optional[StateChangeEvent]:
    """
    Parse a StateChanged event line.

    Format examples:
        "StateChanged Zone_2 Volume=50"
        "StateChanged Zone_3 PowerOn=True"
        "StateChanged ZG_1 Volume=79"

    Args:
        line: StateChanged line from device

    Returns:
        StateChangeEvent object or None if not a state change
    """
    # Match pattern: "StateChanged <target> <property>=<value>"
    match = re.match(r"StateChanged\s+(\S+)\s+(\S+)=(.+)", line.strip())
    if not match:
        return None

    target, property_name, value = match.groups()

    return StateChangeEvent(
        target=target,
        property=property_name,
        value=value.strip(),
    )


def parse_report_state(line: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a ReportState line from GetStatus.

    Format: "ReportState <target> <property>=<value>"

    Args:
        line: ReportState line

    Returns:
        Tuple of (target, property, value) or None
    """
    match = re.match(r"ReportState\s+(\S+)\s+(\S+)=(.+)", line.strip())
    if not match:
        return None

    target, property_name, value = match.groups()
    return target, property_name, value.strip()


def update_zones_from_status(zones: List[Zone], status_lines: List[str]) -> None:
    """
    Update zone objects with data from GetStatus ReportState lines.

    Args:
        zones: List of Zone objects to update
        status_lines: List of ReportState lines
    """
    # Create lookup by zone_id
    zone_map = {z.zone_id: z for z in zones}

    for line in status_lines:
        parsed = parse_report_state(line)
        if not parsed:
            continue

        target, prop, value = parsed

        # Update zone properties
        if target in zone_map:
            zone = zone_map[target]
            try:
                if prop == "Volume":
                    zone.volume = int(value)
                elif prop == "PowerOn":
                    zone.is_on = value == "True"
                elif prop == "Mute":
                    zone.mute = value == "True"
                elif prop == "PartyMode":
                    zone.party_mode = value
                elif prop == "MaxVolume":
                    zone.max_volume = int(value)
                elif prop == "MinVolume":
                    zone.min_volume = int(value)
                elif prop == "DoNotDisturb":
                    zone.do_not_disturb = value == "True"
            except (ValueError, AttributeError):
                pass  # Skip invalid values


def parse_system_properties(status_lines: List[str]) -> Dict[str, str]:
    """
    Parse system-level properties from GetStatus.

    Args:
        status_lines: List of ReportState lines

    Returns:
        Dictionary of system properties
    """
    system_props = {}

    for line in status_lines:
        parsed = parse_report_state(line)
        if not parsed:
            continue

        target, prop, value = parsed

        # System properties (target is device name like "NV-I8G")
        if target.startswith("NV-"):
            system_props[prop] = value

    return system_props
