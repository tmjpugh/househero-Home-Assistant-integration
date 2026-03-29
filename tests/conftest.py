"""Shared fixtures for House Hero tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

MOCK_HOMES = [
    {"id": 1, "name": "My Home", "address": "123 Main St"},
]

MOCK_TICKETS = [
    # Status variety
    {"id": 1, "home_id": 1, "title": "Fix roof", "status": "open", "priority": "high"},
    {"id": 2, "home_id": 1, "title": "Paint walls", "status": "open", "priority": "medium"},
    {"id": 3, "home_id": 1, "title": "Replace filter", "status": "in-progress", "priority": "low"},
    {"id": 4, "home_id": 1, "title": "Old task", "status": "closed", "priority": "low"},
    {"id": 5, "home_id": 1, "title": "Waiting on part", "status": "waiting", "priority": "medium"},
]

MOCK_INVENTORY = [
    {"id": 1, "home_id": 1, "name": "HVAC", "type": "appliance"},
    {"id": 2, "home_id": 1, "name": "Water Heater", "type": "appliance"},
]

MOCK_API_DATA = {
    "homes": MOCK_HOMES,
    "tickets": MOCK_TICKETS,
    "inventory": MOCK_INVENTORY,
}


@pytest.fixture
def mock_coordinator_data():
    """Return mock API data."""
    return MOCK_API_DATA
