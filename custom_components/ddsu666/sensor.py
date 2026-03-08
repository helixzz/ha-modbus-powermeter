"""Sensor platform for DDSU666 power meter."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# UnitOf* enums: voltage is UnitOfElectricPotential (not UnitOfVoltage) in HA
try:
    from homeassistant.const import (
        UnitOfElectricCurrent,
        UnitOfElectricPotential,
        UnitOfEnergy,
        UnitOfFrequency,
        UnitOfPower,
    )
except ImportError:
    UnitOfElectricPotential = type("UnitOfElectricPotential", (), {"VOLT": "V"})
    UnitOfElectricCurrent = type("UnitOfElectricCurrent", (), {"AMPERE": "A"})
    UnitOfPower = type("UnitOfPower", (), {"WATT": "W"})
    UnitOfEnergy = type("UnitOfEnergy", (), {"KILO_WATT_HOUR": "kWh"})
    UnitOfFrequency = type("UnitOfFrequency", (), {"HERTZ": "Hz"})
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_KEYS
from .coordinator import Ddsu666DataUpdateCoordinator

# Key -> (name, device_class, state_class, native_unit, suggested_display_precision)
SENSOR_DEF = {
    "u": (
        "Voltage",
        SensorDeviceClass.VOLTAGE,
        SensorStateClass.MEASUREMENT,
        UnitOfElectricPotential.VOLT,
        1,
    ),
    "i": (
        "Current",
        SensorDeviceClass.CURRENT,
        SensorStateClass.MEASUREMENT,
        UnitOfElectricCurrent.AMPERE,
        2,
    ),
    "p": (
        "Active power",
        SensorDeviceClass.POWER,
        SensorStateClass.MEASUREMENT,
        UnitOfPower.WATT,
        0,
    ),
    "q": (
        "Reactive power",
        None,
        SensorStateClass.MEASUREMENT,
        "var",
        0,
    ),
    "s": (
        "Apparent power",
        None,
        SensorStateClass.MEASUREMENT,
        "VA",
        0,
    ),
    "pf": (
        "Power factor",
        None,
        SensorStateClass.MEASUREMENT,
        None,
        2,
    ),
    "freq": (
        "Frequency",
        SensorDeviceClass.FREQUENCY,
        SensorStateClass.MEASUREMENT,
        UnitOfFrequency.HERTZ,
        2,
    ),
    "impep": (
        "Total active energy",
        SensorDeviceClass.ENERGY,
        SensorStateClass.TOTAL_INCREASING,
        UnitOfEnergy.KILO_WATT_HOUR,
        2,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up DDSU666 sensors from a config entry."""
    coordinator: Ddsu666DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        Ddsu666Sensor(coordinator, entry, key) for key in SENSOR_KEYS
    ]
    async_add_entities(entities)


class Ddsu666Sensor(CoordinatorEntity[Ddsu666DataUpdateCoordinator], SensorEntity):
    """Sensor for a single DDSU666 value."""

    def __init__(
        self,
        coordinator: Ddsu666DataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._entry = entry
        name, device_class, state_class, unit, precision = SENSOR_DEF[key]
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit
        self._attr_suggested_display_precision = precision

    @property
    def device_info(self):
        """Return device info for the meter."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title or "DDSU666 Power Meter",
            "manufacturer": "CHNT",
            "model": "DDSU666",
        }

    @property
    def native_value(self):
        """Return the state from coordinator data."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._key)
        if value is None:
            return None
        if self._key == "pf" and self._attr_suggested_display_precision is not None:
            return round(value, self._attr_suggested_display_precision)
        if self._attr_suggested_display_precision is not None and self._key != "impep":
            return round(value, self._attr_suggested_display_precision)
        return value
