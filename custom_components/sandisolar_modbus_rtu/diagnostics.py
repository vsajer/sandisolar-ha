"""Diagnostics for SANDISOLAR Modbus RTU integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .hub import SandiSolarModbusHub


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    hub: SandiSolarModbusHub = hass.data[DOMAIN][entry.entry_id]

    diagnostics: dict[str, Any] = {
        "port": hub.port,
        "baudrate": hub.baudrate,
        "slave": hub.slave,
        "update_interval": hub.update_interval,
        "connected": getattr(hub._client, "connected", False),
    }

    # ---------------------------------------------------------
    # SAFE REGISTER DUMP (only if hub implements it)
    # ---------------------------------------------------------

    if hasattr(hub, "dump_all_registers"):
        try:
            dump = await hub.dump_all_registers()
            diagnostics["registers"] = dump
        except Exception as err:
            diagnostics["registers_error"] = str(err)
    else:
        diagnostics["registers"] = "dump_all_registers() not implemented"

    return diagnostics
