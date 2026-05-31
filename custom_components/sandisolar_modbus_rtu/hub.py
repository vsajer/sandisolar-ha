import asyncio
import logging
import time
from typing import Optional, Dict, Any

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .modbus_map import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)


# Jak dlouho může čtení čekat na volný Modbus.
# Když je linka vytížená a máme cache, vrátíme cache místo čekání.
READ_LOCK_TIMEOUT = 1.0

# Zápis je důležitější než běžné čtení, takže může čekat déle.
WRITE_LOCK_TIMEOUT = 5.0

# Malá pauza mezi RTU požadavky.
# RS485 není závodní sběrnice, spíš "mluv jeden po druhém".
MIN_REQUEST_GAP = 0.08


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
        self._last_request_time = 0.0

    async def async_init(self):
        """Initialize Modbus client."""
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
            raise ModbusException(f"Cannot connect to Modbus device on {self.port}")

        # Důležité pro tvoji verzi pymodbus:
        # nepředávat slave= ani unit= do čtení/zápisu.
        self._client.unit_id = self.slave

        _LOGGER.info("SANDISOLAR: Connected to %s", self.port)

    async def close(self):
        """Close Modbus client."""
        if self._client is None:
            return

        try:
            result = self._client.close()
            if asyncio.iscoroutine(result):
                await result
        except Exception as err:
            _LOGGER.warning("SANDISOLAR: Error closing Modbus client: %s", err)

        self._client = None

    async def _ensure_connection(self):
        """Ensure Modbus client is connected."""
        if self._client is None:
            await self.async_init()
            return

        if not getattr(self._client, "connected", False):
            connected = await self._client.connect()
            if not connected:
                raise ModbusException("Failed to reconnect Modbus client")

        self._client.unit_id = self.slave

    async def _request_gap(self):
        """Add small spacing between Modbus RTU requests."""
        now = time.monotonic()
        elapsed = now - self._last_request_time

        if elapsed < MIN_REQUEST_GAP:
            await asyncio.sleep(MIN_REQUEST_GAP - elapsed)

        self._last_request_time = time.monotonic()

    async def _acquire_lock(self, timeout: float) -> bool:
        """Acquire Modbus lock with timeout."""
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def get_cached(self, key):
        """Return cached value."""
        return self._cache.get(key)

    async def read_input_register(self, key):
        """Read input register by key."""
        if key not in INPUT_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown input register '%s'", key)
            return None

        # Když je Modbus zaneprázdněný, raději vrať cache než čekat 10+ sekund.
        if self._lock.locked() and key in self._cache:
            return self._cache[key]

        locked = await self._acquire_lock(READ_LOCK_TIMEOUT)

        if not locked:
            if key in self._cache:
                _LOGGER.debug(
                    "SANDISOLAR: Input read skipped for %s, returning cached value",
                    key,
                )
                return self._cache[key]

            _LOGGER.debug(
                "SANDISOLAR: Input read skipped for %s, Modbus busy and no cache",
                key,
            )
            return None

        try:
            return await self._read_input_register_locked(key)
        finally:
            self._lock.release()

    async def read_holding_register(self, key):
        """Read holding register by key."""
        if key not in HOLDING_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown holding register '%s'", key)
            return None

        # Když je Modbus zaneprázdněný, raději vrať cache než čekat 10+ sekund.
        if self._lock.locked() and key in self._cache:
            return self._cache[key]

        locked = await self._acquire_lock(READ_LOCK_TIMEOUT)

        if not locked:
            if key in self._cache:
                _LOGGER.debug(
                    "SANDISOLAR: Holding read skipped for %s, returning cached value",
                    key,
                )
                return self._cache[key]

            _LOGGER.debug(
                "SANDISOLAR: Holding read skipped for %s, Modbus busy and no cache",
                key,
            )
            return None

        try:
            return await self._read_holding_register_locked(key)
        finally:
            self._lock.release()

    async def write_holding_register(self, key, value):
        """Write holding register by key."""
        if key not in HOLDING_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown holding register '%s'", key)
            return False

        locked = await self._acquire_lock(WRITE_LOCK_TIMEOUT)

        if not locked:
            _LOGGER.error(
                "SANDISOLAR: Write skipped for %s=%s, Modbus busy",
                key,
                value,
            )
            return False

        try:
            return await self._write_holding_register_locked(key, value)
        finally:
            self._lock.release()

    async def _read_input_register_locked(self, key):
        """Read input register. Caller must hold lock."""
        reg = INPUT_REGISTERS[key]

        try:
            await self._ensure_connection()
            await self._request_gap()

            self._client.unit_id = self.slave

            result = await self._client.read_input_registers(
                address=reg.address,
                count=reg.count,
            )

        except asyncio.CancelledError:
            _LOGGER.debug("SANDISOLAR: Input read cancelled %s", key)
            raise

        except Exception as err:
            _LOGGER.error("SANDISOLAR: Input read error %s: %s", key, err)
            return None

        if result is None:
            _LOGGER.error("SANDISOLAR: Input read returned None for %s", key)
            return None

        if result.isError():
            _LOGGER.error("SANDISOLAR: Input read error %s: %s", key, result)
            return None

        raw = self._decode(result.registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    async def _read_holding_register_locked(self, key):
        """Read holding register. Caller must hold lock."""
        reg = HOLDING_REGISTERS[key]

        try:
            await self._ensure_connection()
            await self._request_gap()

            self._client.unit_id = self.slave

            result = await self._client.read_holding_registers(
                address=reg.address,
                count=reg.count,
            )

        except asyncio.CancelledError:
            _LOGGER.debug("SANDISOLAR: Holding read cancelled %s", key)
            raise

        except Exception as err:
            _LOGGER.error("SANDISOLAR: Holding read error %s: %s", key, err)
            return None

        if result is None:
            _LOGGER.error("SANDISOLAR: Holding read returned None for %s", key)
            return None

        if result.isError():
            _LOGGER.error("SANDISOLAR: Holding read error %s: %s", key, result)
            return None

        raw = self._decode(result.registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    async def _write_holding_register_locked(self, key, value):
        """Write holding register. Caller must hold lock."""
        reg = HOLDING_REGISTERS[key]
        raw = int(round(value / reg.scale))

        try:
            await self._ensure_connection()
            await self._request_gap()

            self._client.unit_id = self.slave

            result = await self._client.write_register(
                address=reg.address,
                value=raw,
            )

        except asyncio.CancelledError:
            _LOGGER.debug("SANDISOLAR: Write cancelled %s=%s", key, value)
            raise

        except Exception as err:
            _LOGGER.error("SANDISOLAR: Write error %s=%s: %s", key, value, err)
            return False

        if result is None:
            _LOGGER.error("SANDISOLAR: Write returned None for %s=%s", key, value)
            return False

        if result.isError():
            _LOGGER.error("SANDISOLAR: Write error %s=%s: %s", key, value, result)
            return False

        self._cache[key] = value
        return True

    def _decode(self, registers, signed=False):
        """Decode Modbus registers."""
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
