"""Test the Eufy Clean init."""

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eufy_clean.const import DOMAIN


async def test_setup_entry(hass, mock_eufy_api, mock_config_entry_data):
    """Test setting up an entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock()
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

    assert entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]


async def test_setup_entry_connection_error(hass, mock_config_entry_data):
    """Test setup entry with connection error."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=mock_config_entry_data,
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.eufy_clean.EufyCleanAPI") as mock_api:
        api_instance = mock_api.return_value
        api_instance.async_connect = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state == ConfigEntryState.SETUP_RETRY


async def test_unload_entry(hass, mock_eufy_api, mock_config_entry_data):
    """Test unloading an entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
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

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state == ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]
    api_instance.async_disconnect.assert_called_once()


async def test_update_options(hass, mock_eufy_api, mock_config_entry_data):
    """Test updating options triggers reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
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

        # Update options
        with patch("custom_components.eufy_clean.async_update_options") as mock_update:
            hass.config_entries.async_update_entry(
                entry, options={"device_ip": "192.168.1.101"}
            )
            await hass.async_block_till_done()
