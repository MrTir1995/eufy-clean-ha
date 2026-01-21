"""Test the Eufy Clean vacuum platform."""

from unittest.mock import AsyncMock, patch

from homeassistant.components.vacuum import (
    ATTR_FAN_SPEED,
    SERVICE_PAUSE,
    SERVICE_RETURN_TO_BASE,
    SERVICE_SET_FAN_SPEED,
    SERVICE_START,
    SERVICE_STOP,
)
from homeassistant.components.vacuum import DOMAIN as VACUUM_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eufy_clean.const import DOMAIN


async def test_vacuum_setup(hass, mock_config_entry_data):
    """Test vacuum entity setup."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Vacuum",
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
        api_instance.async_disconnect = AsyncMock()
        api_instance.async_get_status = AsyncMock(
            return_value={
                "state": "idle",
                "battery": 100,
                "fan_speed": "Standard",
                "error_code": "0",
                "is_on": False,
            }
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_vacuum"
        state = hass.states.get(entity_id)

        assert state is not None
        assert state.state == "idle"
        assert state.attributes[ATTR_FAN_SPEED] == "Standard"


async def test_vacuum_start(hass, mock_config_entry_data):
    """Test starting the vacuum."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Vacuum",
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
        api_instance.async_disconnect = AsyncMock()
        api_instance.async_start = AsyncMock(return_value=True)
        api_instance.async_get_status = AsyncMock(
            return_value={
                "state": "cleaning",
                "battery": 100,
                "fan_speed": "Standard",
                "error_code": "0",
                "is_on": True,
            }
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_vacuum"

        await hass.services.async_call(
            VACUUM_DOMAIN,
            SERVICE_START,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()

        api_instance.async_start.assert_called_once()


async def test_vacuum_stop(hass, mock_config_entry_data):
    """Test stopping the vacuum."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Vacuum",
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
        api_instance.async_disconnect = AsyncMock()
        api_instance.async_stop = AsyncMock(return_value=True)
        api_instance.async_get_status = AsyncMock(
            return_value={
                "state": "idle",
                "battery": 100,
                "fan_speed": "Standard",
                "error_code": "0",
                "is_on": False,
            }
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_vacuum"

        await hass.services.async_call(
            VACUUM_DOMAIN,
            SERVICE_STOP,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()

        api_instance.async_stop.assert_called_once()


async def test_vacuum_pause(hass, mock_config_entry_data):
    """Test pausing the vacuum."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Vacuum",
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
        api_instance.async_disconnect = AsyncMock()
        api_instance.async_pause = AsyncMock(return_value=True)
        api_instance.async_get_status = AsyncMock(
            return_value={
                "state": "paused",
                "battery": 100,
                "fan_speed": "Standard",
                "error_code": "0",
                "is_on": True,
            }
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_vacuum"

        await hass.services.async_call(
            VACUUM_DOMAIN,
            SERVICE_PAUSE,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()

        api_instance.async_pause.assert_called_once()


async def test_vacuum_return_to_base(hass, mock_config_entry_data):
    """Test returning vacuum to base."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Vacuum",
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
        api_instance.async_disconnect = AsyncMock()
        api_instance.async_return_to_base = AsyncMock(return_value=True)
        api_instance.async_get_status = AsyncMock(
            return_value={
                "state": "returning",
                "battery": 100,
                "fan_speed": "Standard",
                "error_code": "0",
                "is_on": True,
            }
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_vacuum"

        await hass.services.async_call(
            VACUUM_DOMAIN,
            SERVICE_RETURN_TO_BASE,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        await hass.async_block_till_done()

        api_instance.async_return_to_base.assert_called_once()


async def test_vacuum_set_fan_speed(hass, mock_config_entry_data):
    """Test setting fan speed."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Vacuum",
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
        api_instance.async_disconnect = AsyncMock()
        api_instance.async_set_fan_speed = AsyncMock(return_value=True)
        api_instance.async_get_status = AsyncMock(
            return_value={
                "state": "idle",
                "battery": 100,
                "fan_speed": "Turbo",
                "error_code": "0",
                "is_on": False,
            }
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_vacuum"

        await hass.services.async_call(
            VACUUM_DOMAIN,
            SERVICE_SET_FAN_SPEED,
            {ATTR_ENTITY_ID: entity_id, ATTR_FAN_SPEED: "Turbo"},
            blocking=True,
        )
        await hass.async_block_till_done()

        api_instance.async_set_fan_speed.assert_called_once_with("Turbo")


async def test_vacuum_error_state(hass, mock_config_entry_data):
    """Test vacuum with error state."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Vacuum",
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
        api_instance.async_disconnect = AsyncMock()
        api_instance.async_get_status = AsyncMock(
            return_value={
                "state": "error",
                "battery": 50,
                "fan_speed": "Standard",
                "error_code": "1",
                "is_on": False,
            }
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "vacuum.test_vacuum"
        state = hass.states.get(entity_id)

        assert state is not None
        assert state.state == "error"
        assert "error" in state.attributes
        assert "Wheel stuck" in state.attributes["error"]
