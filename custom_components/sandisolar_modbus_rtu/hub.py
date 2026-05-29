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

    # -------------------------------------------------------------------------
    # INIT
    # -------------------------------------------------------------------------

    async def async_init(self) -> None:
        """Initialize and connect Modbus client."""
        _LOGGER.info(
            "SANDISOLAR: Initializing Modbus client on %s @ %s baud (slave %s)",
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

        connected = await self._client.connect()

        if not connected or not getattr(self._client, "connected", False):
            self._client = None
            raise ModbusException(f"SANDISOLAR: Cannot open serial port {self.port}")

        _LOGGER.info("SANDISOLAR: Connected to %s", self.port)

    # -------------------------------------------------------------------------
    # CLOSE
    # -------------------------------------------------------------------------

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

        except Exception as e:
            _LOGGER.warning("SANDISOLAR: Error closing Modbus: %s", e)

        self._client = None
        _LOGGER.info("SANDISOLAR: Modbus client closed")

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------

    async def _ensure_connection(self) -> None:
        """Ensure client exists and is connected."""
        if self._client is None:
            raise ModbusException("SANDISOLAR: Modbus client not initialized")

        if not getattr(self._client, "connected", False):
            _LOGGER.warning("SANDISOLAR: Modbus client disconnected, reconnecting...")

            connected = await self._client.connect()

            if not connected or not getattr(self._client, "connected", False):
                raise ModbusException("SANDISOLAR: Failed to reconnect Modbus client")

    def get_cached(self, key: str) -> Optional[Any]:
        """Return cached value."""
        return self._cache.get(key)

    # -------------------------------------------------------------------------
    # INPUT REGISTERS
    # -------------------------------------------------------------------------

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

            except Exception as e:
                _LOGGER.error("SANDISOLAR: Read error %s: %s", key, e)
                return None

        if result is None or result.isError():
            _LOGGER.debug("SANDISOLAR: Read returned error for %s", key)
            return None

        raw = self._decode(result.registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    # -------------------------------------------------------------------------
    # HOLDING REGISTERS READ
    # -------------------------------------------------------------------------

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

            except Exception as e:
                _LOGGER.error("SANDISOLAR: Holding read error %s: %s", key, e)
                return None

        if result is None or result.isError():
            _LOGGER.debug("SANDISOLAR: Holding read returned error for %s", key)
            return None

        raw = self._decode(result.registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    # -------------------------------------------------------------------------
    # HOLDING REGISTERS WRITE
    # -------------------------------------------------------------------------

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

            except Exception as e:
                _LOGGER.error("SANDISOLAR: Write error %s: %s", key, e)
                return False

        if result is None or result.isError():
            _LOGGER.debug("SANDISOLAR: Write returned error for %s", key)
            return False

        self._cache[key] = value
        return True

    # -------------------------------------------------------------------------
    # DECODER
    # -------------------------------------------------------------------------

    def _decode(self, registers, signed):
        """Decode 16-bit or 32-bit Modbus register values."""
        if not registers:
            return 0

        if len(registers) == 1:
            val = registers[0]

            if signed and val > 32767:
                val -= 65536

            return val

        if len(registers) == 2:
            high, low = registers
            val = (high << 16) | low

            if signed and val > 0x7FFFFFFF:
                val -= 0x100000000

            return val

        return 0
