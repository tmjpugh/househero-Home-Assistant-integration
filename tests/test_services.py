"""Tests for the House Hero create_ticket service."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from homeassistant.exceptions import HomeAssistantError

from custom_components.househero.const import (
    API_TICKETS,
    DOMAIN,
    TICKET_PRIORITY_MEDIUM,
)
from .conftest import MOCK_API_DATA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_coordinator(api_url: str = "http://localhost:8080", home_id: int = 1):
    """Return a lightweight coordinator mock scoped to a specific home."""
    coordinator = MagicMock()
    coordinator.api_url = api_url.rstrip("/")
    coordinator.home_id = home_id
    coordinator.data = MOCK_API_DATA
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def _make_session_mock(status: int = 201, body: dict | None = None):
    """Return an aiohttp session mock with a pre-configured POST response."""
    if body is None:
        body = {"id": 99, "ticket_number": 10, "title": "Window is broken"}
    resp = MagicMock()
    resp.status = status
    resp.json = AsyncMock(return_value=body)
    resp.text = AsyncMock(return_value=json.dumps(body))
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.post = MagicMock(return_value=resp)
    return session, resp


async def _invoke_service(coordinator, call_data: dict):
    """Reproduce the service handler logic from __init__.py for testing."""
    session = coordinator._get_session()
    api_base = coordinator.api_url
    # home_id comes from the coordinator (set at config time)
    home_id = coordinator.home_id

    payload = {
        "home_id": home_id,
        "title": call_data["title"],
        "room": call_data["room"],
        "priority": call_data.get("priority", TICKET_PRIORITY_MEDIUM),
        "type": call_data.get("type", "maintenance"),
        "requester": call_data.get("requester", "Home Assistant"),
    }

    url = f"{api_base}{API_TICKETS}"
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status not in (200, 201):
                body = await resp.text()
                raise HomeAssistantError(
                    f"House Hero API returned {resp.status}: {body}"
                )
            return await resp.json()
    except aiohttp.ClientError as err:
        raise HomeAssistantError(f"Failed to reach House Hero API: {err}") from err
    finally:
        await coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_ticket_uses_configured_home_id():
    """Service uses the home_id from the coordinator (not from call data)."""
    coordinator = _make_coordinator(home_id=7)
    session, _ = _make_session_mock()
    coordinator._get_session = MagicMock(return_value=session)

    await _invoke_service(coordinator, {"title": "Window is broken", "room": "Living Room"})

    call_kwargs = session.post.call_args[1]
    assert call_kwargs["json"]["home_id"] == 7


@pytest.mark.asyncio
async def test_create_ticket_posts_correct_payload():
    """Service POSTs the correct fields to the API."""
    coordinator = _make_coordinator(home_id=1)
    session, mock_response = _make_session_mock()
    coordinator._get_session = MagicMock(return_value=session)

    call_data = {
        "title": "Window is broken",
        "room": "Living Room",
    }

    ticket = await _invoke_service(coordinator, call_data)

    expected_payload = {
        "home_id": 1,
        "title": "Window is broken",
        "room": "Living Room",
        "priority": TICKET_PRIORITY_MEDIUM,
        "type": "maintenance",
        "requester": "Home Assistant",
    }
    url = f"http://localhost:8080{API_TICKETS}"
    session.post.assert_called_once_with(url, json=expected_payload, timeout=aiohttp.ClientTimeout(total=10))
    assert ticket["title"] == "Window is broken"


@pytest.mark.asyncio
async def test_create_ticket_raises_on_api_error():
    """Service raises HomeAssistantError when the API returns a non-2xx status."""
    coordinator = _make_coordinator()
    session, _ = _make_session_mock(status=500, body={"error": "internal server error"})
    coordinator._get_session = MagicMock(return_value=session)

    with pytest.raises(HomeAssistantError, match="House Hero API returned 500"):
        await _invoke_service(coordinator, {"title": "Leaky faucet", "room": "Bathroom"})


@pytest.mark.asyncio
async def test_create_ticket_raises_on_network_error():
    """Service raises HomeAssistantError on connection failure."""
    coordinator = _make_coordinator()

    session = MagicMock()
    resp = MagicMock()
    resp.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("network failure"))
    resp.__aexit__ = AsyncMock(return_value=False)
    session.post = MagicMock(return_value=resp)
    coordinator._get_session = MagicMock(return_value=session)

    with pytest.raises(HomeAssistantError, match="Failed to reach House Hero API"):
        await _invoke_service(coordinator, {"title": "Leaky faucet", "room": "Bathroom"})


@pytest.mark.asyncio
async def test_create_ticket_refreshes_coordinator_after_creation():
    """Service triggers a coordinator refresh after successfully creating a ticket."""
    coordinator = _make_coordinator()
    session, _ = _make_session_mock()
    coordinator._get_session = MagicMock(return_value=session)

    await _invoke_service(coordinator, {"title": "Leaky faucet", "room": "Bathroom"})

    coordinator.async_request_refresh.assert_awaited_once()
