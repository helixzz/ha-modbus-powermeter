"""DataUpdateCoordinator for DDSU666 power meter."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SLAVE,
    DOMAIN,
    get_register_map_from_config,
    SCAN_INTERVAL,
)
from .modbus_client import async_read_all


class Ddsu666DataUpdateCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator that fetches all sensor data from the DDSU666 meter."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self._entry = entry
        self.last_success_time: datetime | None = None
        self.last_error: str | None = None
        self.last_raw_data: dict[str, float] | None = None

        super().__init__(
            hass,
            logger=__name__,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    def _get_config(self) -> dict:
        """Get current config (data + options)."""
        data = dict(self._entry.data)
        if self._entry.options:
            data.update(self._entry.options)
        return data

    async def _async_update_data(self) -> dict[str, float]:
        """Fetch data from Modbus TCP."""
        cfg = self._get_config()
        register_map = get_register_map_from_config(cfg)
        try:
            data = await async_read_all(
                host=cfg[CONF_HOST],
                port=cfg[CONF_PORT],
                slave=cfg[CONF_SLAVE],
                timeout=5.0,
                register_map=register_map,
            )
            self.last_success_time = datetime.utcnow()
            self.last_error = None
            self.last_raw_data = dict(data)
            return data
        except Exception as err:
            self.last_error = f"{type(err).__name__}: {err}"
            raise UpdateFailed(f"Modbus read failed: {err}") from err
