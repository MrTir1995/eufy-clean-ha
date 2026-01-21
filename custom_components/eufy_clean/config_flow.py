"""Config flow for Eufy Clean integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_DEVICE_ID, CONF_DEVICE_IP, CONF_LOCAL_KEY, CONF_MODEL, DOMAIN
from .eufy_api import EufyCloudAPI

_LOGGER = logging.getLogger(__name__)


async def validate_auth(
    hass: HomeAssistant, email: str, password: str
) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = EufyCloudAPI(session)

    try:
        await api.async_login(email, password)
        devices = await api.async_get_devices()

        _LOGGER.debug("Retrieved %d devices from Eufy Cloud", len(devices))

        if not devices:
            raise ValueError("No Eufy Clean devices found in account")

        # Filter for vacuum devices
        vacuum_devices = [
            d
            for d in devices
            if d.get("model")
            and any(
                x in d["model"].lower() for x in ["robovac", "t", "l", "x", "g", "e"]
            )
        ]

        _LOGGER.debug(
            "Found %d vacuum devices after filtering: %s",
            len(vacuum_devices),
            [d.get("model") for d in vacuum_devices],
        )

        if not vacuum_devices:
            _LOGGER.warning(
                "No vacuum devices found. All devices: %s",
                [{"name": d.get("name"), "model": d.get("model")} for d in devices],
            )
            raise ValueError("No vacuum devices found")

        return {"devices": vacuum_devices}
    except aiohttp.ClientError as err:
        _LOGGER.error("Connection error: %s", err)
        raise ValueError("Cannot connect to Eufy Cloud") from err
    except Exception as err:
        _LOGGER.error("Unexpected error: %s", err)
        raise


async def discover_device_ip(hass: HomeAssistant, device_id: str) -> str | None:
    """Try to discover device IP on local network using tinytuya scanner."""
    try:
        import tinytuya

        _LOGGER.info("Scanning local network for device %s...", device_id)

        # Run scanner in executor to avoid blocking
        def scan():
            devices = tinytuya.deviceScan(False, 20)
            return devices

        devices = await hass.async_add_executor_job(scan)

        # Look for our device
        for dev in devices:
            if dev.get("id") == device_id or dev.get("gwId") == device_id:
                ip = dev.get("ip")
                if ip:
                    _LOGGER.info("Found device %s at IP %s", device_id, ip)
                    return ip

        _LOGGER.warning("Device %s not found on local network", device_id)
        return None
    except Exception as err:
        _LOGGER.warning("Failed to scan for devices: %s", err)
        return None


class EufyCleanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eufy Clean."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._devices: list[dict[str, Any]] = []
        self._email: str | None = None
        self._password: str | None = None
        self._selected_device: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_auth(
                    self.hass, user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )

                self._devices = info["devices"]
                self._email = user_input[CONF_EMAIL]
                self._password = user_input[CONF_PASSWORD]

                # If only one device, skip device selection
                if len(self._devices) == 1:
                    device = self._devices[0]
                    return await self._create_entry(device)

                return await self.async_step_device()

            except data_entry_flow.AbortFlow:
                raise
            except ValueError as err:
                errors["base"] = "cannot_connect"
                _LOGGER.error("Validation error: %s", err)
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle device selection step."""
        if user_input is not None:
            # Find selected device
            device = next(
                (d for d in self._devices if d["device_id"] == user_input["device"]),
                None,
            )
            if device:
                # Check if device has IP address
                if not device.get("ip"):
                    # Try to discover IP automatically
                    _LOGGER.info("Device IP missing, scanning network...")
                    discovered_ip = await discover_device_ip(
                        self.hass, device["device_id"]
                    )
                    if discovered_ip:
                        device["ip"] = discovered_ip
                        _LOGGER.info("Found device at %s", discovered_ip)
                        return await self._create_entry(device)
                    else:
                        # IP not found, ask user for manual input
                        self._selected_device = device
                        return await self.async_step_ip()
                return await self._create_entry(device)

        # Create device selection options
        device_options = {
            device[
                "device_id"
            ]: f"{device['name']} ({device['model']}) - IP: {device.get('ip', 'Nicht gefunden')}"
            for device in self._devices
        }

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(device_options),
                }
            ),
        )

    async def async_step_ip(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle IP address input for devices without auto-discovered IP."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_ip = user_input[CONF_DEVICE_IP].strip()

            # Validate IP format and ensure it's a private/local IP
            import ipaddress

            try:
                ip_obj = ipaddress.ip_address(device_ip)
                
                # Check if it's a private/local IP address
                if not ip_obj.is_private:
                    errors["base"] = "not_local_ip"
                    _LOGGER.warning(
                        "User entered public IP %s - local IP required for Tuya communication",
                        device_ip,
                    )
                else:
                    # Valid local IP - add to device and create entry
                    if self._selected_device:
                        self._selected_device["ip"] = device_ip
                        return await self._create_entry(self._selected_device)
            except ValueError:
                errors["base"] = "invalid_ip"

        device_name = (
            self._selected_device.get("name", "Gerät")
            if self._selected_device
            else "Gerät"
        )

        return self.async_show_form(
            step_id="ip",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_IP): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "device_name": device_name,
            },
        )

    async def _create_entry(self, device: dict[str, Any]) -> FlowResult:
        """Create the config entry."""
        # Set unique ID to prevent duplicates
        await self.async_set_unique_id(device["device_id"])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=device["name"],
            data={
                CONF_DEVICE_ID: device["device_id"],
                CONF_LOCAL_KEY: device["local_key"],
                CONF_DEVICE_IP: device["ip"],
                CONF_MODEL: device.get("model", "Unknown"),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EufyCleanOptionsFlowHandler:
        """Get the options flow for this handler."""
        return EufyCleanOptionsFlowHandler()


class EufyCleanOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Eufy Clean."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_ip = user_input.get(CONF_DEVICE_IP)
            
            if device_ip:
                device_ip = device_ip.strip()
                
                # Validate IP format and ensure it's a private/local IP
                import ipaddress
                
                try:
                    ip_obj = ipaddress.ip_address(device_ip)
                    
                    # Check if it's a private/local IP address
                    if not ip_obj.is_private:
                        errors["base"] = "not_local_ip"
                        _LOGGER.warning(
                            "User entered public IP %s - local IP required",
                            device_ip,
                        )
                    else:
                        # Update config entry data with new IP
                        new_data = {**self.config_entry.data, CONF_DEVICE_IP: device_ip}
                        self.hass.config_entries.async_update_entry(
                            self.config_entry,
                            data=new_data,
                        )
                        # Reload the integration to apply changes
                        await self.hass.config_entries.async_reload(
                            self.config_entry.entry_id
                        )
                        return self.async_create_entry(title="", data={})
                except ValueError:
                    errors["base"] = "invalid_ip"
            else:
                # No IP provided, just close options
                return self.async_create_entry(title="", data={})

        # Get current device IP from config entry
        current_ip = self.config_entry.data.get(CONF_DEVICE_IP)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE_IP,
                        default=current_ip,
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "current_ip": current_ip or "Unbekannt",
            },
        )
