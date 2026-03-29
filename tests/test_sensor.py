"""Tests for House Hero sensor entities."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.househero.sensor import (
    HouseHeroSensor,
    SENSOR_TYPES,
    _count_tickets,
)
from custom_components.househero.const import DOMAIN

from .conftest import MOCK_API_DATA


def _make_sensor(description, home_id=1, home_name="My Home"):
    coordinator = MagicMock()
    coordinator.data = MOCK_API_DATA
    sensor = HouseHeroSensor.__new__(HouseHeroSensor)
    sensor.coordinator = coordinator
    sensor.entity_description = description
    sensor._home_id = home_id
    sensor._home_name = home_name
    sensor._attr_unique_id = f"{DOMAIN}_{home_id}_{description.key}"
    return sensor


# ---- Status sensors ----

def test_open_tickets_count():
    """Open tickets sensor counts only open tickets for the home."""
    desc = next(d for d in SENSOR_TYPES if d.key == "open_tickets")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 2  # tickets 1 and 2


def test_in_progress_tickets_count():
    """In-progress sensor counts in-progress tickets."""
    desc = next(d for d in SENSOR_TYPES if d.key == "in_progress_tickets")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 1  # ticket 3


def test_waiting_tickets_count():
    """Waiting sensor counts waiting tickets."""
    desc = next(d for d in SENSOR_TYPES if d.key == "waiting_tickets")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 1  # ticket 5


def test_closed_tickets_count():
    """Closed tickets sensor counts closed tickets."""
    desc = next(d for d in SENSOR_TYPES if d.key == "closed_tickets")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 1  # ticket 4


# ---- Priority sensors ----

def test_high_priority_tickets_count():
    """High priority sensor counts only high-priority tickets."""
    desc = next(d for d in SENSOR_TYPES if d.key == "high_priority_tickets")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 1  # ticket 1


def test_medium_priority_tickets_count():
    """Medium priority sensor counts medium-priority tickets."""
    desc = next(d for d in SENSOR_TYPES if d.key == "medium_priority_tickets")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 2  # tickets 2 and 5


def test_low_priority_tickets_count():
    """Low priority sensor counts low-priority tickets."""
    desc = next(d for d in SENSOR_TYPES if d.key == "low_priority_tickets")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 2  # tickets 3 and 4


# ---- Inventory sensor ----

def test_inventory_items_count():
    """Inventory sensor counts items for the home."""
    desc = next(d for d in SENSOR_TYPES if d.key == "inventory_items")
    sensor = _make_sensor(desc)
    assert sensor.native_value == 2  # items 1 and 2


# ---- Edge cases ----

def test_sensor_returns_none_when_no_data():
    """Sensor returns None when coordinator has no data."""
    desc = next(d for d in SENSOR_TYPES if d.key == "open_tickets")
    sensor = _make_sensor(desc)
    sensor.coordinator.data = None
    assert sensor.native_value is None


def test_sensor_ignores_other_homes():
    """Sensor only counts tickets/inventory belonging to its home."""
    data = {
        "homes": [{"id": 1}, {"id": 2}],
        "tickets": [
            {"id": 10, "home_id": 2, "status": "open", "priority": "low"},
        ],
        "inventory": [],
    }
    desc = next(d for d in SENSOR_TYPES if d.key == "open_tickets")
    coordinator = MagicMock()
    coordinator.data = data
    sensor = HouseHeroSensor.__new__(HouseHeroSensor)
    sensor.coordinator = coordinator
    sensor.entity_description = desc
    sensor._home_id = 1  # home 1 has no tickets
    sensor._home_name = "Home 1"
    assert sensor.native_value == 0


def test_count_tickets_helper():
    """_count_tickets filters correctly."""
    data = MOCK_API_DATA
    assert _count_tickets(data, 1, status="open") == 2
    assert _count_tickets(data, 1, status="in-progress") == 1
    assert _count_tickets(data, 1, status="waiting") == 1
    assert _count_tickets(data, 1, status="closed") == 1
    assert _count_tickets(data, 1, priority="high") == 1
    assert _count_tickets(data, 1, priority="medium") == 2
    assert _count_tickets(data, 1, priority="low") == 2
    assert _count_tickets(data, 99) == 0  # unknown home


def test_all_sensor_types_have_unique_keys():
    """All sensor descriptions must have unique keys."""
    keys = [d.key for d in SENSOR_TYPES]
    assert len(keys) == len(set(keys))


def test_all_status_sensors_present():
    """All four ticket statuses have a corresponding sensor."""
    keys = {d.key for d in SENSOR_TYPES}
    assert "open_tickets" in keys
    assert "in_progress_tickets" in keys
    assert "waiting_tickets" in keys
    assert "closed_tickets" in keys


def test_all_priority_sensors_present():
    """All three ticket priorities have a corresponding sensor."""
    keys = {d.key for d in SENSOR_TYPES}
    assert "high_priority_tickets" in keys
    assert "medium_priority_tickets" in keys
    assert "low_priority_tickets" in keys
