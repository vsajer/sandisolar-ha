"""Modbus RTU Hub for SANDISOLAR SD-PRO-EU."""

import asyncio
import logging
from typing import Any, Optional, Dict

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .modbus_map import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = "/dev/ttyUSB0"
TEST_REGISTER = 64


class SandiSolarModbusHub:
    """Main Modbus RTU hub for SANDISOLAR."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self.port = entry.data.get("port", DEFAULT_PORT)
        self.baudrate = entry.data.get("baudrate", 9600)
        self.update_interval = entry.data.get("update_interval", 30)

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Any] = {}

    async def async_init(self) -> None:
        """Initialize Modbus connection and test communication."""

        _LOGGER.info("Initializing SANDISOLAR Modbus RTU on %s @ %s baud", self.port, self.baudrate)

        self._client = AsyncModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=5,
        )

        connected = await self._client.connect()
        if not connected:
            raise ModbusException(f"Cannot open serial port {self.port}")

        _LOGGER.info("Serial port opened successfully, testing Modbus communication...")

        try:
            result = await self._client.read_input_registers(TEST_REGISTER, 1)
        except Exception as err:
            raise ModbusException(f"Modbus test read failed: {err}") from err

        if result.isError():
            raise ModbusException(f"Device did not respond to test read: {result}")

        raw = result.registers[0]
        self._cache["device_status"] = raw
        _LOGGER.info("SANDISOLAR Modbus communication OK (Test Register=%s)", raw)

    async def _ensure_connection(self) -> None:
        if not self._client:
            raise ModbusException("Modbus client not initialized")

        if self._client.connected:
            return

        delay = 1
        while not self._client.connected:
            _LOGGER.warning("Modbus disconnected, reconnecting in %s seconds...", delay)
            await asyncio.sleep(delay)
            try:
                await self._client.connect()
            except Exception:
                pass
            delay = min(delay * 2, 30)

    async def read_input_register(self, key: str) -> Optional[float]:
        reg = INPUT_REGISTERS.get(key)
        if not reg:
            return None

        async with self._lock:
            await self._ensure_connection()
            try:
                result = await self._client.read_input_registers(reg.address, reg.count)
            except Exception:
                return None

        if result.isError():
            return None

        raw = result.registers[0]
        value = raw * reg.scale
        self._cache[key] = value
        return value

    async def read_holding_register(self, key: str) -> Optional[float]:
        reg = HOLDING_REGISTERS.get(key)
        if not reg:
            return None

        async with self._lock:
            await self._ensure_connection()
            try:
                result = await self._client.read_holding_registers(reg.address, reg.count)
            except Exception:
                return None

        if result.isError():
            return None

        raw = result.registers[0]
        value = raw * reg.scale
        self._cache[key] = value
        return value

    async def write_holding_register(self, key: str, value: float) -> bool:
        reg = HOLDING_REGISTERS.get(key)
        if not reg:
            return False

        raw_value = int(value / reg.scale)

        async with self._lock:
            await self._ensure_connection()
            try:
                result = await self._client.write_register(reg.address, raw_value)
            except Exception:
                return False

        if result.isError():
            return False

        self._cache[key] = value
        return True

    async def close(self) -> None:
        if self._client:
            await self._client.close()
