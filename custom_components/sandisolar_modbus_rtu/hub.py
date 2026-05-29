import asyncio
import logging
from typing import Optional, Dict, Any

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .modbus_map import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)


class SandiSolarModbusHub:
    """Modbus RTU hub for SANDISOLAR SD-PRO-EU using pymodbus 3.2.11."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        self.port: str = entry.data["port"]
        self.baudrate: int = entry.data["baudrate"]
        self.slave: int = entry.data["slave"]
        self.update_interval: int = entry.data.get("update_interval", 10)

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Any] = {}

    async def async_init(self) -> None:
        """Initialize and connect Modbus client."""
        _LOGGER.info(
            "SANDISOLAR: Initializing Modbus RTU on %s @ %s baud, slave %s",
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
            timeout=3,
        )

        try:
            connected = await self._client.connect()
        except Exception as err:
            self._client = None
            raise ModbusException(
                f"SANDISOLAR: Cannot connect to serial port {self.port}: {err}"
            ) from err

        if not connected or not getattr(self._client, "connected", False):
            self._client = None
            raise ModbusException(f"SANDISOLAR: Cannot open serial port {self.port}")

        _LOGGER.info("SANDISOLAR: Connected to %s", self.port)

    async def close(self) -> None:
        """Safely close Modbus client."""
        client = self._client

        if client is None:
            return

        try:
            close_fn = getattr(client, "close", None)

            if callable(close_fn):
                result = close_fn()

                if asyncio.iscoroutine(result):
                    await result

        except Exception as err:
            _LOGGER.warning("SANDISOLAR: Error closing Modbus client: %s", err)

        self._client = None
        _LOGGER.info("SANDISOLAR: Modbus client closed")

    async def _ensure_connection(self) -> None:
        """Ensure client exists and is connected."""
        if self._client is None:
            _LOGGER.warning("SANDISOLAR: Modbus client missing, recreating...")
            await self.async_init()
            return

        if not getattr(self._client, "connected", False):
            _LOGGER.warning("SANDISOLAR: Modbus disconnected, reconnecting...")

            try:
                connected = await self._client.connect()
            except Exception as err:
                raise ModbusException(
                    f"SANDISOLAR: Reconnect failed on {self.port}: {err}"
                ) from err

            if not connected or not getattr(self._client, "connected", False):
                raise ModbusException("SANDISOLAR: Failed to reconnect Modbus client")

    def get_cached(self, key: str) -> Optional[Any]:
        """Return cached value."""
        return self._cache.get(key)

    async def read_input_register(self, key: str) -> Optional[float]:
        """Read one defined input register by key."""
        if key not in INPUT_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown input register key '%s'", key)
            return None

        reg = INPUT_REGISTERS[key]

        async with self._lock:
            try:
                await self._ensure_connection()

                result = await self._client.read_input_registers(
                    address=reg.address,
                    count=reg.count,
                    slave=self.slave,
                )

            except Exception as err:
                _LOGGER.error("SANDISOLAR: Input read error %s: %s", key, err)
                return None

        if result is None:
            _LOGGER.debug("SANDISOLAR: Input read returned None for %s", key)
            return None

        if result.isError():
            _LOGGER.debug("SANDISOLAR: Input read Modbus error for %s: %s", key, result)
            return None

        registers = getattr(result, "registers", None)

        if not registers:
            _LOGGER.debug("SANDISOLAR: Input read empty registers for %s", key)
            return None

        raw = self._decode(registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    async def read_holding_register(self, key: str) -> Optional[float]:
        """Read one defined holding register by key."""
        if key not in HOLDING_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown holding register key '%s'", key)
            return None

        reg = HOLDING_REGISTERS[key]

        async with self._lock:
            try:
                await self._ensure_connection()

                result = await self._client.read_holding_registers(
                    address=reg.address,
                    count=reg.count,
                    slave=self.slave,
                )

            except Exception as err:
                _LOGGER.error("SANDISOLAR: Holding read error %s: %s", key, err)
                return None

        if result is None:
            _LOGGER.debug("SANDISOLAR: Holding read returned None for %s", key)
            return None

        if result.isError():
            _LOGGER.debug("SANDISOLAR: Holding read Modbus error for %s: %s", key, result)
            return None

        registers = getattr(result, "registers", None)

        if not registers:
            _LOGGER.debug("SANDISOLAR: Holding read empty registers for %s", key)
            return None

        raw = self._decode(registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    async def write_holding_register(self, key: str, value: float) -> bool:
        """Write one defined holding register by key."""
        if key not in HOLDING_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown holding register key '%s'", key)
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
                    slave=self.slave,
                )

            except Exception as err:
                _LOGGER.error(
                    "SANDISOLAR: Holding write error %s=%s raw=%s: %s",
                    key,
                    value,
                    raw,
                    err,
                )
                return False

        if result is None:
            _LOGGER.debug("SANDISOLAR: Holding write returned None for %s", key)
            return False

        if result.isError():
            _LOGGER.debug("SANDISOLAR: Holding write Modbus error for %s: %s", key, result)
            return False

        self._cache[key] = value
        return True

    def _decode(self, registers, signed):
        """Decode 16-bit or 32-bit Modbus values.

        SANDISOLAR documentation uses High/Low order:
        - 250 = PpvAll H
        - 251 = PpvAll L
        - 328 = Pactogrid total H
        - 329 = Pactogrid total L
        """

        if not registers:
            return 0

        if len(registers) == 1:
            val = registers[0]

            if signed and val > 0x7FFF:
                val -= 0x10000

            return val

        if len(registers) == 2:
            high, low = registers
            val = (high << 16) | low

            if signed and val > 0x7FFFFFFF:
                val -= 0x100000000

            return val

        val = 0
        for register in registers:
            val = (val << 16) | register

        return val
