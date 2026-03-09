"""Config flow for DDSU666 power meter integration."""

from __future__ import annotations

import logging
import traceback
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_SLAVE,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DOMAIN,
    REGISTER_CONFIG_KEYS,
)
from .modbus_client import async_read_all


def _schema(default_port: int = DEFAULT_PORT, default_slave: int = DEFAULT_SLAVE) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=default_port): vol.Coerce(int),
            vol.Required(CONF_SLAVE, default=default_slave): vol.Coerce(int),
        }
    )


def _options_schema(data: dict) -> vol.Schema:
    """Schema for options flow: connection + optional register addresses (decimal)."""
    base = {
        vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
        vol.Required(CONF_PORT, default=data.get(CONF_PORT, DEFAULT_PORT)): vol.Coerce(int),
        vol.Required(CONF_SLAVE, default=data.get(CONF_SLAVE, DEFAULT_SLAVE)): vol.Coerce(int),
    }
    for key, default_val in REGISTER_CONFIG_KEYS:
        base[vol.Optional(key, default=data.get(key, default_val))] = vol.Coerce(int)
    return vol.Schema(base)


async def _test_connection(hass: HomeAssistant, host: str, port: int, slave: int) -> str | None:
    """Test Modbus TCP connection. Returns None on success, error message on failure."""
    logger = logging.getLogger(__name__)
    try:
        await async_read_all(host=host, port=port, slave=slave, timeout=5.0)
        return None
    except Exception as e:
        msg = str(e)
        logger.warning(
            "DDSU666 connection test failed (%s:%s slave=%s): %s\n%s",
            host, port, slave, msg, traceback.format_exc(),
        )
        return msg


def _entry_data(entry: config_entries.ConfigEntry) -> dict:
    """Get effective config (options override data)."""
    data = dict(entry.data)
    if entry.options:
        data.update(entry.options)
    return data


class Ddsu666ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DDSU666 power meter."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            slave = user_input[CONF_SLAVE]
            if not host:
                errors["base"] = "invalid_host"
            else:
                err = await _test_connection(self.hass, host, port, slave)
                if err:
                    errors["base"] = "cannot_connect"
                    self._connection_error_reason = err
                else:
                    await self.async_set_unique_id(f"{host}:{port}:{slave}")
                    self._abort_if_unique_id_configured()
                    title = f"DDSU666 ({host}:{port} #{slave})"
                    return self.async_create_entry(title=title, data=user_input)

        placeholders = {}
        if errors.get("base") == "cannot_connect" and getattr(self, "_connection_error_reason", None):
            placeholders["reason"] = self._connection_error_reason
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            errors=errors,
            description_placeholders=placeholders if placeholders else None,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> Ddsu666OptionsFlowHandler:
        """Get the options flow for this handler."""
        return Ddsu666OptionsFlowHandler(config_entry)


class Ddsu666OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle DDSU666 options (change host, port, slave, and optional register addresses)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        data = _entry_data(self._config_entry)

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            slave = user_input[CONF_SLAVE]
            if not host:
                errors["base"] = "invalid_host"
            else:
                err = await _test_connection(self.hass, host, port, slave)
                if err:
                    errors["base"] = "cannot_connect"
                    self._connection_error_reason = err
                else:
                    unique_id = f"{host}:{port}:{slave}"
                    for entry in self.hass.config_entries.async_entries(DOMAIN):
                        if entry.entry_id == self._config_entry.entry_id:
                            continue
                        if entry.unique_id == unique_id:
                            errors["base"] = "already_configured"
                            break
                    else:
                        return self.async_create_entry(data=user_input)

        placeholders = {}
        if errors.get("base") == "cannot_connect" and getattr(self, "_connection_error_reason", None):
            placeholders["reason"] = self._connection_error_reason
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(data),
            errors=errors,
            description_placeholders=placeholders if placeholders else None,
        )
