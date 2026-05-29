import asyncio
import logging
from typing import Optional, Dict, Any

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .modbus_map import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)


class SandiSolarModbusHub:
    """Modbus RTU hub for SANDISOLAR SD-PRO-EU."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        self.port = entry.data["port"]
        self.baudrate = entry.data["baudrate"]
        self.slave = entry.data["slave"]
        self.update_interval = entry.data.get("update_interval", 10)

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Any] = {}

    async def async_init(self):
        """Initialize Modbus connection."""

        _LOGGER.info(
            "SANDISOLAR: Connecting to %s @ %s baud (unit=%s)",
            self.port,
            self.baudrate,
            self.slave,
        )

        self._client = AsyncModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=2,
        )

        connected = await self._client.connect()

        if not connected:
            self._client = None
            raise ModbusException(
                f"Cannot connect to Modbus device on {self.port}"
            )

        _LOGGER.info("SANDISOLAR: Connected")

    async def close(self):
        """Close Modbus connection."""

        if self._client is None:
            return

        try:
            result = self._client.close()

            if asyncio.iscoroutine(result):
                await result

        except Exception as err:
            _LOGGER.warning(
                "SANDISOLAR: Error while closing Modbus client: %s",
                err,
            )

        self._client = None

    async def _ensure_connection(self):
        """Reconnect if needed."""

        if self._client is None:
            await self.async_init()
            return

        if not getattr(self._client, "connected", False):
            _LOGGER.warning(
                "SANDISOLAR: Connection lost, reconnecting..."
            )

            connected = await self._client.connect()

            if not connected:
                raise ModbusException(
                    "Failed to reconnect Modbus client"
                )

    def get_cached(self, key):
        return self._cache.get(key)

    async def read_input_register(self, key):
        """Read Input Register."""

        if key not in INPUT_REGISTERS:
            _LOGGER.error(
                "SANDISOLAR: Unknown input register '%s'",
                key,
            )
            return None

        reg = INPUT_REGISTERS[key]

        async with self._lock:
            try:
                await self._ensure_connection()

                result = await self._client.read_input_registers(
                    address=reg.address,
                    count=reg.count,
                    unit=self.slave,
                )

            except Exception as err:
                _LOGGER.error(
                    "SANDISOLAR: Input read error %s: %s",
                    key,
                    err,
                )
                return None

        if result is None or result.isError():
            return None

        raw = self._decode(
            result.registers,
            reg.signed,
        )

        value = raw * reg.scale

        self._cache[key] = value

        return value

    async def read_holding_register(self, key):
        """Read Holding Register."""

        if key not in HOLDING_REGISTERS:
            _LOGGER.error(
                "SANDISOLAR: Unknown holding register '%s'",
                key,
            )
            return None

        reg = HOLDING_REGISTERS[key]

        async with self._lock:
            try:
                await self._ensure_connection()

                result = await self._client.read_holding_registers(
                    address=reg.address,
                    count=reg.count,
                    unit=self.slave,
                )

            except Exception as err:
                _LOGGER.error(
                    "SANDISOLAR: Holding read error %s: %s",
                    key,
                    err,
                )
                return None

        if result is None or result.isError():
            return None

        raw = self._decode(
            result.registers,
            reg.signed,
        )

        value = raw * reg.scale

        self._cache[key] = value

        return value

    async def write_holding_register(self, key, value):
        """Write Holding Register."""

        if key not in HOLDING_REGISTERS:
            _LOGGER.error(
                "SANDISOLAR: Unknown holding register '%s'",
                key,
            )
            return False

        reg = HOLDING_REGISTERS[key]

        try:
            raw = int(round(value / reg.scale))
        except Exception:
            raw = int(value)

        async with self._lock:
            try:
                await self._ensure_connection()

                result = await self._client.write_register(
                    address=reg.address,
                    value=raw,
                    unit=self.slave,
                )

            except Exception as err:
                _LOGGER.error(
                    "SANDISOLAR: Write error %s: %s",
                    key,
                    err,
                )
                return False

        if result is None or result.isError():
            return False

        self._cache[key] = value

        return True

    def _decode(self, registers, signed=False):
        """Decode Modbus values."""

        if not registers:
            return 0

        if len(registers) == 1:
            value = registers[0]

            if signed and value > 32767:
                value -= 65536

            return value

        if len(registers) == 2:
            high, low = registers

            value = (high << 16) | low

            if signed and value > 0x7FFFFFFF:
                value -= 0x100000000

            return value

        value = 0

        for reg in registers:
            value = (value << 16) | reg

        return value
