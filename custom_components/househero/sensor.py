"""Sensor platform for House Hero."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    TICKET_PRIORITY_HIGH,
    TICKET_STATUS_CLOSED,
    TICKET_STATUS_IN_PROGRESS,
    TICKET_STATUS_OPEN,
)
from .coordinator import HouseHeroCoordinator


@dataclass(frozen=True)
class HouseHeroSensorEntityDescription(SensorEntityDescription):
    """Describes a House Hero sensor."""

    value_fn: Callable[[dict, int], int] | None = None


def _count_tickets(data: dict, home_id: int, **filters) -> int:
    """Return ticket count for a home matching optional keyword filters."""
    return sum(
        1
        for t in data["tickets"]
        if t.get("home_id") == home_id
        and all(t.get(k) == v for k, v in filters.items())
    )


SENSOR_TYPES: tuple[HouseHeroSensorEntityDescription, ...] = (
    HouseHeroSensorEntityDescription(
        key="open_tickets",
        name="Open Tickets",
        icon="mdi:ticket-outline",
        native_unit_of_measurement="tickets",
        value_fn=lambda data, home_id: _count_tickets(
            data, home_id, status=TICKET_STATUS_OPEN
        ),
    ),
    HouseHeroSensorEntityDescription(
        key="in_progress_tickets",
        name="In Progress Tickets",
        icon="mdi:ticket-confirmation-outline",
        native_unit_of_measurement="tickets",
        value_fn=lambda data, home_id: _count_tickets(
            data, home_id, status=TICKET_STATUS_IN_PROGRESS
        ),
    ),
    HouseHeroSensorEntityDescription(
        key="closed_tickets",
        name="Closed Tickets",
        icon="mdi:ticket-confirmation",
        native_unit_of_measurement="tickets",
        value_fn=lambda data, home_id: _count_tickets(
            data, home_id, status=TICKET_STATUS_CLOSED
        ),
    ),
    HouseHeroSensorEntityDescription(
        key="high_priority_tickets",
        name="High Priority Tickets",
        icon="mdi:alert-circle-outline",
        native_unit_of_measurement="tickets",
        value_fn=lambda data, home_id: _count_tickets(
            data, home_id, priority=TICKET_PRIORITY_HIGH
        ),
    ),
    HouseHeroSensorEntityDescription(
        key="inventory_items",
        name="Inventory Items",
        icon="mdi:home-city-outline",
        native_unit_of_measurement="items",
        value_fn=lambda data, home_id: sum(
            1 for i in data["inventory"] if i.get("home_id") == home_id
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up House Hero sensors from a config entry."""
    coordinator: HouseHeroCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[HouseHeroSensor] = []
    for home in coordinator.data.get("homes", []):
        home_id = home["id"]
        home_name = home.get("name", f"Home {home_id}")
        for description in SENSOR_TYPES:
            entities.append(
                HouseHeroSensor(coordinator, description, home_id, home_name)
            )

    async_add_entities(entities)


class HouseHeroSensor(CoordinatorEntity[HouseHeroCoordinator], SensorEntity):
    """Representation of a House Hero sensor."""

    entity_description: HouseHeroSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HouseHeroCoordinator,
        description: HouseHeroSensorEntityDescription,
        home_id: int,
        home_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._home_id = home_id
        self._home_name = home_name
        self._attr_unique_id = f"{DOMAIN}_{home_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(home_id))},
            "name": home_name,
            "manufacturer": "House Hero",
            "model": "Maintenance Tracker",
        }

    @property
    def native_value(self) -> int | None:
        """Return the current sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data, self._home_id)
