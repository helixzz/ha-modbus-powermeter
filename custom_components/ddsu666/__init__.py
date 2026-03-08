"""DDSU666 power meter integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from .const import CONF_SLAVE, DOMAIN
from .coordinator import Ddsu666DataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up DDSU666 from a config entry."""
    coordinator = Ddsu666DataUpdateCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_forward_entry_unload(
        entry, "sensor"
    ):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for the config entry."""
    coordinator: Ddsu666DataUpdateCoordinator | None = hass.data.get(DOMAIN, {}).get(
        entry.entry_id
    )
    data = dict(entry.data)
    if entry.options:
        data.update(entry.options)
    host = data.get(CONF_HOST, "")
    port = data.get(CONF_PORT, 0)
    slave = data.get(CONF_SLAVE, 0)
    redacted_host = _redact_host(host)
    result: dict[str, Any] = {
        "config": {
            "host": redacted_host,
            "port": port,
            "slave": slave,
        },
        "last_update": None,
        "last_error": None,
        "last_raw": None,
    }
    if coordinator:
        if coordinator.last_success_time:
            result["last_update"] = coordinator.last_success_time.isoformat()
        result["last_error"] = coordinator.last_error
        result["last_raw"] = coordinator.last_raw_data
    return result


def _redact_host(host: str) -> str:
    """Redact host for diagnostics (e.g. 192.168.1.100 -> 192.168.1.xxx)."""
    if not host or "." not in host:
        return "***"
    parts = host.rsplit(".", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return f"{parts[0]}.xxx"
    return "***"
