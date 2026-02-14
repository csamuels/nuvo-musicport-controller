"""DataUpdateCoordinator for NuVo MusicPort."""

from datetime import timedelta
import logging
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_API_HOST, CONF_API_PORT, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class NuVoCoordinator(DataUpdateCoordinator):
    """NuVo MusicPort data update coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.host = entry.data[CONF_API_HOST]
        self.port = entry.data[CONF_API_PORT]
        self.base_url = f"http://{self.host}:{self.port}/api"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            async with aiohttp.ClientSession() as session:
                # Get zones
                async with session.get(f"{self.base_url}/zones") as resp:
                    zones = await resp.json()

                # Get sources
                async with session.get(f"{self.base_url}/sources") as resp:
                    sources = await resp.json()

                return {"zones": zones, "sources": sources}

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def power_on(self, zone_number: int) -> None:
        """Turn zone on."""
        await self._api_request("POST", f"/zones/{zone_number}/power/on")

    async def power_off(self, zone_number: int) -> None:
        """Turn zone off."""
        await self._api_request("POST", f"/zones/{zone_number}/power/off")

    async def set_volume(self, zone_number: int, volume: int) -> None:
        """Set zone volume."""
        await self._api_request(
            "POST",
            f"/zones/{zone_number}/volume",
            json={"volume": volume}
        )

    async def mute_toggle(self, zone_number: int) -> None:
        """Toggle zone mute."""
        await self._api_request("POST", f"/zones/{zone_number}/mute")

    async def set_source(self, zone_number: int, source_guid: str) -> None:
        """Set zone source."""
        await self._api_request(
            "POST",
            f"/zones/{zone_number}/source",
            json={"source_guid": source_guid}
        )

    async def toggle_party_mode(self) -> None:
        """Toggle party mode."""
        await self._api_request("POST", "/control/partymode")

    async def _api_request(self, method: str, endpoint: str, **kwargs) -> None:
        """Make API request."""
        url = f"{self.base_url}{endpoint}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as resp:
                    resp.raise_for_status()
        except Exception as err:
            _LOGGER.error("API request failed: %s", err)
            raise
