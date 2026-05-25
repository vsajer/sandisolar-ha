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

DEFAULT_PORT = "/dev/ttyUSB0"
TEST_REGISTER = 0  # Device status register


class SandiSolarModbusHub:
    """Main Modbus RTU hub for SANDISOLAR."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the hub."""
        self.hass = hass
        self.entry = entry

        # Auto-fill port if missing
        self.port = entry.data.get("port", DEFAULT_PORT)
        self.baudrate = entry.data.get("baudrate", 9600)
        self.slave_id = entry.data.get("slave_id", 1)
        self.update_interval = entry.data.get("update_interval", 30)

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()

    # -------------------------------------------------------------------------
    # INITIALIZATION
    # -------------------------------------------------------------------------

    async def async_init(self) -> None:
        """Initialize Modbus connection and test communication."""

        # Check if port is already used by another integration
        if self._is_port_in_use():
            raise ModbusException(
                f"Serial port {self.port} is already used by another integration."
            )

        _LOGGER.info(
            "Initializing SANDISOLAR Modbus RTU on %s @ %s baud",
            self.port,
            self.baudrate,
        )

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

        _LOGGER.info("Serial port opened successfully, testing Modbus communication...")

        # Test read register 0 (Device Status)
        try:
            result = await self._client.read_input_registers(
                address=TEST_REGISTER,
                count=1,
                unit=self.slave_id,
            )
        except Exception as err:
            raise ModbusException(f"Modbus test read failed: {err}") from err

        if result.isError():
            raise ModbusException(f"Device did not respond to test read: {result}")

        _LOGGER.info("SANDISOLAR Modbus communication OK (Device Status read successful)")

    # -------------------------------------------------------------------------
    # PORT CHECK
    # -------------------------------------------------------------------------

    def _is_port_in_use(self) -> bool:
        """Check if another integration is already using this serial port."""
        for domain, entries in self.hass.data.items():
            if not isinstance(entries, dict):
                continue

            for entry_id, hub in entries.items():
                if hasattr(hub, "port") and hub.port == self.port:
                    _LOGGER.warning(
                        "Port %s is already used by integration: %s (%s)",
                        self.port,
                        domain,
                        entry_id,
                    )
                    return True

        return False

    # -------------------------------------------------------------------------
    # CONNECTION MANAGEMENT
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
                    unit=self.slave_id,
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
                    unit=self.slave_id,
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
                    unit=self.slave_id,
                )
            except Exception as err:
                _LOGGER.error("Modbus write error (%s): %s", key, err)
                return False

        if result.isError():
            _LOGGER.error("Modbus write error for %s", key)
            return False

        return True

    # -------------------------------------------------------------------------
    # CLOSE CONNECTION
    # -------------------------------------------------------------------------

    async def close(self) -> None:
        """Close Modbus connection."""
        if self._client:
            await self._client.close()
            _LOGGER.info("SANDISOLAR Modbus RTU connection closed")
