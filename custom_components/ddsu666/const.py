"""Constants for the DDSU666 power meter integration."""

from __future__ import annotations

from typing import Any

DOMAIN = "ddsu666"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE = "slave"

# Optional register address overrides (decimal, e.g. 0x2000 = 8192)
CONF_REG_U = "reg_u"
CONF_REG_I = "reg_i"
CONF_REG_P = "reg_p"
CONF_REG_Q = "reg_q"
CONF_REG_S = "reg_s"
CONF_REG_PF = "reg_pf"
CONF_REG_FREQ = "reg_freq"
CONF_REG_IMPEP = "reg_impep"

DEFAULT_PORT = 9999
DEFAULT_SLAVE = 1
SCAN_INTERVAL = 30  # seconds

# Default register addresses (holding registers, 2 registers = float32 each)
DEFAULT_REG_U = 0x2000      # voltage
DEFAULT_REG_I = 0x2002     # current
DEFAULT_REG_P = 0x2004      # active power (value * 1000 = W)
DEFAULT_REG_Q = 0x2006      # reactive power (value * 1000 = var)
DEFAULT_REG_S = 0x2008     # apparent power
DEFAULT_REG_PF = 0x200A    # power factor
DEFAULT_REG_FREQ = 0x200E  # frequency
DEFAULT_REG_IMPEP = 0x4000 # total active energy (kWh)

# Sensor keys and default register mapping for read_all
# (start_address, count, scale, key)
# scale: None = abs, 1000 = abs * 1000
SENSOR_REGISTERS = [
    (DEFAULT_REG_U, 2, None, "u"),
    (DEFAULT_REG_I, 2, None, "i"),
    (DEFAULT_REG_P, 2, 1000, "p"),
    (DEFAULT_REG_Q, 2, 1000, "q"),
    (DEFAULT_REG_S, 2, None, "s"),
    (DEFAULT_REG_PF, 2, None, "pf"),
    (DEFAULT_REG_FREQ, 2, None, "freq"),
    (DEFAULT_REG_IMPEP, 2, None, "impep"),
]

SENSOR_KEYS = [r[3] for r in SENSOR_REGISTERS]

# Config keys for register options (for building schema and storage)
REGISTER_CONFIG_KEYS = [
    (CONF_REG_U, DEFAULT_REG_U),
    (CONF_REG_I, DEFAULT_REG_I),
    (CONF_REG_P, DEFAULT_REG_P),
    (CONF_REG_Q, DEFAULT_REG_Q),
    (CONF_REG_S, DEFAULT_REG_S),
    (CONF_REG_PF, DEFAULT_REG_PF),
    (CONF_REG_FREQ, DEFAULT_REG_FREQ),
    (CONF_REG_IMPEP, DEFAULT_REG_IMPEP),
]


def get_register_map_from_config(config: dict[str, Any]) -> list[tuple[int, int, int | None, str]]:
    """Build register map (start_address, count, scale, key) from config. Uses defaults for missing keys."""
    return [
        (config.get(CONF_REG_U, DEFAULT_REG_U), 2, None, "u"),
        (config.get(CONF_REG_I, DEFAULT_REG_I), 2, None, "i"),
        (config.get(CONF_REG_P, DEFAULT_REG_P), 2, 1000, "p"),
        (config.get(CONF_REG_Q, DEFAULT_REG_Q), 2, 1000, "q"),
        (config.get(CONF_REG_S, DEFAULT_REG_S), 2, None, "s"),
        (config.get(CONF_REG_PF, DEFAULT_REG_PF), 2, None, "pf"),
        (config.get(CONF_REG_FREQ, DEFAULT_REG_FREQ), 2, None, "freq"),
        (config.get(CONF_REG_IMPEP, DEFAULT_REG_IMPEP), 2, None, "impep"),
    ]
