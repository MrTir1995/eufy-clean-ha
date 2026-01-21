"""Common fixtures for Eufy Clean tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

from custom_components.eufy_clean.const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_IP,
    CONF_LOCAL_KEY,
    CONF_MODEL,
)


# Load the integration for tests
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def mock_config_entry_data():
    """Return mock config entry data."""
    return {
        CONF_DEVICE_ID: "test_device_id",
        CONF_LOCAL_KEY: "test_local_key",
        CONF_DEVICE_IP: "192.168.1.100",
        CONF_MODEL: "T2250",
    }


@pytest.fixture
def mock_user_input():
    """Return mock user input."""
    return {
        CONF_EMAIL: "test@example.com",
        CONF_PASSWORD: "test_password",
    }


@pytest.fixture
def mock_device_status():
    """Return mock device status."""
    return {
        "state": "idle",
        "battery": 100,
        "fan_speed": "Standard",
        "error_code": "0",
        "is_on": False,
        "raw_dps": {
            "1": False,
            "15": "standby",
            "102": 1,
            "104": 100,
        },
    }


@pytest.fixture
def mock_devices_list():
    """Return mock devices list from cloud API."""
    return [
        {
            "device_id": "test_device_id",
            "name": "RoboVac 30C",
            "model": "T2250",
            "local_key": "test_local_key",
            "ip": "192.168.1.100",
        }
    ]


@pytest.fixture
def mock_eufy_api():
    """Return a mocked EufyCleanAPI."""
    with patch("custom_components.eufy_clean.eufy_api.EufyCleanAPI") as mock:
        api = MagicMock()
        api.async_connect = AsyncMock()
        api.async_disconnect = AsyncMock()
        api.async_get_status = AsyncMock(
            return_value={
                "state": "idle",
                "battery": 100,
                "fan_speed": "Standard",
                "error_code": "0",
                "is_on": False,
                "raw_dps": {},
            }
        )
        api.async_start = AsyncMock(return_value=True)
        api.async_stop = AsyncMock(return_value=True)
        api.async_pause = AsyncMock(return_value=True)
        api.async_return_to_base = AsyncMock(return_value=True)
        api.async_set_fan_speed = AsyncMock(return_value=True)
        mock.return_value = api
        yield mock


@pytest.fixture
def mock_eufy_cloud_api():
    """Return a mocked EufyCloudAPI."""
    with patch("custom_components.eufy_clean.config_flow.EufyCloudAPI") as mock:
        api = MagicMock()
        api.async_login = AsyncMock(return_value="test_token")
        api.async_get_devices = AsyncMock(
            return_value=[
                {
                    "device_id": "test_device_id",
                    "name": "RoboVac 30C",
                    "model": "T2250",
                    "local_key": "test_local_key",
                    "ip": "192.168.1.100",
                }
            ]
        )
        mock.return_value = api
        yield mock


@pytest.fixture
def mock_tinytuya():
    """Return a mocked tinytuya Device."""
    with patch("custom_components.eufy_clean.eufy_api.tinytuya.Device") as mock:
        device = MagicMock()
        device.status = MagicMock(
            return_value={
                "dps": {
                    "1": False,
                    "15": "standby",
                    "102": 1,
                    "104": 100,
                    "106": "0",
                }
            }
        )
        device.set_multiple_values = MagicMock(return_value=True)
        device.set_socketPersistent = MagicMock()
        device.set_socketTimeout = MagicMock()
        device.close = MagicMock()
        mock.return_value = device
        yield mock
