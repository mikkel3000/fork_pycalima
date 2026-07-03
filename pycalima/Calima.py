import binascii
import datetime
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from struct import pack, unpack

ReadUuid = Callable[[str], Awaitable[bytes]]
WriteUuid = Callable[[str, bytes], Awaitable[None]]


@dataclass(frozen=True)
class Fanspeeds:
    Humidity: int = 2250
    Light: int = 1625
    Trickle: int = 1000


@dataclass(frozen=True)
class Time:
    DayOfWeek: int
    Hour: int
    Minute: int
    Second: int


@dataclass(frozen=True)
class Sensitivity:
    HumidityOn: int
    Humidity: int
    LightOn: int
    Light: int


@dataclass(frozen=True)
class LightSensorSettings:
    DelayedStart: int
    RunningTime: int


@dataclass(frozen=True)
class HeatDistributorSettings:
    TemperatureLimit: int
    FanSpeedBelow: int
    FanSpeedAbove: int


@dataclass(frozen=True)
class SilentHours:
    On: int
    StartingHour: int
    StartingMinute: int
    EndingHour: int
    EndingMinute: int


@dataclass(frozen=True)
class TrickleDays:
    Weekdays: int
    Weekends: int


@dataclass(frozen=True)
class BoostMode:
    OnOff: int
    Speed: int
    Seconds: int


@dataclass(frozen=True)
class FanState:
    Humidity: float
    Temp: float
    Light: int
    RPM: int
    Mode: str


CHARACTERISTIC_APPEARANCE = "00002a01-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_AUTOMATIC_CYCLES = "f508408a-508b-41c6-aa57-61d1fd0d5c39"
CHARACTERISTIC_BASIC_VENTILATION = "faa49e09-a79c-4725-b197-bdc57c67dc32"
CHARACTERISTIC_BOOST = "118c949c-28c8-4139-b0b3-36657fd055a9"
CHARACTERISTIC_CLOCK = "6dec478e-ae0b-4186-9d82-13dda03c0682"
CHARACTERISTIC_DEVICE_NAME = "00002a00-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_FACTORY_SETTINGS_CHANGED = "63b04af9-24c0-4e5d-a69c-94eb9c5707b4"
CHARACTERISTIC_FAN_DESCRIPTION = "b85fa07a-9382-4838-871c-81d045dcc2ff"
CHARACTERISTIC_FIRMWARE_REVISION = "00002a26-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_HARDWARE_REVISION = "00002a27-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_LED = "8b850c04-dc18-44d2-9501-7662d65ba36e"
CHARACTERISTIC_LEVEL_OF_FAN_SPEED = "1488a757-35bc-4ec8-9a6b-9ecf1502778e"
CHARACTERISTIC_MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_MODE = "90cabcd1-bcda-4167-85d8-16dcd8ab6a6b"
CHARACTERISTIC_MODEL_NUMBER = "00002a24-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_NIGHT_MODE = "b5836b55-57bd-433e-8480-46e4993c5ac0"
CHARACTERISTIC_PIN_CODE = "4cad343a-209a-40b7-b911-4d9b3df569b2"
CHARACTERISTIC_PIN_CONFIRMATION = "d1ae6b70-ee12-4f6d-b166-d2063dcaffe1"
CHARACTERISTIC_RESET = "ff5f7c4f-2606-4c69-b360-15aaea58ad5f"
CHARACTERISTIC_SENSITIVITY = "e782e131-6ce1-4191-a8db-f4304d7610f1"
CHARACTERISTIC_SENSOR_DATA = "528b80e8-c47a-4c0a-bdf1-916a7748f412"
CHARACTERISTIC_SERIAL_NUMBER = "00002a25-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_SOFTWARE_REVISION = "00002a28-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_STATUS = "25a824ad-3021-4de9-9f2f-60cf8d17bded"
CHARACTERISTIC_TEMP_HEAT_DISTRIBUTOR = "a22eae12-dba8-49f3-9c69-1721dcff1d96"
CHARACTERISTIC_TIME_FUNCTIONS = "49c616de-02b1-4b67-b237-90f66793a6f2"


