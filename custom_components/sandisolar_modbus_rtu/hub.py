import asyncio
import logging
import time
from typing import Optional, Dict, Any

from homeassistant.exceptions import ConfigEntryNotReady

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.exceptions import ModbusException

from .modbus_map import INPUT_REGISTERS, HOLDING_REGISTERS

_LOGGER = logging.getLogger(__name__)


# Jak dlouho může běžné čtení input registrů čekat na volný Modbus.
# Input registry jsou průběžná měření, takže při vytížení linky můžeme vrátit cache.
READ_LOCK_TIMEOUT = 1.0

# Zápis a čtení holding registrů jsou důležitější.
# Holding registry jsou nastavení měniče a mohou se změnit i přímo na LCD.
WRITE_LOCK_TIMEOUT = 5.0

# Malá pauza mezi RTU požadavky.
# RS485 není závodní sběrnice, spíš "mluv jeden po druhém".
MIN_REQUEST_GAP = 0.12

# Krátká pauza před opakováním neúspěšného požadavku.
REQUEST_RETRY_DELAY = 0.25

# Tvrdý timeout pro jednu Modbus operaci.
# Když pymodbus/serial zatuhne, nesmí držet lock navždy.
MODBUS_OPERATION_TIMEOUT = 4.0

# Po kolika po sobě jdoucích chybách klienta zahodit a připojit znovu.
MAX_CONSECUTIVE_ERRORS = 3

# Počet pokusů o připojení při startu integrace.
CONNECT_ATTEMPTS = 3

# Pauza mezi pokusy o připojení.
CONNECT_RETRY_DELAY = 1.0


