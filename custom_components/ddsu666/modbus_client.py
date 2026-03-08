"""Modbus TCP client for DDSU666 power meter (holding registers, float32 reverse)."""

from __future__ import annotations

import struct
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import get_register_map_from_config, SENSOR_REGISTERS


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
        if not client.connected:
            raise ConnectionError("Modbus TCP connection failed")

        for start_address, count, scale, key in register_map:
            rr = await client.read_holding_registers(
                address=start_address,
                count=count,
                slave=slave,
            )
            if rr.isError():
                raise ModbusException(str(rr))
            if not rr.registers or len(rr.registers) < count:
                raise ValueError(f"Invalid response for {key}")
            value = abs(_read_float_reverse(rr.registers, 0))
            if scale is not None:
                value = value * scale
            result[key] = value

    return result
