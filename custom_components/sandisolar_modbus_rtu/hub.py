import asyncio
import logging
from typing import Optional, Dict, Any

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .modbus_map import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)


class SandiSolarModbusHub:
    """Modbus RTU hub for SANDISOLAR SD-PRO-EU using pymodbus 4.x."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self.port = entry.data["port"]
        self.baudrate = entry.data["baudrate"]
        self.slave = entry.data["slave"]
        self.update_interval = entry.data["update_interval"]

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Any] = {}

    async def async_init(self) -> None:
        self._client = AsyncModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=3,
        )

        connected = await self._client.connect()
        if not connected:
            raise ModbusException("Cannot open serial port")

        _LOGGER.info("SANDISOLAR: Connected to %s", self.port)

    async def _ensure_connection(self):
        if not self._client.connected:
            await self._client.connect()

    async def read_input_register(self, key: str):
        reg = INPUT_REGISTERS[key]

        async with self._lock:
            await self._ensure_connection()
            try:
                self._client.unit_id = self.slave
                result = await self._client.read_input_registers(
                    address=reg.address,
                    count=reg.count,
                )
            except Exception as e:
                _LOGGER.error("Read error %s: %s", key, e)
                return None

        if result.isError():
            return None

        raw = (
            (result.registers[0] << 16) | result.registers[1]
            if reg.count == 2
            else result.registers[0]
        )

        if reg.signed:
            bits = 32 if reg.count == 2 else 16
            max_val = 1 << (bits - 1)
            if raw >= max_val:
                raw -= 1 << bits

        value = raw * reg.scale
        self._cache[key] = value
        return value

    async def read_holding_register(self, key: str):
        reg = HOLDING_REGISTERS[key]

        async with self._lock:
            await self._ensure_connection()
            try:
                self._client.unit_id = self.slave
                result = await self._client.read_holding_registers(
                    address=reg.address,
                    count=reg.count,
                )
            except Exception as e:
                _LOGGER.error("Holding read error %s: %s", key, e)
                return None

        if result.isError():
            return None

        raw = result.registers[0]
        value = raw * reg.scale
        self._cache[key] = value
        return value

    async def write_holding_register(self, key: str, value: float):
        reg = HOLDING_REGISTERS[key]
        raw = int(value / reg.scale)

        async with self._lock:
            await self._ensure_connection()
            try:
                self._client.unit_id = self.slave
                result = await self._client.write_register(
                    address=reg.address,
                    value=raw,
                )
            except Exception as e:
                _LOGGER.error("Write error %s: %s", key, e)
                return False

        return not result.isError()

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
