"""Test the Eufy Clean config flow."""

from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eufy_clean.const import DOMAIN


async def test_form_user(hass, mock_eufy_cloud_api):
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Test with valid credentials
    with patch(
        "custom_components.eufy_clean.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test@example.com",
                CONF_PASSWORD: "test_password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "RoboVac 30C"
    assert result["data"]["device_id"] == "test_device_id"
    assert result["data"]["local_key"] == "test_local_key"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_user_invalid_auth(hass, mock_eufy_cloud_api):
    """Test invalid authentication."""
    mock_eufy_cloud_api.return_value.async_login.side_effect = ValueError(
        "Invalid credentials"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "wrong_password",
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_user_multiple_devices(hass, mock_eufy_cloud_api):
    """Test config flow with multiple devices."""
    mock_eufy_cloud_api.return_value.async_get_devices.return_value = [
        {
            "device_id": "device_1",
            "name": "RoboVac 1",
            "model": "T2250",
            "local_key": "key_1",
            "ip": "192.168.1.100",
        },
        {
            "device_id": "device_2",
            "name": "RoboVac 2",
            "model": "T2251",
            "local_key": "key_2",
            "ip": "192.168.1.101",
        },
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test_password",
        },
    )

    # Should go to device selection step
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "device"

    # Select first device
    with patch(
        "custom_components.eufy_clean.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"device": "device_1"},
        )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "RoboVac 1"
    assert result["data"]["device_id"] == "device_1"


async def test_form_user_already_configured(hass, mock_eufy_cloud_api):
    """Test we handle already configured devices."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"device_id": "test_device_id"},
        unique_id="test_device_id",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "test_password",
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass):
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "device_id": "test_device_id",
            "local_key": "test_local_key",
            "device_ip": "192.168.1.100",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"device_ip": "192.168.1.101"},
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["device_ip"] == "192.168.1.101"
