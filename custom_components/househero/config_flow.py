"""Config flow for House Hero."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_API_URL, CONF_HOME_ID, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_URL, description={"suggested_value": "http://192.168.1.100:8080"}): str,
        vol.Required(CONF_HOME_ID): vol.Coerce(int),
    }
)


async def _validate_connection(hass: HomeAssistant, api_url: str, home_id: int) -> None:
    """Verify the House Hero API is reachable and the home_id exists."""
    base = api_url.rstrip("/")
    async with aiohttp.ClientSession() as session:
        # Validate the base URL is reachable
        async with session.get(
            f"{base}/api/homes", timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            resp.raise_for_status()
            homes = await resp.json()

    # Confirm the requested home_id is present in the returned list
    home_ids = [h.get("id") for h in homes if isinstance(h, dict)]
    if home_id not in home_ids:
        raise HomeNotFoundError(f"Home {home_id} not found on this House Hero server")


class HomeNotFoundError(Exception):
    """Raised when the configured home_id does not exist on the server."""


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
            home_id: int = user_input[CONF_HOME_ID]

            # Each (server, home) pair is its own unique entry
            await self.async_set_unique_id(f"{api_url}_{home_id}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_connection(self.hass, api_url, home_id)
            except HomeNotFoundError:
                errors["base"] = "home_not_found"
            except aiohttp.ClientResponseError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"House Hero (Home {home_id})",
                    data={CONF_API_URL: api_url, CONF_HOME_ID: home_id},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
