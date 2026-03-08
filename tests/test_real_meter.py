"""
Real device test: run against a live DDSU666 meter at 172.16.33.254.

Usage:
  pytest tests/test_real_meter.py -v -s
  # Or with custom host/port/slave (env or defaults):
  DDSU666_HOST=172.16.33.254 DDSU666_PORT=9999 DDSU666_SLAVE=1 pytest tests/test_real_meter.py -v -s

Skip if meter is unreachable:
  pytest tests/test_real_meter.py -v -s --ignore-global
  # Or: set DDSU666_SKIP=1 to skip
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure custom_components is on path (conftest does this when running via pytest)
root = Path(__file__).resolve().parent.parent
custom_components = root / "custom_components"
if str(custom_components) not in sys.path:
    sys.path.insert(0, str(custom_components))

# Mock homeassistant so ddsu666 package can be imported
if "homeassistant" not in sys.modules:
    from unittest.mock import MagicMock
    for mod in ("homeassistant", "homeassistant.config_entries", "homeassistant.const",
                "homeassistant.core", "homeassistant.helpers.device_registry",
                "homeassistant.helpers.entity_platform", "homeassistant.helpers.update_coordinator"):
        sys.modules[mod] = MagicMock()

import ddsu666.modbus_client as modbus_client


def _meter_config():
    return {
        "host": os.environ.get("DDSU666_HOST", "172.16.33.254"),
        "port": int(os.environ.get("DDSU666_PORT", "9999")),
        "slave": int(os.environ.get("DDSU666_SLAVE", "1")),
    }


@pytest.mark.asyncio
async def test_real_meter_async_read_all():
    """Connect to real meter and run async_read_all (same as config flow / coordinator)."""
    if os.environ.get("DDSU666_SKIP"):
        pytest.skip("DDSU666_SKIP=1")
    cfg = _meter_config()
    modbus_client._unit_strategy = None  # force fresh discovery
    try:
        result = await modbus_client.async_read_all(
            host=cfg["host"],
            port=cfg["port"],
            slave=cfg["slave"],
            timeout=5.0,
        )
    except Exception as e:
        pytest.fail(f"async_read_all failed: {e}")
    assert isinstance(result, dict)
    for key in ("u", "i", "p", "impep"):
        assert key in result, f"missing key {key}"
        assert isinstance(result[key], (int, float)), f"{key} not numeric"
    print(f"  unit strategy used: {modbus_client._unit_strategy}")
    print(f"  u (V): {result.get('u')}, i (A): {result.get('i')}, p (W): {result.get('p')}, impep (kWh): {result.get('impep')}")
