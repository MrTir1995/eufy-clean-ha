"""Vacuum platform for Eufy Clean integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    DOMAIN,
    ERROR_CODES,
    FAN_SPEEDS,
    STATE_CHARGING,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
)
from .coordinator import EufyCleanDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Eufy Clean vacuum from config entry."""
    coordinator: EufyCleanDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([EufyCleanVacuum(coordinator, entry)])


class EufyCleanVacuum(
    CoordinatorEntity[EufyCleanDataUpdateCoordinator], StateVacuumEntity
):
    """Representation of a Eufy Clean vacuum."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.STATE
    )

    def __init__(
        self,
        coordinator: EufyCleanDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the vacuum."""
        super().__init__(coordinator)

        self._attr_unique_id = entry.data[CONF_DEVICE_ID]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.data[CONF_DEVICE_ID])},
            "name": entry.title,
            "manufacturer": "Eufy",
            "model": entry.data.get(CONF_MODEL, "RoboVac"),
        }
        self._attr_fan_speed_list = FAN_SPEEDS

    @property
    def state(self) -> str | None:
        """Return the state of the vacuum."""
        if self.coordinator.data is None:
            return None

        state = self.coordinator.data.get("state")

        # Map internal states to HA vacuum states
        state_map = {
            STATE_CLEANING: "cleaning",
            STATE_DOCKED: "docked",
            STATE_RETURNING: "returning",
            STATE_IDLE: "idle",
            STATE_PAUSED: "paused",
            STATE_CHARGING: "docked",
            STATE_ERROR: "error",
        }

        return state_map.get(state, "idle")

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the vacuum."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("battery")

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("fan_speed")

    @property
    def error(self) -> str | None:
        """Return the error state."""
        if self.coordinator.data is None:
            return None

        error_code = self.coordinator.data.get("error_code", "0")
        if error_code == "0":
            return None

        return ERROR_CODES.get(error_code, f"Unknown error: {error_code}")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}

        attrs = {}

        if self.error:
            attrs["error"] = self.error

        # Add model info
        if self._attr_device_info:
            attrs["model"] = self._attr_device_info.get("model")

        return attrs

    async def async_start(self) -> None:
        """Start or resume the cleaning task."""
        await self.coordinator.api.async_start()
        await self.coordinator.async_request_refresh()

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop the vacuum."""
        await self.coordinator.api.async_stop()
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        """Pause the vacuum."""
        await self.coordinator.api.async_pause()
        await self.coordinator.async_request_refresh()

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Return the vacuum to base."""
        await self.coordinator.api.async_return_to_base()
        await self.coordinator.async_request_refresh()

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set the fan speed."""
        if fan_speed not in FAN_SPEEDS:
            _LOGGER.error("Invalid fan speed: %s", fan_speed)
            return

        await self.coordinator.api.async_set_fan_speed(fan_speed)
        await self.coordinator.async_request_refresh()
