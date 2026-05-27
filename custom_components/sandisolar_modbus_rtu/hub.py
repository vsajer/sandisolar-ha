import asyncio
import logging
from pymodbus.client import AsyncModbusSerialClient

_LOGGER = logging.getLogger(__name__)


class SandiSolarHub:
    """Main Modbus RTU hub for SANDISOLAR SD‑PRO‑EU."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        # Config from config_flow
        self._port = entry.data.get("port")
        self._baudrate = entry.data.get("baudrate", 9600)
        self._slave_id = entry.data.get("slave", 1)
        self._update_interval = entry.data.get("update_interval", 10)

        # Fixed Modbus RTU parameters
        self._parity = "N"
        self._stopbits = 1
        self._bytesize = 8

        # Modbus client
        self._client = None
        self._lock = asyncio.Lock()

        # Cache for all registers
        self._cache = {}

    # ---------------------------------------------------------
    # INIT
    # ---------------------------------------------------------

    async def async_init(self):
        """Initialize Modbus connection."""
        return await self.connect()

    async def connect(self):
        """Connect to Modbus RTU device."""
        try:
            self._client = AsyncModbusSerialClient(
                port=self._port,
                baudrate=self._baudrate,
                parity=self._parity,
                stopbits=self._stopbits,
                bytesize=self._bytesize,
                timeout=2,
            )

            connected = await self._client.connect()

            if not connected:
                _LOGGER.error("Failed to connect to Modbus device on %s", self._port)
                self._client = None
                return False

            _LOGGER.info("Connected to Modbus device on %s", self._port)
            return True

        except Exception as e:
            _LOGGER.error("Error connecting Modbus client: %s", e)
            self._client = None
            return False

    # ---------------------------------------------------------
    # CLOSE
    # ---------------------------------------------------------

    async def close(self):
        """Close Modbus client safely."""
        if self._client:
            try:
                await self._client.close()
                _LOGGER.info("Modbus client closed")
            except Exception as e:
                _LOGGER.warning("Error closing Modbus client: %s", e)

        self._client = None

    # ---------------------------------------------------------
    # INPUT REGISTERS (sensors)
    # ---------------------------------------------------------

    async def read_input_register(self, register):
        """Read input register (read‑only)."""
        async with self._lock:
            if not self._client:
                _LOGGER.warning("Modbus client not connected")
                return None

            try:
                result = await self._client.read_input_registers(
                    address=register,
                    count=1,
                    unit=self._slave_id,
                )

                if result.isError():
                    _LOGGER.warning("Modbus error reading input register %s: %s", register, result)
                    return None

                value = result.registers[0]
                self._cache[register] = value
                return value

            except Exception as e:
                _LOGGER.error("Exception reading input register %s: %s", register, e)
                return None

    # ---------------------------------------------------------
    # HOLDING REGISTERS (switch, number, select)
    # ---------------------------------------------------------

    async def read_holding_register(self, register):
        """Read holding register (read/write)."""
        async with self._lock:
            if not self._client:
                _LOGGER.warning("Modbus client not connected")
                return None

            try:
                result = await self._client.read_holding_registers(
                    address=register,
                    count=1,
                    unit=self._slave_id,
                )

                if result.isError():
                    _LOGGER.warning("Modbus error reading holding register %s: %s", register, result)
                    return None

                value = result.registers[0]
                self._cache[register] = value
                return value

            except Exception as e:
                _LOGGER.error("Exception reading holding register %s: %s", register, e)
                return None

    async def write_holding_register(self, register, value):
        """Write holding register."""
        async with self._lock:
            if not self._client:
                _LOGGER.warning("Modbus client not connected")
                return False

            try:
                result = await self._client.write_register(
                    address=register,
                    value=value,
                    unit=self._slave_id,
                )

                if result.isError():
                    _LOGGER.warning("Modbus error writing register %s: %s", register, result)
                    return False

                # Update cache immediately
                self._cache[register] = value
                return True

            except Exception as e:
                _LOGGER.error("Exception writing holding register %s: %s", register, e)
                return False
