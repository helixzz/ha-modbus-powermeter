"""Pytest configuration: add custom_components to path and fake homeassistant for offline tests."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

root = Path(__file__).resolve().parent.parent
custom_components = root / "custom_components"
if str(custom_components) not in sys.path:
    sys.path.insert(0, str(custom_components))

# Fake homeassistant so ddsu666 package can be imported without HA installed
if "homeassistant" not in sys.modules:
    sys.modules["homeassistant"] = MagicMock()
    sys.modules["homeassistant.config_entries"] = MagicMock()
    sys.modules["homeassistant.const"] = MagicMock()
    sys.modules["homeassistant.core"] = MagicMock()
    sys.modules["homeassistant.helpers.device_registry"] = MagicMock()
    sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()
    sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()
