# DDSU666 Power Meter

Home Assistant integration for the 正泰 (CHNT) DDSU666 single-phase power meter over Modbus TCP (e.g. via an RS485‑to‑TCP gateway).

## Features

- **Config flow**: Add the meter via the UI with host, port, and Modbus slave address. Connection is tested before saving.
- **Options flow**: Change IP, port, or slave address later from the integration/device Configure screen.
- **Multiple meters**: Add the same gateway several times with different slave IDs to support multiple DDSU666 meters on one gateway.
- **Diagnostics**: Download diagnostics (last update time, last error, last raw values) from the integration/device menu to troubleshoot connection or data issues.
- **Energy dashboard**: Use the **Total active energy** sensor in the Energy dashboard for consumption statistics.

## Sensors

Voltage, current, active/reactive/apparent power, power factor, frequency, and total active energy (kWh). All are exposed as sensors with appropriate device and state classes for history and Energy.

## Installation

Install via HACS (add this repo as a custom integration repository) or copy `custom_components/ddsu666` into your `custom_components` folder and restart Home Assistant.

See the [README](https://github.com/helixzz/ha-modbus-powermeter) for full setup and configuration.
