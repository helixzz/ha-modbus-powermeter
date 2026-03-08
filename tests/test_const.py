"""Tests for ddsu666.const (no pymodbus)."""
import pytest

# Import after conftest has added custom_components to path
from ddsu666.const import (
    DEFAULT_REG_I,
    DEFAULT_REG_IMPEP,
    DEFAULT_REG_U,
    get_register_map_from_config,
    REGISTER_CONFIG_KEYS,
    SENSOR_KEYS,
    SENSOR_REGISTERS,
)


def test_sensor_keys():
    assert len(SENSOR_KEYS) == 8
    assert SENSOR_KEYS == ["u", "i", "p", "q", "s", "pf", "freq", "impep"]


def test_sensor_registers_defaults():
    assert len(SENSOR_REGISTERS) == 8
    assert SENSOR_REGISTERS[0][0] == DEFAULT_REG_U  # voltage address
    assert SENSOR_REGISTERS[0][1] == 2  # count
    assert SENSOR_REGISTERS[0][2] is None  # scale
    assert SENSOR_REGISTERS[0][3] == "u"
    assert SENSOR_REGISTERS[7][0] == DEFAULT_REG_IMPEP
    assert SENSOR_REGISTERS[7][3] == "impep"


def test_register_config_keys():
    assert len(REGISTER_CONFIG_KEYS) == 8


def test_get_register_map_from_config_empty():
    m = get_register_map_from_config({})
    assert len(m) == 8
    assert m[0][0] == DEFAULT_REG_U
    assert m[7][0] == DEFAULT_REG_IMPEP


def test_get_register_map_from_config_overrides():
    m = get_register_map_from_config({"reg_u": 0x3000, "reg_impep": 0x5000})
    assert m[0][0] == 0x3000
    assert m[7][0] == 0x5000
    assert m[1][0] == DEFAULT_REG_I  # unchanged
