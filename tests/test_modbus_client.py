"""Tests for ddsu666.modbus_client (float parsing + pymodbus call compatibility)."""
import inspect
import struct
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import after conftest; clear keyword cache before tests that need a specific signature
import ddsu666.modbus_client as modbus_client
from ddsu666.modbus_client import (
    _read_float_reverse,
    _read_holding_registers,
    async_read_all,
)


def _float_to_two_registers_reverse(value: float) -> list[int]:
    """Same as DDSU666: big-endian float32, high word first (reverse=True in script)."""
    b = struct.pack("!f", value)
    r0 = (b[0] << 8) | b[1]
    r1 = (b[2] << 8) | b[3]
    return [r0, r1]


# --- _read_float_reverse (no pymodbus) ---


def test_read_float_reverse_voltage():
    # 220.5 V -> two registers (reverse order)
    regs = _float_to_two_registers_reverse(220.5)
    out = _read_float_reverse(regs, 0)
    assert abs(out - 220.5) < 0.001


def test_read_float_reverse_negative():
    regs = _float_to_two_registers_reverse(-10.0)
    out = _read_float_reverse(regs, 0)
    assert abs(out - (-10.0)) < 0.001


def test_read_float_reverse_insufficient_registers():
    with pytest.raises(ValueError, match="Not enough registers"):
        _read_float_reverse([0], 0)


def test_read_float_reverse_offset():
    regs = [0, 0] + _float_to_two_registers_reverse(50.0)
    out = _read_float_reverse(regs, 2)
    assert abs(out - 50.0) < 0.001


# --- _read_holding_registers keyword detection (mock client) ---


@pytest.fixture(autouse=True)
def reset_unit_keyword():
    """Reset the cached unit keyword so each test sees a clean signature."""
    modbus_client._unit_keyword = None
    yield
    modbus_client._unit_keyword = None


@pytest.mark.asyncio
async def test_read_holding_registers_uses_unit_keyword():
    """Client with unit= in signature (pymodbus 3.x style)."""
    async def read_holding_registers(address: int, count: int, *, unit: int = 1):
        assert address == 0x2000 and count == 2 and unit == 1
        return MagicMock(isError=lambda: False, registers=[0x4390, 0x8000])  # 288.0

    client = MagicMock()
    client.read_holding_registers = read_holding_registers
    result = await _read_holding_registers(client, 0x2000, 2, 1)
    assert result.registers == [0x4390, 0x8000]
    assert modbus_client._unit_keyword == "unit"


@pytest.mark.asyncio
async def test_read_holding_registers_uses_slave_keyword():
    """Client with slave= in signature (older pymodbus)."""
    modbus_client._unit_keyword = None

    async def read_holding_registers(address: int, count: int, *, slave: int = 1):
        assert address == 0x2000 and count == 2 and slave == 2
        return MagicMock(isError=lambda: False, registers=[0, 0])

    client = MagicMock()
    client.read_holding_registers = read_holding_registers
    result = await _read_holding_registers(client, 0x2000, 2, 2)
    assert modbus_client._unit_keyword == "slave"


@pytest.mark.asyncio
async def test_read_holding_registers_only_two_positional():
    """Client that only accepts (address, count) - no unit param (uses default)."""
    modbus_client._unit_keyword = None

    async def read_holding_registers(address: int, count: int):
        assert address == 0x2000 and count == 2
        return MagicMock(isError=lambda: False, registers=[0x4390, 0x8000])

    client = MagicMock()
    client.read_holding_registers = read_holding_registers
    result = await _read_holding_registers(client, 0x2000, 2, 1)
    assert result.registers == [0x4390, 0x8000]
    assert modbus_client._unit_keyword is None


# --- async_read_all with mock (full flow) ---


@pytest.mark.asyncio
async def test_async_read_all_mock_client():
    """Test full read flow with a mock AsyncModbusTcpClient (no real network)."""
    regs_u = _float_to_two_registers_reverse(220.0)
    regs_i = _float_to_two_registers_reverse(1.5)
    regs_p = _float_to_two_registers_reverse(0.35)   # * 1000 = 350 W
    regs_q = _float_to_two_registers_reverse(0.0)
    regs_s = _float_to_two_registers_reverse(350.0)
    regs_pf = _float_to_two_registers_reverse(1.0)
    regs_freq = _float_to_two_registers_reverse(50.0)
    regs_impep = _float_to_two_registers_reverse(1234.56)

    call_count = 0
    reg_list = [regs_u, regs_i, regs_p, regs_q, regs_s, regs_pf, regs_freq, regs_impep]

    async def fake_read(address: int, count: int, *, unit: int = 1):
        nonlocal call_count
        assert unit == 1
        idx = call_count
        call_count += 1
        return MagicMock(isError=lambda: False, registers=reg_list[idx])

    fake_client = MagicMock()
    fake_client.read_holding_registers = fake_read  # has (address, count, *, unit=1) in signature
    fake_client.connected = True

    class FakeCtx:
        async def __aenter__(self):
            return fake_client
        async def __aexit__(self, *args):
            pass

    with patch("ddsu666.modbus_client.AsyncModbusTcpClient", return_value=FakeCtx()):
        modbus_client._unit_keyword = None
        result = await async_read_all("127.0.0.1", 9999, 1, timeout=1.0)

    assert result["u"] == pytest.approx(220.0, abs=0.01)
    assert result["i"] == pytest.approx(1.5, abs=0.01)
    assert result["p"] == pytest.approx(350.0, abs=0.01)
    assert result["q"] == pytest.approx(0.0, abs=0.01)
    assert result["s"] == pytest.approx(350.0, abs=0.01)
    assert result["pf"] == pytest.approx(1.0, abs=0.01)
    assert result["freq"] == pytest.approx(50.0, abs=0.01)
    assert result["impep"] == pytest.approx(1234.56, abs=0.01)


@pytest.mark.asyncio
async def test_async_read_all_uses_inspect_for_keyword():
    """Ensure we only call read_holding_registers with (address, count) + one keyword."""
    seen_kwargs = []

    async def capture_read(address: int, count: int, **kwargs):
        seen_kwargs.append(kwargs)
        # Return valid 2 registers for float
        return MagicMock(isError=lambda: False, registers=[0x4390, 0x8000])

    fake_client = MagicMock()
    fake_client.read_holding_registers = capture_read
    # Signature with unit= (keyword-only)
    sig = inspect.signature(lambda address, count, *, unit=1: None)
    fake_client.read_holding_registers.__signature__ = sig

    class FakeCtx:
        async def __aenter__(self):
            return fake_client
        async def __aexit__(self, *args):
            pass

    with patch("ddsu666.modbus_client.AsyncModbusTcpClient", return_value=FakeCtx()):
        modbus_client._unit_keyword = None
        # Only read one register set to avoid many calls
        from ddsu666.const import SENSOR_REGISTERS
        single_map = [SENSOR_REGISTERS[0]]
        result = await async_read_all(
            "127.0.0.1", 9999, 5, timeout=1.0, register_map=single_map
        )

    assert len(seen_kwargs) == 1
    assert seen_kwargs[0] == {"unit": 5}
    assert "u" in result