class Calima:
    """Async, transport-agnostic protocol implementation for Pax Calima-like fans."""

    def __init__(self, read_uuid: ReadUuid, write_uuid: WriteUuid):
        self._read_uuid = read_uuid
        self._write_uuid = write_uuid

    @staticmethod
    def _b_to_str(value: bytes) -> str:
        return binascii.b2a_hex(value).decode("utf-8")

    async def getDeviceName(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_DEVICE_NAME)).decode("ascii")

    async def getModelNumber(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_MODEL_NUMBER)).decode("ascii")

    async def getSerialNumber(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_SERIAL_NUMBER)).decode("ascii")

    async def getHardwareRevision(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_HARDWARE_REVISION)).decode("ascii")

    async def getFirmwareRevision(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_FIRMWARE_REVISION)).decode("ascii")

    async def getSoftwareRevision(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_SOFTWARE_REVISION)).decode("ascii")

    async def getManufacturer(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_MANUFACTURER_NAME)).decode(
            "ascii"
        )

    async def setAuth(self, pin) -> None:
        await self._write_uuid(CHARACTERISTIC_PIN_CODE, pack("<I", int(pin)))

    async def getAuth(self) -> int:
        return unpack("<I", await self._read_uuid(CHARACTERISTIC_PIN_CODE))[0]

    async def checkAuth(self) -> bool:
        return bool(unpack("<b", await self._read_uuid(CHARACTERISTIC_PIN_CONFIRMATION))[0])

    async def setAlias(self, name) -> None:
        await self._write_uuid(
            CHARACTERISTIC_FAN_DESCRIPTION,
            pack("20s", bytearray(name, "utf-8")),
        )

    async def getAlias(self) -> str:
        return (await self._read_uuid(CHARACTERISTIC_FAN_DESCRIPTION)).decode("utf-8")

    async def getIsClockSet(self) -> str:
        return self._b_to_str(await self._read_uuid(CHARACTERISTIC_STATUS))

    async def getFactorySettingsChanged(self) -> bool:
        return unpack(
            "<?", await self._read_uuid(CHARACTERISTIC_FACTORY_SETTINGS_CHANGED)
        )[0]

    async def getLed(self) -> str:
        return self._b_to_str(await self._read_uuid(CHARACTERISTIC_LED))

    async def setTime(self, dayofweek, hour, minute, second) -> None:
        await self._write_uuid(
            CHARACTERISTIC_CLOCK, pack("<4B", dayofweek, hour, minute, second)
        )

    async def getTime(self) -> Time:
        return Time(*unpack("<BBBB", await self._read_uuid(CHARACTERISTIC_CLOCK)))

    async def setTimeToNow(self) -> None:
        now = datetime.datetime.now()
        await self.setTime(now.isoweekday(), now.hour, now.minute, now.second)

    async def getReset(self):
        return await self._read_uuid(CHARACTERISTIC_RESET)

    async def resetDevice(self):
        await self._write_uuid(CHARACTERISTIC_RESET, pack("<I", 120))

    async def resetValues(self):
        await self._write_uuid(CHARACTERISTIC_RESET, pack("<I", 85))

    async def getBoostMode(self) -> BoostMode:
        return BoostMode(*unpack("<BHH", await self._read_uuid(CHARACTERISTIC_BOOST)))

    async def setBoostMode(self, on, speed, seconds) -> None:
        if speed % 25:
            raise ValueError("Speed must be a multiple of 25")
        if not on:
            speed = 0
            seconds = 0

        await self._write_uuid(CHARACTERISTIC_BOOST, pack("<BHH", on, speed, seconds))

    async def getMode(self) -> str:
        value = unpack("<B", await self._read_uuid(CHARACTERISTIC_MODE))[0]
        modes = {
            0: "MultiMode",
            1: "DraftShutterMode",
            2: "WallSwitchExtendedRuntimeMode",
            3: "WallSwitchNoExtendedRuntimeMode",
            4: "HeatDistributionMode",
        }
        return modes.get(value, "Unknown: " + str(value))

    async def getState(self) -> FanState:
        value = unpack("<4HBHB", await self._read_uuid(CHARACTERISTIC_SENSOR_DATA))
        trigger = "No trigger"
        if ((value[4] >> 4) & 1) == 1:
            trigger = "Boost"
        elif ((value[4] >> 6) & 3) == 3:
            trigger = "Switch"
        elif (value[4] & 3) == 1:
            trigger = "Trickle ventilation"
        elif (value[4] & 3) == 2:
            trigger = "Light ventilation"
        elif (value[4] & 3) == 3:
            trigger = "Humidity ventilation"

        return FanState(
            round(math.log2(value[0] - 30) * 10, 2) if value[0] > 30 else 0,
            value[1] / 4 - 2.6,
            value[2],
            value[3],
            trigger,
        )

    async def getAutomaticCycles(self) -> int:
        return unpack("<B", await self._read_uuid(CHARACTERISTIC_AUTOMATIC_CYCLES))[0]

    async def setAutomaticCycles(self, setting: int) -> None:
        if setting < 0 or setting > 3:
            raise ValueError("Setting must be between 0-3")
        await self._write_uuid(CHARACTERISTIC_AUTOMATIC_CYCLES, pack("<B", setting))

    async def getFanSpeedSettings(self) -> Fanspeeds:
        return Fanspeeds(
            *unpack("<HHH", await self._read_uuid(CHARACTERISTIC_LEVEL_OF_FAN_SPEED))
        )

    async def setFanSpeedSettings(
        self, humidity=2250, light=1625, trickle=1000
    ) -> None:
        for value in (humidity, light, trickle):
            if value % 25 != 0:
                raise ValueError("Speeds should be multiples of 25")
            if value > 2500 or value < 0:
                raise ValueError("Speeds must be between 0 and 2500 rpm")

        await self._write_uuid(
            CHARACTERISTIC_LEVEL_OF_FAN_SPEED,
            pack("<HHH", humidity, light, trickle),
        )

    async def getHeatDistributor(self) -> HeatDistributorSettings:
        return HeatDistributorSettings(
            *unpack(
                "<BHH", await self._read_uuid(CHARACTERISTIC_TEMP_HEAT_DISTRIBUTOR)
            )
        )

    async def setHeatDistributor(
        self, temperatureLimit, fanSpeedBelow, fanSpeedAbove
    ) -> None:
        await self._write_uuid(
            CHARACTERISTIC_TEMP_HEAT_DISTRIBUTOR,
            pack("<BHH", temperatureLimit, fanSpeedBelow, fanSpeedAbove),
        )

    async def getSilentHours(self) -> SilentHours:
        return SilentHours(
            *unpack("<5B", await self._read_uuid(CHARACTERISTIC_NIGHT_MODE))
        )

    async def setSilentHours(
        self, on: bool, startingTime: datetime.time, endingTime: datetime.time
    ) -> None:
        await self._write_uuid(
            CHARACTERISTIC_NIGHT_MODE,
            pack(
                "<5B",
                int(on),
                startingTime.hour,
                startingTime.minute,
                endingTime.hour,
                endingTime.minute,
            ),
        )

    async def getTrickleDays(self) -> TrickleDays:
        return TrickleDays(
            *unpack("<2B", await self._read_uuid(CHARACTERISTIC_BASIC_VENTILATION))
        )

    async def setTrickleDays(self, weekdays, weekends) -> None:
        await self._write_uuid(
            CHARACTERISTIC_BASIC_VENTILATION, pack("<2B", weekdays, weekends)
        )

    async def getLightSensorSettings(self) -> LightSensorSettings:
        return LightSensorSettings(
            *unpack("<2B", await self._read_uuid(CHARACTERISTIC_TIME_FUNCTIONS))
        )

    async def setLightSensorSettings(self, delayed, running) -> None:
        if delayed not in (0, 5, 10):
            raise ValueError("Delayed must be 0, 5 or 10 minutes")
        if running not in (5, 10, 15, 30, 60):
            raise ValueError("Running time must be 5, 10, 15, 30 or 60 minutes")
        await self._write_uuid(CHARACTERISTIC_TIME_FUNCTIONS, pack("<2B", delayed, running))

    async def getSensorsSensitivity(self) -> Sensitivity:
        sensitivity = Sensitivity(
            *unpack("<4B", await self._read_uuid(CHARACTERISTIC_SENSITIVITY))
        )
        return Sensitivity(
            sensitivity.HumidityOn,
            sensitivity.Humidity if sensitivity.HumidityOn else 0,
            sensitivity.LightOn,
            sensitivity.Light if sensitivity.LightOn else 0,
        )

    async def setSensorsSensitivity(self, humidity, light) -> None:
        if humidity > 3 or humidity < 0:
            raise ValueError("Humidity sensitivity must be between 0-3")
        if light > 3 or light < 0:
            raise ValueError("Light sensitivity must be between 0-3")
        await self._write_uuid(
            CHARACTERISTIC_SENSITIVITY,
            pack("<4B", bool(humidity), humidity, bool(light), light),
        )
