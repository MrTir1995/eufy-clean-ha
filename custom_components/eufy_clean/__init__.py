"""The Eufy Clean integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_DEVICE_ID, CONF_DEVICE_IP, CONF_LOCAL_KEY, DOMAIN
from .coordinator import EufyCleanDataUpdateCoordinator
from .eufy_api import EufyCleanAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.VACUUM]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eufy Clean from a config entry."""
    _LOGGER.debug("Setting up Eufy Clean integration")

    # Initialize API client
    api = EufyCleanAPI(
        device_id=entry.data[CONF_DEVICE_ID],
        local_key=entry.data[CONF_LOCAL_KEY],
        device_ip=entry.data[CONF_DEVICE_IP],
    )

    # Test connection
    try:
        await api.async_connect()
        status = await api.async_get_status()
        if status is None:
            raise ConfigEntryNotReady("Unable to connect to device")
    except Exception as err:
        _LOGGER.error("Error connecting to Eufy Clean device: %s", err)
        raise ConfigEntryNotReady from err

    # Create coordinator
    coordinator = EufyCleanDataUpdateCoordinator(hass, api)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Setup update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Eufy Clean integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Disconnect and cleanup
        coordinator: EufyCleanDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.api.async_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Eufy Clean component."""
    # Only config flow is supported
    return True
