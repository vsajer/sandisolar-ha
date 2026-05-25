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


ATTRIBUTE_GROUPS = {
    "pv": ["pv_voltage", "pv_current", "pv_power", "pv_status"],
    "battery": ["battery_voltage", "battery_current", "battery_temperature", "battery_soc", "battery_status"],
    "grid": ["grid_voltage", "grid_frequency", "grid_power", "grid_status"],
    "inverter": ["inverter_status", "output_load", "temperature", "error_code"],
}


class SandiSolarModbusHub:
    """Main Modbus RTU hub for SANDISOLAR."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self.port = entry.data.get("port", DEFAULT_PORT)
        self.baudrate = entry.data.get("baudrate", 9600)
        self.slave_id = entry.data.get("slave_id", 1)
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
            result = await self._client.read_input_registers(
                address=TEST_REGISTER,
                count=1,
                slave=self.slave_id,
            )
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
        max_delay = 30

        while not self._client.connected:
            _LOGGER.warning("Modbus disconnected, reconnecting in %s seconds...", delay)
            await asyncio.sleep(delay)

            try:
                await self._client.connect()
            except Exception as err:
                _LOGGER.error("Reconnect failed: %s", err)

            delay = min(delay * 2, max_delay)

        _LOGGER.info("Modbus reconnected successfully")

    async def read_input_register(self, key: str) -> Optional[float]:
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
        value = raw * reg.scale
        self._cache[key] = value
        return value

    async def read_holding_register(self, key: str) -> Optional[float]:
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
        value = raw * reg.scale
        self._cache[key] = value
        return value

    async def write_holding_register(self, key: str, value: float) -> bool:
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

        self._cache[key] = value
        return True

    def get_attributes_for(self, key: str) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {}

        for group, keys in ATTRIBUTE_GROUPS.items():
            if key in keys:
                for k in keys:
                    if k in self._cache:
                        attrs[k] = self._cache[k]

        return attrs

    async def dump_all_registers(self) -> Dict[str, Any]:
        dump: Dict[str, Any] = {}

        for key in INPUT_REGISTERS:
            try:
                dump[key] = await self.read_input_register(key)
            except Exception as err:
                dump[key] = f"ERR: {err}"

        for key in HOLDING_REGISTERS:
            try:
                dump[key] = await self.read_holding_register(key)
            except Exception as err:
                dump[key] = f"ERR: {err}"

        _LOGGER.warning("FULL REGISTER DUMP:\n%s", dump)
        return dump

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            _LOGGER.info("SANDISOLAR Modbus RTU connection closed")
