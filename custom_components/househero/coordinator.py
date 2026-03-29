"""Data update coordinator for House Hero."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_HOMES,
    API_INVENTORY,
    API_TICKETS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class HouseHeroCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches all data from the House Hero API."""

    def __init__(self, hass: HomeAssistant, api_url: str) -> None:
        """Initialise the coordinator."""
        self.api_url = api_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def async_close(self) -> None:
        """Close the underlying HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    # ------------------------------------------------------------------
    # Data fetch
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        """Fetch homes, tickets, and inventory from the API."""
        session = self._get_session()
        try:
            homes = await self._fetch(session, API_HOMES)
            tickets = await self._fetch(session, API_TICKETS)
            inventory = await self._fetch(session, API_INVENTORY)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with House Hero API: {err}") from err

        return {
            "homes": homes if isinstance(homes, list) else [],
            "tickets": tickets if isinstance(tickets, list) else [],
            "inventory": inventory if isinstance(inventory, list) else [],
        }

    async def _fetch(self, session: aiohttp.ClientSession, path: str) -> list:
        """Fetch a single endpoint and return the parsed JSON."""
        url = f"{self.api_url}{path}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            return await resp.json()
