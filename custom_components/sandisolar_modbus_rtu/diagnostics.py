"""Diagnostics for SANDISOLAR Modbus RTU integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from . import DOMAIN
from .hub import SandiSolarModbusHub


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    hub: SandiSolarModbusHub = hass.data[DOMAIN][entry.entry_id]

    diagnostics: dict[str, Any] = {
        "port": hub.port,
        "baudrate": hub.baudrate,
        "slave_id": hub.slave_id,
        "update_interval": hub.update_interval,
    }

    try:
        dump = await hub.dump_all_registers()
        diagnostics["registers"] = dump
    except Exception as err:
        diagnostics["registers_error"] = str(err)

    return diagnostics
