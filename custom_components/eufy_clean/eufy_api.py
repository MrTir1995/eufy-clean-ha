"""Eufy Clean API client for local control and cloud authentication."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import urljoin

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
    EUFY_API_BASE,
    EUFY_API_LOGIN,
    EUFY_CLIENTS,
    STATE_CHARGING,
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    TUYA_VERSION,
)
from .tuya_api import TuyaAPIClient

_LOGGER = logging.getLogger(__name__)


class EufyCloudAPI:
    """Eufy Cloud API client for authentication and key extraction via Tuya."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the Eufy Cloud API client."""
        self.session = session
        self._token: str | None = None
        self._base_url: str = EUFY_API_BASE
        self._user_id: str | None = None
        self._phone_code: str | None = None
        self._tuya_client: TuyaAPIClient | None = None

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
                # Verwende urljoin für sichere URL-Konstruktion
                url = urljoin(self._base_url, EUFY_API_LOGIN)
                _LOGGER.debug("Login URL: %s", url)
                async with self.session.post(
                    url, json=data, headers=headers, timeout=10
                ) as response:
                    result = await response.json()

                    # Check for error in response
                    if result.get("error"):
                        error_msg = result.get("message", {}).get(
                            "message", result.get("error_description")
                        )
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
                        # Extrahiere user_id und request_host für weitere Requests
                        user_info = result.get("user_info", {})
                        self._user_id = user_info.get("id")
                        self._phone_code = user_info.get("phone_code", "1")
                        request_host = user_info.get("request_host")

                        # Wenn eine spezifische request_host zurückgegeben wird, verwende diese
                        if request_host:
                            # Stelle sicher, dass URL mit /v1/ endet
                            if not request_host.endswith("/"):
                                request_host = request_host + "/"
                            if not request_host.endswith("/v1/"):
                                request_host = request_host + "v1/"
                            self._base_url = request_host
                            _LOGGER.debug("Using regional API server: %s", request_host)

                        # Initialize Tuya API client
                        self._tuya_client = TuyaAPIClient(self.session)
                        self._tuya_client.username = f"eh-{self._user_id}"
                        self._tuya_client.country_code = self._phone_code

                        _LOGGER.info(
                            "Successfully authenticated with Eufy API using client: %s",
                            client["name"],
                        )
                        _LOGGER.debug("Tuya username: %s", self._tuya_client.username)
                        return self._token
                    else:
                        _LOGGER.debug(
                            "No token in response from client %s", client["name"]
                        )
                        last_error = "No access token in response"

            except aiohttp.ClientError as err:
                _LOGGER.debug("Client %s connection error: %s", client["name"], err)
                last_error = str(err)
                continue

        # All clients failed
        error_msg = (
            f"Failed to authenticate with any Eufy client. Last error: {last_error}"
        )
        _LOGGER.error(error_msg)
        raise ValueError(error_msg)

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Get list of devices from Tuya API (used by Eufy for RoboVac devices)."""
        if not self._token:
            raise ValueError("Not authenticated - call async_login first")

        if not self._tuya_client:
            raise ValueError("Tuya client not initialized")

        try:
            _LOGGER.info("Fetching devices from Tuya API...")

            # Get all devices from Tuya (supports multi-home)
            tuya_devices = await self._tuya_client.get_all_devices()

            _LOGGER.debug("Found %d devices from Tuya API", len(tuya_devices))

            devices = []
            for tuya_device in tuya_devices:
                # Extract device info from Tuya format
                device_info = {
                    "device_id": tuya_device.get("devId"),
                    "name": tuya_device.get("name", "Unknown"),
                    "model": tuya_device.get("productId", "Unknown"),
                    "local_key": tuya_device.get("localKey"),
                    "ip": tuya_device.get("ip"),  # May not be present
                }

                # Only add devices with required info
                if device_info["device_id"] and device_info["local_key"]:
                    devices.append(device_info)
                    _LOGGER.debug(
                        "Found device: %s (%s)",
                        device_info["name"],
                        device_info["device_id"],
                    )
                else:
                    _LOGGER.warning(
                        "Skipping device without ID or local key: %s",
                        tuya_device.get("name"),
                    )

            _LOGGER.info("Found %d valid devices from Tuya API", len(devices))

            return devices

        except Exception as err:
            _LOGGER.error("Failed to get devices from Tuya API: %s", err)
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
                    # Check if it's a device unreachable error
                    if isinstance(status, dict) and status.get("Err") == "905":
                        _LOGGER.error(
                            "Device unreachable at %s. Please verify: "
                            "1) Device is powered on and connected to WiFi, "
                            "2) IP address is correct, "
                            "3) Device is on the same network as Home Assistant",
                            self.device_ip,
                        )
                    else:
                        _LOGGER.warning("Invalid status response: %s", status)
                    return None

                dps = status["dps"]
                _LOGGER.debug("Raw DPS data: %s", dps)

                return self._parse_status(dps)
            except Exception as err:
                _LOGGER.error(
                    "Error getting status from %s: %s (Check network connectivity and device power)",
                    self.device_ip,
                    err,
                )
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
