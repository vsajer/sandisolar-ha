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

        self.port: str = entry.data["port"]
        self.baudrate: int = entry.data["baudrate"]
        self.slave: int = entry.data["slave"]
        self.update_interval: int = entry.data["update_interval"]

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Any] = {}

    # -------------------------------------------------------------------------
    # Lifecycle
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
            _LOGGER.warning("SANDISOLAR: Error while closing Modbus client: %s", e)

        self._client = None
        _LOGGER.info("SANDISOLAR: Modbus client closed")

    # -------------------------------------------------------------------------
    # Internal helpers
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
        """Return last cached value for given key."""
        return self._cache.get(key)

    # -------------------------------------------------------------------------
    # Register access – INPUT
    # -------------------------------------------------------------------------

    async def read_input_register(self, key: str) -> Optional[float]:
        """Read and decode input register defined in INPUT_REGISTERS."""
        if key not in INPUT_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown input register key '%s'", key)
            return None

        reg = INPUT_REGISTERS[key]

        async with self._lock:
            try:
                await self._ensure_connection()
            except ModbusException as e:
                _LOGGER.error("SANDISOLAR: Connection error before input read %s: %s", key, e)
                return None

            try:
                self._client.unit_id = self.slave
                result = await self._client.read_input_registers(
                    address=reg.address,
                    count=reg.count,
                )
            except Exception as e:
                _LOGGER.error("SANDISOLAR: Read error %s: %s", key, e)
                return None

        if result.isError():
            _LOGGER.error("SANDISOLAR: Modbus error reading %s: %s", key, result)
            return None

        # 16/32bit decode
        if reg.count == 2:
            raw = (result.registers[0] << 16) | result.registers[1]
            bits = 32
        else:
            raw = result.registers[0]
            bits = 16

        # signed/unsigned
        if reg.signed:
            max_val = 1 << (bits - 1)
            if raw >= max_val:
                raw -= 1 << bits

        value = raw * reg.scale
        self._cache[key] = value
        return value

    # -------------------------------------------------------------------------
    # Register access – HOLDING (read)
    # -------------------------------------------------------------------------

    async def read_holding_register(self, key: str) -> Optional[float]:
        """Read and decode holding register defined in HOLDING_REGISTERS."""
        if key not in HOLDING_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown holding register key '%s'", key)
            return None

        reg = HOLDING_REGISTERS[key]

        async with self._lock:
            try:
                await self._ensure_connection()
            except ModbusException as e:
                _LOGGER.error("SANDISOLAR: Connection error before holding read %s: %s", key, e)
                return None

            try:
                self._client.unit_id = self.slave
                result = await self._client.read_holding_registers(
                    address=reg.address,
                    count=reg.count,
                )
            except Exception as e:
                _LOGGER.error("SANDISOLAR: Holding read error %s: %s", key, e)
                return None

        if result.isError():
            _LOGGER.error("SANDISOLAR: Modbus error reading holding %s: %s", key, result)
            return None

        # Většina holding registrů u tebe je 1x16bit → jednoduché dekódování
        raw = result.registers[0]
        value = raw * reg.scale
        self._cache[key] = value
        return value

    # -------------------------------------------------------------------------
    # Register access – HOLDING (write)
    # -------------------------------------------------------------------------

    async def write_holding_register(self, key: str, value: float) -> bool:
        """Write value to holding register defined in HOLDING_REGISTERS."""
        if key not in HOLDING_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown holding register key '%s'", key)
            return False

        reg = HOLDING_REGISTERS[key]

        # scale → raw
        try:
            raw = int(round(value / reg.scale))
        except Exception as e:
            _LOGGER.error("SANDISOLAR: Scaling error for %s (%s): %s", key, value, e)
            return False

        async with self._lock:
            try:
                await self._ensure_connection()
            except ModbusException as e:
                _LOGGER.error("SANDISOLAR: Connection error before write %s: %s", key, e)
                return False

            try:
                self._client.unit_id = self.slave
                result = await self._client.write_register(
                    address=reg.address,
                    value=raw,
                )
            except Exception as e:
                _LOGGER.error("SANDISOLAR: Write error %s: %s", key, e)
                return False

        if result.isError():
            _LOGGER.error("SANDISOLAR: Modbus error writing %s: %s", key, result)
            return False

        # po úspěšném zápisu aktualizuj cache
        self._cache[key] = value
        return True
