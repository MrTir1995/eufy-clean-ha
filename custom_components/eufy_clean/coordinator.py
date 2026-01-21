"""DataUpdateCoordinator for Eufy Clean."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .eufy_api import EufyCleanAPI

_LOGGER = logging.getLogger(__name__)


class EufyCleanDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Eufy Clean data."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: EufyCleanAPI,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        try:
            status = await self.api.async_get_status()

            if status is None:
                raise UpdateFailed("Failed to get device status")

            return status
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err
