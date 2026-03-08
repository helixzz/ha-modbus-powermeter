# DDSU666 Power Meter – Home Assistant Integration

Home Assistant integration for the **正泰 (CHNT) DDSU666** single-phase power meter. The meter is connected via RS485 Modbus; use a common RS485‑Modbus‑to‑TCP gateway so the meter is reachable over your LAN. This integration reads voltage, current, power, power factor, frequency, and total active energy, and exposes them as sensors. The **total active energy** sensor can be used in the [Energy dashboard](https://www.home-assistant.io/docs/energy/) for consumption statistics.

## Requirements

- Home Assistant 2025.x or 2026.x (tested on 2026.3.1 / HAOS 17.1)
- Modbus TCP gateway on the same network as Home Assistant (IP and port reachable)
- DDSU666 meter connected to the gateway and configured with a known Modbus slave address (default 1)

## Installation

### Via HACS (recommended)

1. In HACS, go to **Integrations**, click the three dots, then **Custom repositories**.
2. Add this repository URL and set category **Integration**.
3. Search for **DDSU666 Power Meter**, install it, then restart Home Assistant.

### Manual

1. Download or clone this repository.
2. Copy the `custom_components/ddsu666` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **DDSU666** or **DDSU666 Power Meter**.
3. Enter:
   - **Host (IP address)**: IP of the Modbus TCP gateway (e.g. `172.16.33.254`).
   - **Port**: TCP port (e.g. `9999` or `502`).
   - **Modbus slave address**: Slave/unit ID of the meter (default `1`).
4. Click **Submit**. The integration will test the connection; if it succeeds, the device and sensors are created.

## Options (change connection or register addresses)

After the integration is added, you can change the gateway IP, port, slave address, or **Modbus register addresses** without removing it:

1. Go to **Settings → Devices & services**.
2. Find the **DDSU666 Power Meter** integration and open it.
3. Click **Configure** (or the device → **Configure**).
4. Update host, port, or slave and submit. A connection test is run before saving.

**Register addresses**: If your meter uses different Modbus addresses (e.g. another firmware or a similar model), you can set each register in the same Configure screen. Values are in **decimal** (e.g. 8192 for 0x2000). The default values match the standard DDSU666; leave them unchanged if you are not sure.

## Multiple meters (same gateway)

If one Modbus TCP gateway has several DDSU666 meters (different slave IDs), add the integration once per meter:

1. Add the first meter with the gateway IP, port, and its slave address (e.g. 1).
2. Add integration again with the **same** IP and port but a **different** slave address (e.g. 2, 3).
3. Each entry becomes one device with its own set of sensors. You can rename devices in the device list for clarity.

## Diagnostics

To help with connection or data issues:

1. Go to **Settings → Devices & services**.
2. Open the **DDSU666 Power Meter** integration, then open the config entry.
3. Click **Download diagnostics** (or use the three-dot menu on the device).

The downloaded JSON includes:

- **config**: Current host (IP may be partially redacted), port, and slave.
- **last_update**: Time of the last successful Modbus read (ISO format).
- **last_error**: Last error message if the most recent read failed; otherwise `null`.
- **last_raw**: Last successfully read sensor values (for comparison with the meter or manual).

Do not share full diagnostics (especially unredacted IPs) in public places.

## Sensors (entities)

| Entity | Description | Unit | Use in Energy |
|--------|-------------|------|----------------|
| Voltage | Instantaneous voltage | V | — |
| Current | Instantaneous current | A | — |
| Active power | Instantaneous active power | W | — |
| Reactive power | Instantaneous reactive power | var | — |
| Apparent power | Instantaneous apparent power | VA | — |
| Power factor | Power factor | — | — |
| Frequency | Grid frequency | Hz | — |
| **Total active energy** | Cumulative active energy | kWh | **Yes** |

In the Energy dashboard, add a **consumption** (or similar) and choose the **Total active energy** sensor for this device to track electricity usage.

## Supported device

- **Model**: 正泰 DDSU666 (CHNT DDSU666) single-phase power meter
- **Communication**: Modbus RTU over RS485, exposed via a Modbus TCP gateway (e.g. RS485‑to‑TCP converter) on your network

## Development and testing

Unit tests run locally (no Home Assistant required):

```bash
pip install -r requirements-dev.txt
pytest tests -v
```

- **Mock tests**: float parsing (`_read_float_reverse`), config/register map (`const`), and the `read_holding_registers` wrapper that adapts to different pymodbus APIs (`device_id` / `unit` / `slave` / `client.params.unit`). The full `async_read_all` flow is tested with a mock client.
- **Real device test** (optional): if the meter is reachable (e.g. at `172.16.33.254:9999`), run `pytest tests/test_real_meter.py -v -s` to hit the real meter. Set `DDSU666_HOST`, `DDSU666_PORT`, `DDSU666_SLAVE` to override; set `DDSU666_SKIP=1` to skip this test.

## License

See [LICENSE](LICENSE) in the repository root.
