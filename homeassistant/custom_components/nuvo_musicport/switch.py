"""Switch platform for NuVo MusicPort."""

import logging

from homeassistant.components.switch import SwitchEntity
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
    """Set up NuVo switch entities."""
    coordinator: NuVoCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [NuVoPartyModeSwitch(coordinator)]

    async_add_entities(entities)


class NuVoPartyModeSwitch(CoordinatorEntity, SwitchEntity):
    """Party mode switch."""

    def __init__(self, coordinator: NuVoCoordinator) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = "nuvo_party_mode"
        self._attr_name = "Party Mode"
        self._attr_icon = "mdi:party-popper"

    @property
    def is_on(self) -> bool:
        """Return if party mode is on."""
        zones = self.coordinator.data.get("zones", [])
        # Party mode is on if any zone reports party mode active
        return any(z.get("party_mode") not in ["Off", ""] for z in zones)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn party mode on."""
        if not self.is_on:
            await self.coordinator.toggle_party_mode()
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn party mode off."""
        if self.is_on:
            await self.coordinator.toggle_party_mode()
            await self.coordinator.async_request_refresh()
