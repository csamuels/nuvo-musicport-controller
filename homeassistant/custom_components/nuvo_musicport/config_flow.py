"""Config flow for NuVo MusicPort integration."""

from typing import Any
import voluptuous as vol
import aiohttp

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_API_HOST, CONF_API_PORT, DEFAULT_API_PORT


async def validate_connection(hass: HomeAssistant, host: str, port: int) -> dict[str, Any]:
    """Validate the API connection."""
    url = f"http://{host}:{port}/health"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"title": "NuVo MusicPort", "device": data.get("device")}
    except Exception as err:
        raise ConnectionError(f"Cannot connect to {url}: {err}")


class NuVoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NuVo MusicPort."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""

        errors = {}

        if user_input is not None:
            try:
                info = await validate_connection(
                    self.hass,
                    user_input[CONF_API_HOST],
                    user_input[CONF_API_PORT],
                )

                await self.async_set_unique_id(user_input[CONF_API_HOST])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_HOST, default="10.0.0.45"): cv.string,
                vol.Required(CONF_API_PORT, default=DEFAULT_API_PORT): cv.port,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
