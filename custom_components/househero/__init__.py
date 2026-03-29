"""House Hero Home Assistant Integration."""
from __future__ import annotations

import logging

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    API_TICKETS,
    CONF_API_URL,
    CONF_HOME_ID,
    DOMAIN,
    SERVICE_CREATE_TICKET,
    TICKET_PRIORITY_HIGH,
    TICKET_PRIORITY_LOW,
    TICKET_PRIORITY_MEDIUM,
)
from .coordinator import HouseHeroCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

CREATE_TICKET_SCHEMA = vol.Schema(
    {
        vol.Required("title"): cv.string,
        vol.Required("room"): cv.string,
        vol.Optional("priority", default=TICKET_PRIORITY_MEDIUM): vol.In(
            [TICKET_PRIORITY_LOW, TICKET_PRIORITY_MEDIUM, TICKET_PRIORITY_HIGH]
        ),
        vol.Optional("type", default="maintenance"): cv.string,
        vol.Optional("requester", default="Home Assistant"): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up House Hero from a config entry."""
    api_url = entry.data[CONF_API_URL]
    home_id: int = entry.data[CONF_HOME_ID]
    coordinator = HouseHeroCoordinator(hass, api_url, home_id)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register create_ticket service (only once; the handler resolves the
    # right coordinator at call time via the entry_id in the service data or
    # by falling back to the single configured entry)
    if not hass.services.has_service(DOMAIN, SERVICE_CREATE_TICKET):

        async def handle_create_ticket(call: ServiceCall) -> None:
            """Handle the create_ticket service call."""
            coordinators: dict[str, HouseHeroCoordinator] = hass.data[DOMAIN]
            if not coordinators:
                raise HomeAssistantError(
                    "No House Hero entries are loaded. Please check your configuration."
                )

            # With multiple entries (one per home) pick the right coordinator.
            # If only one entry exists, use it automatically.
            # If multiple entries exist the caller must pass the target entry_id.
            entry_id: str | None = call.data.get("entry_id")
            if entry_id:
                coordinator_instance = coordinators.get(entry_id)
                if coordinator_instance is None:
                    raise HomeAssistantError(
                        f"No House Hero entry found for entry_id '{entry_id}'."
                    )
            elif len(coordinators) == 1:
                coordinator_instance = next(iter(coordinators.values()))
            else:
                raise HomeAssistantError(
                    "Multiple House Hero homes are configured. Specify which home to "
                    "use by passing the 'entry_id' field in the service call."
                )

            session = coordinator_instance._get_session()
            api_base = coordinator_instance.api_url
            home_id = coordinator_instance.home_id

            payload = {
                "home_id": home_id,
                "title": call.data["title"],
                "room": call.data["room"],
                "priority": call.data.get("priority", TICKET_PRIORITY_MEDIUM),
                "type": call.data.get("type", "maintenance"),
                "requester": call.data.get("requester", "Home Assistant"),
            }

            url = f"{api_base}{API_TICKETS}"
            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status not in (200, 201):
                        body = await resp.text()
                        raise HomeAssistantError(
                            f"House Hero API returned {resp.status}: {body}"
                        )
                    ticket = await resp.json()
                    _LOGGER.info(
                        "Created House Hero ticket #%s: %s",
                        ticket.get("ticket_number"),
                        ticket.get("title"),
                    )
            except aiohttp.ClientError as err:
                raise HomeAssistantError(
                    f"Failed to reach House Hero API: {err}"
                ) from err

            # Refresh coordinator so sensors reflect the new ticket immediately
            await coordinator_instance.async_request_refresh()

        hass.services.async_register(
            DOMAIN,
            SERVICE_CREATE_TICKET,
            handle_create_ticket,
            schema=CREATE_TICKET_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: HouseHeroCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()

        # Remove the service when the last entry is unloaded
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_CREATE_TICKET)

    return unload_ok
