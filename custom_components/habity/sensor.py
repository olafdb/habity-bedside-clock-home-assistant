"""Sensor platform — next alarm time + UDP-driven button/event sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENTITY_ALARM_EVENT,
    ENTITY_NEXT_ALARM,
    ENTITY_SNOOZE_BTN,
    ENTITY_STOP_BTN,
    UDP_TYPE_EVENT,
    UDP_TYPE_SNOOZE_BTN,
    UDP_TYPE_STOP_BTN,
)
from .coordinator import HabityCoordinator

_LOGGER = logging.getLogger(__name__)


def _device_info(entry: ConfigEntry) -> dict:
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": "Habity",
        "manufacturer": "Habity",
        "model": "Bedside Clock",
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HabityCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    next_alarm_sensor = NextAlarmSensor(coordinator, entry)

    snooze_sensor = UDPButtonSensor(
        entry,
        unique_suffix=ENTITY_SNOOZE_BTN,
        name="Snooze Button",
        icon="mdi:alarm-snooze",
        udp_type=UDP_TYPE_SNOOZE_BTN,
    )
    stop_sensor = UDPButtonSensor(
        entry,
        unique_suffix=ENTITY_STOP_BTN,
        name="Stop Button",
        icon="mdi:alarm-off",
        udp_type=UDP_TYPE_STOP_BTN,
    )
    event_sensor = UDPButtonSensor(
        entry,
        unique_suffix=ENTITY_ALARM_EVENT,
        name="Alarm Event",
        icon="mdi:bell-ring",
        udp_type=UDP_TYPE_EVENT,
    )

    hass.data[DOMAIN][entry.entry_id]["udp_sensors"] = {
        UDP_TYPE_SNOOZE_BTN: snooze_sensor,
        UDP_TYPE_STOP_BTN: stop_sensor,
        UDP_TYPE_EVENT: event_sensor,
    }

    async_add_entities([next_alarm_sensor, snooze_sensor, stop_sensor, event_sensor])


class NextAlarmSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the next scheduled alarm time (HH:MM)."""

    _attr_name = "Next Alarm"
    _attr_icon = "mdi:clock-time-eight-outline"

    def __init__(self, coordinator: HabityCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{ENTITY_NEXT_ALARM}"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("next_alarm")


class UDPButtonSensor(RestoreEntity, SensorEntity):
    """
    A sensor updated in real-time by UDP broadcasts.

    States for button sensors: pressed | hold | released
    States for event sensor:   active | snoozed | stopped
    """

    def __init__(
        self,
        entry: ConfigEntry,
        unique_suffix: str,
        name: str,
        icon: str,
        udp_type: str,
    ) -> None:
        self._attr_unique_id = f"{entry.entry_id}_{unique_suffix}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry)
        self._udp_type = udp_type
        self._state: str | None = None

    @property
    def native_value(self) -> str | None:
        return self._state

    def handle_udp_update(self, state: str) -> None:
        """Called by the UDP listener when a matching packet arrives."""
        _LOGGER.debug("UDP update for %s: %s", self._attr_name, state)
        self._state = state
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Restore last known state on restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._state = last_state.state

    @property
    def should_poll(self) -> bool:
        return False
