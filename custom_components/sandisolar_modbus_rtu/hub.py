import asyncio
import logging
from pymodbus.client import AsyncModbusSerialClient

_LOGGER = logging.getLogger(__name__)


class SandiSolarHub:
    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        # Načtení konfigurace z config_flow
        self._port = entry.data.get("port")
        self._baudrate = entry.data.get("baudrate", 9600)
        self._slave_id = entry.data.get("slave", 1)
        self._update_interval = entry.data.get("update_interval", 10)

        # Fixní parametry podle protokolu
        self._parity = "N"
        self._stopbits = 1
        self._bytesize = 8

        self._client = None
        self._lock = asyncio.Lock()

    async def async_init(self):
        """Initialize Modbus connection."""
        return await self.connect()

    async def connect(self):
        """Initialize Modbus RTU client."""
        try:
            self._client = AsyncModbusSerialClient(
                port=self._port,
                baudrate=self._baudrate,
                parity=self._parity,
                stopbits=self._stopbits,
                bytesize=self._bytesize,
                timeout=2,
            )

            connection = await self._client.connect()

            if not connection:
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
        """Safely close Modbus client."""
        if self._client is None:
            return

        try:
            await self._client.close()
            _LOGGER.info("Modbus client closed")
        except Exception as e:
            _LOGGER.warning("Error closing Modbus client: %s", e)

        self._client = None

    async def read_input_register(self, register):
        """Thread‑safe Modbus read."""
        async with self._lock:
            if self._client is None:
                _LOGGER.warning("Modbus client not connected")
                return None

            try:
                result = await self._client.read_input_registers(
                    address=register,
                    count=1,
                    slave=self._slave_id,
                )

                if result.isError():
                    _LOGGER.warning("Modbus error reading register %s: %s", register, result)
                    return None

                return result.registers[0]

            except Exception as e:
                _LOGGER.error("Exception reading register %s: %s", register, e)
                return None
