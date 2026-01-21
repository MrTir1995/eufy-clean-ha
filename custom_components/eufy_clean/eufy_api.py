"""Eufy Clean API client for local control and cloud authentication."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import tinytuya

from .const import (
    DPS_BATTERY,
    DPS_ERROR_CODE,
    DPS_FAN_SPEED,
    DPS_MODE,
    DPS_POWER,
    DPS_RETURN_HOME,
    DPS_STATUS,
    EUFY_API_DEVICES,
    EUFY_API_LOGIN,
    EUFY_CLIENT_ID,
    EUFY_CLIENT_SECRET,
    EUFY_CLIENTS,
    STATE_CHARGING,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    TUYA_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class EufyCloudAPI:
    """Eufy Cloud API client for authentication and key extraction."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the Eufy Cloud API client."""
        self.session = session
        self._token: str | None = None

    async def async_login(self, email: str, password: str) -> str:
        """Login to Eufy Cloud and get access token. Tries multiple client credentials."""
        headers = {
            "Content-Type": "application/json",
        }
        
        # Try multiple client credentials
        last_error = None
        for client in EUFY_CLIENTS:
            data = {
                "client_id": client["client_id"],
                "client_secret": client["client_secret"],
                "email": email,
                "password": password,
            }
            
            _LOGGER.debug("Attempting login with client: %s", client["name"])

            try:
                async with self.session.post(
                    EUFY_API_LOGIN, json=data, headers=headers, timeout=10
                ) as response:
                    result = await response.json()
                    
                    # Check for error in response
                    if result.get("error"):
                        error_msg = result.get("message", {}).get("message", result.get("error_description"))
                        _LOGGER.debug("Client %s failed: %s", client["name"], error_msg)
                        last_error = error_msg
                        continue
                    
                    # Try to extract token
                    self._token = (
                        result.get("access_token")
                        or result.get("data", {}).get("access_token")
                        or result.get("user_info", {}).get("token")
                    )

                    if self._token:
                        _LOGGER.info(
                            "Successfully authenticated with Eufy API using client: %s",
                            client["name"],
                        )
                        return self._token
                    else:
                        _LOGGER.debug(
                            "No token in response from client %s", client["name"]
                        )
                        last_error = "No access token in response"

            except aiohttp.ClientError as err:
                _LOGGER.debug(
                    "Client %s connection error: %s", client["name"], err
                )
                last_error = str(err)
                continue

        # All clients failed
        error_msg = f"Failed to authenticate with any Eufy client. Last error: {last_error}"
        _LOGGER.error(error_msg)
        raise ValueError(error_msg)

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Get list of devices from Eufy Clean API."""
        if not self._token:
            raise ValueError("Not authenticated - call async_login first")

        headers = {
            "token": self._token,
            "category": "Home",
            "Content-Type": "application/json",
        }

        try:
            async with self.session.get(
                EUFY_API_DEVICES, headers=headers, timeout=10
            ) as response:
                response.raise_for_status()
                result = await response.json()
                _LOGGER.debug(
                    "Devices response structure: %s",
                    result.keys() if isinstance(result, dict) else type(result),
                )
                _LOGGER.debug("Full devices response: %s", result)

                devices = []

                # Eufy Clean API returns devices directly in "data" array
                # or nested in data.items or data.devices
                data = result.get("data", [])

                # Handle both array and dict responses
                if isinstance(data, dict):
                    items = (
                        data.get("items", [])
                        or data.get("devices", [])
                        or data.get("device_list", [])
                    )
                elif isinstance(data, list):
                    items = data
                else:
                    items = []

                _LOGGER.debug("Found %d items in Eufy Clean API response", len(items))

                for idx, item in enumerate(items):
                    _LOGGER.debug(
                        "Processing item %d: %s",
                        idx,
                        item.keys() if isinstance(item, dict) else type(item),
                    )

                    # Eufy Clean may return devices directly or nested
                    device = None
                    if isinstance(item, dict):
                        device = item.get("device") or item

                    if device:
                        # Extract device info with fallbacks for Eufy Clean API
                        device_info = {
                            "device_id": (
                                device.get("id")
                                or device.get("device_id")
                                or device.get("deviceId")
                            ),
                            "name": device.get("alias")
                            or device.get("name")
                            or device.get("device_name")
                            or "Unknown",
                            "model": (
                                device.get("product", {}).get("product_code")
                                or device.get("product_code")
                                or device.get("model")
                                or device.get("product_name")
                            ),
                            "local_key": (
                                device.get("local_code")
                                or device.get("local_key")
                                or device.get("localKey")
                            ),
                            "ip": (
                                device.get("wifi", {}).get("lan_ip")
                                or device.get("lan_ip")
                                or device.get("ip")
                            ),
                        }
                        _LOGGER.debug("Extracted device info: %s", device_info)

                        # Only add if we have at least device_id
                        if device_info["device_id"]:
                            devices.append(device_info)
                        else:
                            _LOGGER.warning("Skipping device without ID: %s", device)

                _LOGGER.info("Found %d devices total from Eufy Cloud", len(devices))

                if not devices:
                    _LOGGER.warning(
                        "No devices found. Response structure: data=%s, items=%s",
                        data.keys() if isinstance(data, dict) else type(data),
                        len(items),
                    )

                return devices
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to get devices from Eufy Cloud: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error getting devices: %s", err)
            raise
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error getting devices: %s", err)
            raise


class EufyCleanAPI:
    """Eufy Clean local API client using Tuya protocol."""

    def __init__(
        self,
        device_id: str,
        local_key: str,
        device_ip: str,
    ) -> None:
        """Initialize the Eufy Clean API client."""
        self.device_id = device_id
        self.local_key = local_key
        self.device_ip = device_ip
        self._device: tinytuya.Device | None = None
        self._lock = asyncio.Lock()

    async def async_connect(self) -> None:
        """Connect to the device."""
        await asyncio.get_event_loop().run_in_executor(None, self._connect)

    def _connect(self) -> None:
        """Connect to the device (blocking)."""
        self._device = tinytuya.Device(
            dev_id=self.device_id,
            address=self.device_ip,
            local_key=self.local_key,
            version=float(TUYA_VERSION),
        )
        self._device.set_socketPersistent(True)
        self._device.set_socketTimeout(5)

    async def async_disconnect(self) -> None:
        """Disconnect from the device."""
        if self._device:
            await asyncio.get_event_loop().run_in_executor(None, self._device.close)
            self._device = None

    async def async_get_status(self) -> dict[str, Any] | None:
        """Get current device status."""
        if not self._device:
            await self.async_connect()

        async with self._lock:
            try:
                status = await asyncio.get_event_loop().run_in_executor(
                    None, self._device.status
                )

                if not status or "dps" not in status:
                    _LOGGER.warning("Invalid status response: %s", status)
                    return None

                dps = status["dps"]
                _LOGGER.debug("Raw DPS data: %s", dps)

                return self._parse_status(dps)
            except Exception as err:
                _LOGGER.error("Error getting status: %s", err)
                return None

    def _parse_status(self, dps: dict[str, Any]) -> dict[str, Any]:
        """Parse DPS data into friendly format."""
        # Parse power state
        is_on = dps.get(DPS_POWER, False)

        # Parse cleaning state
        raw_status = dps.get(DPS_STATUS, "standby")
        state = self._map_state(raw_status, is_on)

        # Parse battery
        battery = dps.get(DPS_BATTERY, 0)

        # Parse fan speed
        fan_speed = self._map_fan_speed(dps.get(DPS_FAN_SPEED, 0))

        # Parse error
        error_code = dps.get(DPS_ERROR_CODE, "0")

        return {
            "state": state,
            "battery": battery,
            "fan_speed": fan_speed,
            "error_code": error_code,
            "is_on": is_on,
            "raw_dps": dps,
        }

    def _map_state(self, raw_status: str, is_on: bool) -> str:
        """Map raw status to vacuum state."""
        if not is_on:
            return STATE_DOCKED

        status_map = {
            "charging": STATE_CHARGING,
            "Charging": STATE_CHARGING,
            "cleaning": STATE_CLEANING,
            "Cleaning": STATE_CLEANING,
            "completed": STATE_IDLE,
            "Completed": STATE_IDLE,
            "standby": STATE_IDLE,
            "Standby": STATE_IDLE,
            "paused": STATE_PAUSED,
            "Paused": STATE_PAUSED,
            "recharge": STATE_RETURNING,
            "Recharge": STATE_RETURNING,
            "goto_pos": STATE_RETURNING,
        }

        return status_map.get(raw_status, STATE_IDLE)

    def _map_fan_speed(self, speed_value: int) -> str:
        """Map DPS fan speed value to string."""
        speed_map = {
            0: "Quiet",
            1: "Standard",
            2: "Turbo",
            3: "Max",
        }
        return speed_map.get(speed_value, "Standard")

    def _reverse_map_fan_speed(self, speed_name: str) -> int:
        """Map fan speed string to DPS value."""
        speed_map = {
            "Quiet": 0,
            "Standard": 1,
            "Turbo": 2,
            "Max": 3,
        }
        return speed_map.get(speed_name, 1)

    async def async_start(self) -> bool:
        """Start cleaning."""
        return await self._send_command({DPS_POWER: True, DPS_MODE: 0})

    async def async_stop(self) -> bool:
        """Stop cleaning."""
        return await self._send_command({DPS_POWER: False})

    async def async_pause(self) -> bool:
        """Pause cleaning."""
        return await self._send_command({DPS_POWER: False})

    async def async_return_to_base(self) -> bool:
        """Return to charging base."""
        return await self._send_command({DPS_RETURN_HOME: True})

    async def async_set_fan_speed(self, speed: str) -> bool:
        """Set fan speed."""
        speed_value = self._reverse_map_fan_speed(speed)
        return await self._send_command({DPS_FAN_SPEED: speed_value})

    async def _send_command(self, commands: dict[str, Any]) -> bool:
        """Send command to device."""
        if not self._device:
            await self.async_connect()

        async with self._lock:
            try:
                _LOGGER.debug("Sending command: %s", commands)
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._device.set_multiple_values, commands
                )
                _LOGGER.debug("Command result: %s", result)
                return True
            except Exception as err:
                _LOGGER.error("Error sending command: %s", err)
                return False
