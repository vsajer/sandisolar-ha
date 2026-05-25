"""Modbus RTU Hub for SANDISOLAR SD-PRO-EU."""

import asyncio
import logging
from typing import Any, Optional

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .modbus_map import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)


class SandiSolarModbusHub:
    """Main Modbus RTU hub for SANDISOLAR."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the hub."""
        self.hass = hass
        self.entry = entry

        self.port = entry.data["port"]
        self.baudrate = entry.data["baudrate"]
        self.slave_id = entry.data["slave_id"]
        self.update_interval = entry.data["update_interval"]

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()

    async def async_init(self) -> None:
        """Initialize Modbus connection."""
        _LOGGER.info("Initializing SANDISOLAR Modbus RTU on %s", self.port)

        self._client = AsyncModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2,
            retries=3,
        )

        connected = await self._client.connect()
        if not connected:
            raise ModbusException(f"Cannot open serial port {self.port}")

        _LOGGER.info("SANDISOLAR Modbus RTU connected successfully")

    async def close(self) -> None:
        """Close Modbus connection."""
        if self._client:
            await self._client.close()
            _LOGGER.info("SANDISOLAR Modbus RTU connection closed")

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------

    async def _ensure_connection(self) -> None:
        """Reconnect if needed."""
        if not self._client:
            raise ModbusException("Modbus client not initialized")

        if not self._client.connected:
            _LOGGER.warning("Modbus disconnected, reconnecting...")
            await self._client.connect()

    # -------------------------------------------------------------------------
    # INPUT REGISTERS (READ ONLY)
    # -------------------------------------------------------------------------

    async def read_input_register(self, key: str) -> Optional[float]:
        """Read an input register by key."""
        reg = INPUT_REGISTERS.get(key)
        if not reg:
            _LOGGER.error("Unknown input register key: %s", key)
            return None

        async with self._lock:
            await self._ensure_connection()

            try:
                result = await self._client.read_input_registers(
                    address=reg.address,
                    count=reg.count,
                    slave=self.slave_id,
                )
            except Exception as err:
                _LOGGER.error("Modbus read_input error (%s): %s", key, err)
                return None

        if result.isError():
            _LOGGER.error("Modbus error reading %s", key)
            return None

        raw = result.registers[0]
        return raw * reg.scale

    # -------------------------------------------------------------------------
    # HOLDING REGISTERS (READ + WRITE)
    # -------------------------------------------------------------------------

    async def read_holding_register(self, key: str) -> Optional[float]:
        """Read a holding register."""
        reg = HOLDING_REGISTERS.get(key)
        if not reg:
            _LOGGER.error("Unknown holding register key: %s", key)
            return None

        async with self._lock:
            await self._ensure_connection()

            try:
                result = await self._client.read_holding_registers(
                    address=reg.address,
                    count=reg.count,
                    slave=self.slave_id,
                )
            except Exception as err:
                _LOGGER.error("Modbus read_holding error (%s): %s", key, err)
                return None

        if result.isError():
            _LOGGER.error("Modbus error reading %s", key)
            return None

        raw = result.registers[0]
        return raw * reg.scale

    async def write_holding_register(self, key: str, value: float) -> bool:
        """Write a holding register."""
        reg = HOLDING_REGISTERS.get(key)
        if not reg:
            _LOGGER.error("Unknown holding register key: %s", key)
            return False

        raw_value = int(value / reg.scale)

        async with self._lock:
            await self._ensure_connection()

            try:
                result = await self._client.write_register(
                    address=reg.address,
                    value=raw_value,
                    slave=self.slave_id,
                )
            except Exception as err:
                _LOGGER.error("Modbus write error (%s): %s", key, err)
                return False

        if result.isError():
            _LOGGER.error("Modbus write error for %s", key)
            return False

        return True
