"""Modbus TCP client for DDSU666 power meter (holding registers, float32 reverse)."""

from __future__ import annotations

import inspect
import struct
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import get_register_map_from_config, SENSOR_REGISTERS

# Cache for the correct keyword to pass slave/unit (discovered once per process)
_unit_keyword: str | None = None


async def _read_holding_registers(client: Any, address: int, count: int, slave: int) -> Any:
    """Call read_holding_registers with (address, count) + correct unit/slave keyword for this pymodbus version."""
    global _unit_keyword
    if _unit_keyword is None:
        sig = inspect.signature(client.read_holding_registers)
        for name in ("unit", "slave", "unit_id", "slave_id", "device_id"):
            if name in sig.parameters:
                _unit_keyword = name
                break
    if _unit_keyword:
        return await client.read_holding_registers(address, count, **{_unit_keyword: slave})
    return await client.read_holding_registers(address, count)


def _read_float_reverse(registers: list[int], offset: int = 0) -> float:
    """Parse two 16-bit registers as big-endian float32 (high word first)."""
    if offset + 2 > len(registers):
        raise ValueError("Not enough registers for float")
    r0, r1 = registers[offset], registers[offset + 1]
    value = struct.unpack("!f", struct.pack("!HH", r0, r1))[0]
    return round(value, 6)


async def async_read_all(
    host: str,
    port: int,
    slave: int,
    timeout: float = 3.0,
    register_map: list[tuple[int, int, int | None, str]] | None = None,
) -> dict[str, float]:
    """
    Connect to Modbus TCP gateway and read all DDSU666 sensor values.
    Returns dict of key -> value (e.g. u, i, p, q, s, pf, freq, impep).
    register_map: optional list of (start_address, count, scale, key); uses defaults if None.
    """
    if register_map is None:
        register_map = SENSOR_REGISTERS
    result: dict[str, float] = {}
    async with AsyncModbusTcpClient(
        host=host,
        port=port,
        timeout=timeout,
    ) as client:
        # Connection may be established on first request in some pymodbus versions
        # API takes only (address, count); unit/slave via keyword (name varies by version)
        for start_address, count, scale, key in register_map:
            rr = await _read_holding_registers(client, start_address, count, slave)
            if rr.isError():
                raise ModbusException(str(rr))
            if not rr.registers or len(rr.registers) < count:
                raise ValueError(f"Invalid response for {key}")
            value = abs(_read_float_reverse(rr.registers, 0))
            if scale is not None:
                value = value * scale
            result[key] = value

    return result
