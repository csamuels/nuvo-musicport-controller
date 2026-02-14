"""Media player platform for NuVo MusicPort."""

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NuVoCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NuVo media player entities."""
    coordinator: NuVoCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        NuVoZone(coordinator, zone)
        for zone in coordinator.data["zones"]
    ]

    async_add_entities(entities)


class NuVoZone(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a NuVo zone."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, coordinator: NuVoCoordinator, zone: dict) -> None:
        """Initialize the zone."""
        super().__init__(coordinator)
        self._zone_number = zone["zone_number"]
        self._attr_unique_id = f"nuvo_zone_{self._zone_number}"
        self._attr_name = zone["name"]

    @property
    def zone_data(self) -> dict:
        """Get current zone data from coordinator."""
        zones = self.coordinator.data.get("zones", [])
        return next(
            (z for z in zones if z["zone_number"] == self._zone_number),
            {}
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the zone."""
        if self.zone_data.get("is_on"):
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float:
        """Volume level (0..1)."""
        volume = self.zone_data.get("volume", 0)
        max_volume = self.zone_data.get("max_volume", 79)
        return volume / max_volume

    @property
    def is_volume_muted(self) -> bool:
        """Return if volume is muted."""
        return self.zone_data.get("mute", False)

    @property
    def source(self) -> str:
        """Return the current source."""
        return self.zone_data.get("source_name", "")

    @property
    def source_list(self) -> list[str]:
        """List of available sources."""
        sources = self.coordinator.data.get("sources", [])
        return [s["name"] for s in sources]

    async def async_turn_on(self) -> None:
        """Turn the zone on."""
        await self.coordinator.power_on(self._zone_number)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the zone off."""
        await self.coordinator.power_off(self._zone_number)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level (0..1)."""
        max_volume = self.zone_data.get("max_volume", 79)
        nuvo_volume = int(volume * max_volume)
        await self.coordinator.set_volume(self._zone_number, nuvo_volume)
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        """Volume up."""
        current = self.zone_data.get("volume", 0)
        max_volume = self.zone_data.get("max_volume", 79)
        new_volume = min(current + 5, max_volume)
        await self.coordinator.set_volume(self._zone_number, new_volume)
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        """Volume down."""
        current = self.zone_data.get("volume", 0)
        new_volume = max(current - 5, 0)
        await self.coordinator.set_volume(self._zone_number, new_volume)
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await self.coordinator.mute_toggle(self._zone_number)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        """Select source."""
        sources = self.coordinator.data.get("sources", [])
        source_data = next((s for s in sources if s["name"] == source), None)

        if source_data:
            await self.coordinator.set_source(self._zone_number, source_data["guid"])
            await self.coordinator.async_request_refresh()
