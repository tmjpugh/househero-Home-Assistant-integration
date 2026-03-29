# House Hero — Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

A [Home Assistant](https://www.home-assistant.io/) integration for the [House Hero](https://github.com/tmjpugh/househero) home maintenance tracker.

It polls your self-hosted House Hero instance and creates **sensor entities** for each of your homes so you can build dashboards, automations, and alerts directly inside Home Assistant.

---

## Sensors created (per home)

| Sensor | Description |
|--------|-------------|
| **Open Tickets** | Number of tickets with status `open` |
| **In Progress Tickets** | Number of tickets with status `in_progress` |
| **Closed Tickets** | Number of tickets with status `closed` |
| **High Priority Tickets** | Number of tickets with priority `high` (any status) |
| **Inventory Items** | Number of inventory items tracked for the home |

---

## Installation

### Via HACS (recommended)

1. Open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/tmjpugh/househero-Home-Assistant-integration` as type **Integration**.
3. Search for *House Hero* and install.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/househero/` into your HA `config/custom_components/` directory.
2. Restart Home Assistant.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **House Hero**.
3. Enter the base URL of your House Hero instance, e.g. `http://192.168.1.100:8080`.
4. Click **Submit** — the integration will verify connectivity and create all sensors.

> **Note:** The integration polls the API every 5 minutes by default.

---

## Requirements

- A running [House Hero](https://github.com/tmjpugh/househero) instance reachable from your Home Assistant host.
- Home Assistant 2024.1 or newer.

---

## Development

```bash
# Install dev dependencies
pip install -r requirements_test.txt

# Run tests
python -m pytest tests/ -v
```