class SandiSolarModbusHub:
    """Modbus RTU hub for SANDISOLAR SD-PRO-EU."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        self.port = entry.data["port"]
        self.baudrate = entry.data["baudrate"]
        self.slave = entry.data["slave"]

        # Interval ber primárně z Options flow.
        # Díky tomu se změna v Možnosti integrace opravdu použije po reloadu entry.
        self.update_interval = entry.options.get(
            "update_interval",
            entry.data.get("update_interval", 10),
        )

        self._client: Optional[AsyncModbusSerialClient] = None
        self._lock = asyncio.Lock()
        self._cache: Dict[str, Any] = {}
        self._last_request_time = 0.0
        self._consecutive_errors = 0
        self._last_success_time = 0.0

    async def async_init(self):
        """Initialize Modbus client.

        Important:
        If the serial port is temporarily busy, raise ConfigEntryNotReady.
        Home Assistant will retry setup later instead of marking the integration
        as a hard failure.
        """

        # Kdyby po reloadu zůstal starý klient v objektu, nejdřív ho zavři.
        await self.close()

        last_error = None

        for attempt in range(1, CONNECT_ATTEMPTS + 1):
            try:
                self._client = self._create_client()

                connected = await self._client.connect()

                if connected:
                    # Důležité pro tvoji verzi pymodbus:
                    # nepředávat slave= ani unit= do čtení/zápisu.
                    self._client.unit_id = self.slave

                    _LOGGER.info(
                        "SANDISOLAR: Connected to %s, baudrate=%s, slave=%s",
                        self.port,
                        self.baudrate,
                        self.slave,
                    )
                    return

                last_error = f"connect() returned False on attempt {attempt}"

            except Exception as err:
                last_error = err

                _LOGGER.warning(
                    "SANDISOLAR: Modbus connect attempt %s/%s failed on %s: %s",
                    attempt,
                    CONNECT_ATTEMPTS,
                    self.port,
                    err,
                )

            await self._close_client_only()

            if attempt < CONNECT_ATTEMPTS:
                await asyncio.sleep(CONNECT_RETRY_DELAY)

        raise ConfigEntryNotReady(
            f"SANDISOLAR: Cannot connect to Modbus device on {self.port}: {last_error}"
        )

    def _create_client(self):
        """Create Modbus serial client."""

        return AsyncModbusSerialClient(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=3,
            retries=2,
        )

    async def close(self):
        """Close Modbus client."""

        # Pokud někdo zrovna čte/zapisuje, počkáme krátce na lock.
        locked = False

        try:
            locked = await self._acquire_lock(WRITE_LOCK_TIMEOUT)

            if not locked:
                _LOGGER.warning(
                    "SANDISOLAR: Closing Modbus client without lock, Modbus busy"
                )

            await self._close_client_only()

        finally:
            if locked:
                self._lock.release()

    async def _close_client_only(self):
        """Close client without acquiring lock. Caller handles locking."""

        if self._client is None:
            return

        client = self._client
        self._client = None

        try:
            result = client.close()
            if asyncio.iscoroutine(result):
                await result

        except Exception as err:
            _LOGGER.debug("SANDISOLAR: Error while closing Modbus client: %s", err)

    async def _drop_connection(self, reason: str):
        """Drop current Modbus connection after communication error."""

        _LOGGER.debug("SANDISOLAR: Dropping Modbus connection: %s", reason)
        await self._close_client_only()

    async def _ensure_connection(self):
        """Ensure Modbus client is connected."""

        if self._client is None:
            self._client = self._create_client()

        if not getattr(self._client, "connected", False):
            connected = await self._client.connect()

            if not connected:
                await self._drop_connection("reconnect_failed")
                raise ModbusException(f"Failed to reconnect Modbus client on {self.port}")

        # Důležité: nepředávat slave= ani unit= do konkrétních Modbus volání.
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

    def _cached_or_none(self, key, reason: str):
        """Return cached value if available, otherwise None."""

        if key in self._cache:
            _LOGGER.debug(
                "SANDISOLAR: Returning cached value for %s, reason=%s",
                key,
                reason,
            )
            return self._cache[key]

        return None

    async def read_input_register(self, key):
        """Read input register by key.

        Input registers are live measurements.
        When Modbus is busy, cached value is acceptable to keep sensors stable.
        """

        if key not in INPUT_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown input register '%s'", key)
            return None

        locked = await self._acquire_lock(READ_LOCK_TIMEOUT)

        if not locked:
            cached = self._cached_or_none(key, "modbus_busy")
            if cached is not None:
                return cached

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
        """Read holding register by key.

        Holding registers are inverter settings.
        Always try to read real value from inverter because settings can be
        changed directly on inverter LCD.

        Important:
        Do not immediately return cached values here when Modbus is busy.
        Otherwise Home Assistant may keep showing old settings after a change
        made directly on the inverter LCD.
        """

        if key not in HOLDING_REGISTERS:
            _LOGGER.error("SANDISOLAR: Unknown holding register '%s'", key)
            return None

        # Holding registry jsou nastavení.
        # Počkáme déle, aby se změny z LCD měniče propsaly do HA.
        locked = await self._acquire_lock(WRITE_LOCK_TIMEOUT)

        if not locked:
            _LOGGER.debug(
                "SANDISOLAR: Holding read skipped for %s, Modbus busy",
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

        result = await self._execute_with_retry(
            action_name="Input read",
            key=key,
            operation=lambda: self._client.read_input_registers(
                address=reg.address,
                count=reg.count,
            ),
        )

        if result is None:
            return self._cached_or_none(key, "input_read_failed")

        if result.isError():
            _LOGGER.warning("SANDISOLAR: Input read Modbus error %s: %s", key, result)
            return self._cached_or_none(key, "input_read_modbus_error")

        raw = self._decode(result.registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    async def _read_holding_register_locked(self, key):
        """Read holding register. Caller must hold lock."""

        reg = HOLDING_REGISTERS[key]

        result = await self._execute_with_retry(
            action_name="Holding read",
            key=key,
            operation=lambda: self._client.read_holding_registers(
                address=reg.address,
                count=reg.count,
            ),
        )

        if result is None:
            return self._cached_or_none(key, "holding_read_failed")

        if result.isError():
            _LOGGER.warning("SANDISOLAR: Holding read Modbus error %s: %s", key, result)
            return self._cached_or_none(key, "holding_read_modbus_error")

        raw = self._decode(result.registers, reg.signed)
        value = raw * reg.scale

        self._cache[key] = value
        return value

    async def _write_holding_register_locked(self, key, value):
        """Write holding register. Caller must hold lock."""

        reg = HOLDING_REGISTERS[key]
        raw = int(round(value / reg.scale))

        result = await self._execute_with_retry(
            action_name="Write",
            key=f"{key}={value}",
            operation=lambda: self._client.write_register(
                address=reg.address,
                value=raw,
            ),
        )

        if result is None:
            _LOGGER.warning("SANDISOLAR: Write failed %s=%s", key, value)
            return False

        if result.isError():
            _LOGGER.warning("SANDISOLAR: Write Modbus error %s=%s: %s", key, value, result)
            return False

        # Po zápisu z HA víme, co jsme nastavili, takže cache může být aktualizovaná.
        self._cache[key] = value
        return True

    async def _execute_with_retry(self, action_name: str, key: str, operation):
        """Execute one Modbus operation with retry and hard timeout.

        Without a hard timeout one stuck serial/pymodbus request can hold the
        Modbus lock forever. Then input sensors only return cached values and
        everything looks frozen until Home Assistant is restarted.
        """

        for attempt in range(1, 3):
            try:
                await self._ensure_connection()
                await self._request_gap()

                # Důležité: unit_id nastavit na klientovi.
                # Nepředávat slave= ani unit= do Modbus metod.
                self._client.unit_id = self.slave

                result = await asyncio.wait_for(
                    operation(),
                    timeout=MODBUS_OPERATION_TIMEOUT,
                )

                if result is None:
                    _LOGGER.debug(
                        "SANDISOLAR: %s returned None for %s, attempt %s/2",
                        action_name,
                        key,
                        attempt,
                    )

                    if attempt == 1:
                        await asyncio.sleep(REQUEST_RETRY_DELAY)
                        continue

                self._consecutive_errors = 0
                self._last_success_time = time.monotonic()
                return result

            except asyncio.CancelledError:
                _LOGGER.debug("SANDISOLAR: %s cancelled %s", action_name, key)
                raise

            except asyncio.TimeoutError:
                self._consecutive_errors += 1

                _LOGGER.warning(
                    "SANDISOLAR: %s timeout for %s, attempt %s/2, errors=%s",
                    action_name,
                    key,
                    attempt,
                    self._consecutive_errors,
                )

                await self._drop_connection(f"{action_name} timeout for {key}")

                if attempt == 1:
                    await asyncio.sleep(REQUEST_RETRY_DELAY)
                    continue

                return None

            except Exception as err:
                err_text = str(err)

                transient = (
                    "Request cancelled outside pymodbus" in err_text
                    or "temporarily unavailable" in err_text.lower()
                    or "resource temporarily unavailable" in err_text.lower()
                    or "device reports readiness to read but returned no data" in err_text.lower()
                    or "no response received" in err_text.lower()
                    or "failed to reconnect" in err_text.lower()
                )

                self._consecutive_errors += 1

                if transient:
                    _LOGGER.debug(
                        "SANDISOLAR: %s transient error %s, attempt %s/2, errors=%s: %s",
                        action_name,
                        key,
                        attempt,
                        self._consecutive_errors,
                        err,
                    )
                else:
                    _LOGGER.warning(
                        "SANDISOLAR: %s error %s, attempt %s/2, errors=%s: %s",
                        action_name,
                        key,
                        attempt,
                        self._consecutive_errors,
                        err,
                    )

                await self._drop_connection(f"{action_name} failed for {key}: {err}")

                if attempt == 1:
                    await asyncio.sleep(REQUEST_RETRY_DELAY)
                    continue

                return None

        return None


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
