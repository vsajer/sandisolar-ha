import logging
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .const import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)


class SandiSolarModbusHub:
    """Main Modbus RTU hub for SANDISOLAR SD‑PRO‑EU."""

    def __init__(self, hass, port, baudrate, slave_id):
        self._hass = hass
        self._port = port
        self._baudrate = baudrate
        self._slave = slave_id

        self._client = None
        self._cache = {}

    # ------------------------------------------------------------------
    # INIT & CONNECT
    # ------------------------------------------------------------------

    async def connect(self):
        """Initialize Modbus RTU client."""
        self._client = AsyncModbusSerialClient(
            port=self._port,
            baudrate=self._baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1,
        )

        await self._client.connect()
        if not self._client.connected:
            _LOGGER.error("SANDISOLAR: Modbus connection failed")
        else:
            _LOGGER.info("SANDISOLAR: Modbus connected")

    # ------------------------------------------------------------------
    # CLOSE CONNECTION
    # ------------------------------------------------------------------

    async def close(self):
        """Close Modbus connection."""
        if self._client:
            try:
                await self._client.close()
                _LOGGER.info("SANDISOLAR: Modbus connection closed")
            except Exception as e:
                _LOGGER.error("SANDISOLAR: Error closing Modbus: %s", e)

    # ------------------------------------------------------------------
    # CACHE
    # ------------------------------------------------------------------

    def get_cached(self, key):
        return self._cache.get(key)

    def set_cached(self, key, value):
        self._cache[key] = value

    # ------------------------------------------------------------------
    # GENERIC READERS
    # ------------------------------------------------------------------

    async def _read_registers(self, address, count):
        """Low-level Modbus read for INPUT registers."""
        if not self._client or not self._client.connected:
            return None

        try:
            rr = await self._client.read_input_registers(
                address=address,
                count=count,
                unit=self._slave
            )
            if rr.isError():
                return None
            return rr.registers

        except ModbusException as e:
            _LOGGER.error("SANDISOLAR: Modbus read error: %s", e)
            return None

    async def _read_holding(self, address, count):
        """Low-level Modbus read for HOLDING registers."""
        if not self._client or not self._client.connected:
            return None

        try:
            rr = await self._client.read_holding_registers(
                address=address,
                count=count,
                unit=self._slave
            )
            if rr.isError():
                return None
            return rr.registers

        except ModbusException as e:
            _LOGGER.error("SANDISOLAR: Modbus holding read error: %s", e)
            return None

    # ------------------------------------------------------------------
    # HIGH-LEVEL READERS
    # ------------------------------------------------------------------

    async def read_input_register(self, key):
        """Read and scale INPUT register."""
        reg = INPUT_REGISTERS.get(key)
        if not reg:
            _LOGGER.warning("SANDISOLAR: Unknown input register key '%s'", key)
            return None

        raw = await self._read_registers(reg.address, reg.count)
        if raw is None:
            return None

        value = self._decode(raw, reg.signed)
        return value * reg.scale

    async def read_holding_register(self, key):
        """Read and scale HOLDING register."""
        reg = HOLDING_REGISTERS.get(key)
        if not reg:
            _LOGGER.warning("SANDISOLAR: Unknown holding register key '%s'", key)
            return None

        raw = await self._read_holding(reg.address, reg.count)
        if raw is None:
            return None

        value = self._decode(raw, reg.signed)
        scaled = value * reg.scale

        # Cache device info
        if key in ("device_name", "device_model"):
            self.set_cached(key, scaled)

        return scaled

    # ------------------------------------------------------------------
    # WRITE HOLDING REGISTER
    # ------------------------------------------------------------------

    async def write_holding_register(self, key, value):
        """Write scaled value to a holding register."""
        reg = HOLDING_REGISTERS.get(key)
        if not reg:
            _LOGGER.warning("SANDISOLAR: Unknown holding register key '%s'", key)
            return False

        if not self._client or not self._client.connected:
            _LOGGER.error("SANDISOLAR: Cannot write, Modbus not connected")
            return False

        # Reverse scale (HA → raw)
        try:
            raw_value = int(value / reg.scale)
        except Exception:
            raw_value = int(value)

        try:
            rq = await self._client.write_register(
                address=reg.address,
                value=raw_value,
                unit=self._slave
            )
            if rq.isError():
                _LOGGER.error("SANDISOLAR: Write error for %s", key)
                return False

            return True

        except Exception as e:
            _LOGGER.error("SANDISOLAR: Exception during write: %s", e)
            return False

    # ------------------------------------------------------------------
    # DECODER
    # ------------------------------------------------------------------

    def _decode(self, registers, signed):
        """Decode 1–2 register values."""
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
