"""Switch platform — Alarm enabled/disabled."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ENTITY_ALARM_SWITCH
from .coordinator import HabityCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: HabityCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([AlarmSwitch(coordinator, entry)])


class AlarmSwitch(CoordinatorEntity, SwitchEntity):
    """Represents the alarm enabled/disabled switch."""

    _attr_name = "Alarm"
    _attr_icon = "mdi:alarm"

    def __init__(self, coordinator: HabityCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{ENTITY_ALARM_SWITCH}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Habity",
            "manufacturer": "Habity",
            "model": "Bedside Clock",
        }

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("alarm_enabled")

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_alarm(alarm_enabled=True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_alarm(alarm_enabled=False)
