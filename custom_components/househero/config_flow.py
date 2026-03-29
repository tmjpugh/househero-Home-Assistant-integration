"""Config flow for House Hero."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_API_URL, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, description={"suggested_value": "http://192.168.1.100:8080"}): str,
    }
)


async def _validate_api_url(hass: HomeAssistant, api_url: str) -> None:
    """Try to reach the House Hero API and raise if unreachable."""
    url = api_url.rstrip("/") + "/api/homes"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()


class HouseHeroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for House Hero."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL].rstrip("/")

            # Prevent duplicate entries for the same URL
            await self.async_set_unique_id(api_url)
            self._abort_if_unique_id_configured()

            try:
                await _validate_api_url(self.hass, api_url)
            except aiohttp.ClientResponseError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="House Hero",
                    data={CONF_API_URL: api_url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
