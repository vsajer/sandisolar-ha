import asyncio
import logging
from pymodbus.client import AsyncModbusSerialClient

_LOGGER = logging.getLogger(__name__)


class SandiSolarHub:
    """Modbus RTU hub for SANDISOLAR SD‑PRO‑EU (pymodbus 3.2.11)."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        self._port = entry.data.get("port")
        self._baudrate = entry.data.get("baudrate", 9600)
        self._slave_id = entry.data.get("slave", 1)
        self._update_interval = entry.data.get("update_interval", 10)

        self._parity = "N"
        self._stopbits = 1
        self._bytesize = 8

        self._client = None
        self._lock = asyncio.Lock()

        self._cache = {}

    async def async_init(self):
        return await self.connect()

    async def connect(self):
        try:
            self._client = AsyncModbusSerialClient(
                port=self._port,
                baudrate=self._baudrate,
                parity=self._parity,
                stopbits=self._stopbits,
                bytesize=self._bytesize,
                timeout=2,
            )

            ok = await self._client.connect()

            if not ok:
                _LOGGER.error("Failed to connect to Modbus device on %s", self._port)
                self._client = None
                return False

            _LOGGER.info("Connected to Modbus device on %s", self._port)
            return True

        except Exception as e:
            _LOGGER.error("Error connecting Modbus client: %s", e)
            self._client = None
            return False

    async def close(self):
        if self._client:
            try:
                await self._client.close()
            except Exception as e:
                _LOGGER.warning("Error closing Modbus client: %s", e)

        self._client = None

    # ---------------------------------------------------------
    # INPUT REGISTERS
    # ---------------------------------------------------------

    async def read_input_register(self, register):
        async with self._lock:
            if not self._client:
                return None

            try:
                result = await self._client.read_input_registers(
                    register,
                    1,
                    unit=self._slave_id,
                )

                if result.isError():
                    return None

                value = result.registers[0]
                self._cache[register] = value
                return value

            except Exception as e:
                _LOGGER.error("Exception reading input register %s: %s", register, e)
                return None

    # ---------------------------------------------------------
    # HOLDING REGISTERS
    # ---------------------------------------------------------

    async def read_holding_register(self, register):
        async with self._lock:
            if not self._client:
                return None

            try:
                result = await self._client.read_holding_registers(
                    register,
                    1,
                    unit=self._slave_id,
                )

                if result.isError():
                    return None

                value = result.registers[0]
                self._cache[register] = value
                return value

            except Exception as e:
                _LOGGER.error("Exception reading holding register %s: %s", register, e)
                return None

    async def write_holding_register(self, register, value):
        async with self._lock:
            if not self._client:
                return False

            try:
                result = await self._client.write_register(
                    register,
                    value,
                    unit=self._slave_id,
                )

                if result.isError():
                    return False

                self._cache[register] = value
                return True

            except Exception as e:
                _LOGGER.error("Exception writing holding register %s: %s", register, e)
                return False
