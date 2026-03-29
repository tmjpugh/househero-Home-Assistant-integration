"""Tests for the House Hero config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.househero.config_flow import HouseHeroConfigFlow
from custom_components.househero.const import CONF_API_URL, DOMAIN


def _make_flow() -> HouseHeroConfigFlow:
    """Create a HouseHeroConfigFlow with all HA infrastructure mocked out."""
    flow = HouseHeroConfigFlow()
    # Build a minimal hass mock that satisfies async_set_unique_id internals
    flow.hass = MagicMock()
    flow.hass.config_entries.flow.async_progress_by_handler.return_value = []
    flow.hass.config_entries.async_entries.return_value = []
    # Return None so _abort_if_unique_id_configured doesn't raise AbortFlow
    flow.hass.config_entries.async_entry_for_domain_unique_id.return_value = None
    flow.context = {}
    flow.flow_id = "test-flow-id"
    return flow


@pytest.mark.asyncio
async def test_user_step_success():
    """Test successful configuration with a valid API URL."""
    flow = _make_flow()

    with patch(
        "custom_components.househero.config_flow._validate_api_url",
        new=AsyncMock(return_value=None),
    ):
        result = await flow.async_step_user(
            user_input={CONF_API_URL: "http://localhost:8080"}
        )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_API_URL] == "http://localhost:8080"


@pytest.mark.asyncio
async def test_user_step_cannot_connect():
    """Test that a connection error surfaces the correct error key."""
    import aiohttp

    flow = _make_flow()

    with patch(
        "custom_components.househero.config_flow._validate_api_url",
        new=AsyncMock(side_effect=aiohttp.ClientError("boom")),
    ):
        result = await flow.async_step_user(
            user_input={CONF_API_URL: "http://bad-host:8080"}
        )

    assert result["type"] == "form"
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_user_step_shows_form_when_no_input():
    """Test that the form is shown when no input is provided."""
    flow = _make_flow()
    result = await flow.async_step_user(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"
