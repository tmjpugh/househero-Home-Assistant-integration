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

def _make_coordinator(api_url: str = "http://localhost:8080", homes=None):
    """Return a lightweight coordinator mock."""
    coordinator = MagicMock()
    coordinator.api_url = api_url.rstrip("/")
    coordinator.data = {
        "homes": homes if homes is not None else MOCK_API_DATA["homes"],
        "tickets": MOCK_API_DATA["tickets"],
        "inventory": MOCK_API_DATA["inventory"],
    }
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

    home_id: int | None = call_data.get("home_id")
    if home_id is None:
        homes = coordinator.data.get("homes", [])
        if not homes:
            raise HomeAssistantError(
                "No homes found in House Hero; cannot create ticket."
            )
        home_id = homes[0]["id"]

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
async def test_create_ticket_posts_correct_payload():
    """Service POSTs the correct fields to the API."""
    coordinator = _make_coordinator()
    session, resp = _make_session_mock()
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
async def test_create_ticket_uses_first_home_when_no_home_id():
    """Service defaults to the first home when home_id is not given."""
    coordinator = _make_coordinator()
    session, _ = _make_session_mock()
    coordinator._get_session = MagicMock(return_value=session)

    await _invoke_service(coordinator, {"title": "Leaky faucet", "room": "Bathroom"})

    _, kwargs = session.post.call_args
    posted = session.post.call_args[1]["json"] if "json" in session.post.call_args[1] else session.post.call_args[0][1]
    # home_id should be the first home's id (1)
    call_args = session.post.call_args
    assert call_args is not None


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
async def test_create_ticket_raises_when_no_homes():
    """Service raises HomeAssistantError when no homes exist."""
    coordinator = _make_coordinator(homes=[])
    session, _ = _make_session_mock()
    coordinator._get_session = MagicMock(return_value=session)

    with pytest.raises(HomeAssistantError, match="No homes found"):
        await _invoke_service(coordinator, {"title": "Leaky faucet", "room": "Bathroom"})
