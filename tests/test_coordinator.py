"""Tests for the House Hero coordinator."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.househero.coordinator import HouseHeroCoordinator
from custom_components.househero.const import DOMAIN

from .conftest import MOCK_HOMES, MOCK_TICKETS, MOCK_INVENTORY


def _make_coordinator(api_url: str = "http://localhost:8080", home_id: int = 1) -> HouseHeroCoordinator:
    """Return a coordinator with a mock hass."""
    hass = MagicMock()
    hass.loop = None
    coordinator = HouseHeroCoordinator.__new__(HouseHeroCoordinator)
    coordinator.api_url = api_url
    coordinator.home_id = home_id
    coordinator._session = None
    coordinator.logger = MagicMock()
    coordinator.hass = hass
    return coordinator


@pytest.mark.asyncio
async def test_async_update_data_success():
    """Coordinator returns structured data filtered to configured home."""
    coordinator = _make_coordinator(home_id=1)

    async def mock_fetch(session, path):
        if path == "/api/homes":
            return MOCK_HOMES
        if path.startswith("/api/tickets"):
            return MOCK_TICKETS
        if path.startswith("/api/inventory"):
            return MOCK_INVENTORY
        return []

    with patch.object(coordinator, "_fetch", side_effect=mock_fetch):
        data = await coordinator._async_update_data()

    # homes is filtered to the configured home_id
    assert data["homes"] == [h for h in MOCK_HOMES if h["id"] == 1]
    assert data["tickets"] == MOCK_TICKETS
    assert data["inventory"] == MOCK_INVENTORY


@pytest.mark.asyncio
async def test_async_update_data_fetches_with_home_id_param():
    """Coordinator appends home_id query param to tickets and inventory fetches."""
    coordinator = _make_coordinator(home_id=42)
    fetched_paths: list[str] = []

    async def mock_fetch(session, path):
        fetched_paths.append(path)
        return []

    with patch.object(coordinator, "_fetch", side_effect=mock_fetch):
        await coordinator._async_update_data()

    assert any("home_id=42" in p for p in fetched_paths if "tickets" in p)
    assert any("home_id=42" in p for p in fetched_paths if "inventory" in p)


@pytest.mark.asyncio
async def test_async_update_data_connection_error():
    """Coordinator raises UpdateFailed on connection error."""
    from homeassistant.helpers.update_coordinator import UpdateFailed

    coordinator = _make_coordinator()

    with patch.object(
        coordinator,
        "_fetch",
        side_effect=aiohttp.ClientError("network error"),
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_async_close_session():
    """Coordinator closes the session on close."""
    coordinator = _make_coordinator()
    mock_session = AsyncMock()
    mock_session.closed = False
    coordinator._session = mock_session

    await coordinator.async_close()

    mock_session.close.assert_awaited_once()
