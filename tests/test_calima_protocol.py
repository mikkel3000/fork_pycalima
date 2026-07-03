import datetime as dt
import unittest

from pycalima.Calima import (
    CHARACTERISTIC_BOOST,
    CHARACTERISTIC_FACTORY_SETTINGS_CHANGED,
    CHARACTERISTIC_LEVEL_OF_FAN_SPEED,
    CHARACTERISTIC_MODE,
    CHARACTERISTIC_PIN_CODE,
    CHARACTERISTIC_PIN_CONFIRMATION,
    CHARACTERISTIC_SENSOR_DATA,
    CHARACTERISTIC_SENSITIVITY,
    Calima,
)


class FakeTransport:
    def __init__(self):
        self.values = {}
        self.writes = []

    async def read_uuid(self, uuid):
        return self.values[uuid]

    async def write_uuid(self, uuid, value):
        self.writes.append((uuid, value))


class CalimaProtocolTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.transport = FakeTransport()
        self.fan = Calima(self.transport.read_uuid, self.transport.write_uuid)

    async def test_set_auth_writes_pin_without_opening_transport(self):
        await self.fan.setAuth("123456")

        self.assertEqual(
            self.transport.writes,
            [(CHARACTERISTIC_PIN_CODE, b"\x40\xe2\x01\x00")],
        )

    async def test_check_auth_decodes_boolean_value(self):
        self.transport.values[CHARACTERISTIC_PIN_CONFIRMATION] = b"\x00"
        self.assertFalse(await self.fan.checkAuth())

        self.transport.values[CHARACTERISTIC_PIN_CONFIRMATION] = b"\x01"
        self.assertTrue(await self.fan.checkAuth())

    async def test_get_factory_settings_changed_returns_bool(self):
        self.transport.values[CHARACTERISTIC_FACTORY_SETTINGS_CHANGED] = b"\x01"

        self.assertIs(await self.fan.getFactorySettingsChanged(), True)

    async def test_get_mode_decodes_byte_value(self):
        self.transport.values[CHARACTERISTIC_MODE] = b"\x00"
        self.assertEqual(await self.fan.getMode(), "MultiMode")

        self.transport.values[CHARACTERISTIC_MODE] = b"\x04"
        self.assertEqual(await self.fan.getMode(), "HeatDistributionMode")

        self.transport.values[CHARACTERISTIC_MODE] = b"\x63"
        self.assertEqual(await self.fan.getMode(), "Unknown: 99")

    async def test_get_state_decodes_sensor_payload(self):
        self.transport.values[CHARACTERISTIC_SENSOR_DATA] = (
            b"\x2e\x01\x62\x00\x7b\x00\xd0\x07\x03\x00\x00\x00"
        )

        state = await self.fan.getState()

        self.assertEqual(state.Humidity, 80.87)
        self.assertEqual(state.Temp, 21.9)
        self.assertEqual(state.Light, 123)
        self.assertEqual(state.RPM, 2000)
        self.assertEqual(state.Mode, "Humidity ventilation")

    async def test_read_first_configuration_methods(self):
        self.transport.values[CHARACTERISTIC_BOOST] = b"\x01\xc4\x09\x58\x02"
        self.transport.values[CHARACTERISTIC_LEVEL_OF_FAN_SPEED] = (
            b"\xca\x08\x59\x06\xe8\x03"
        )
        self.transport.values[CHARACTERISTIC_SENSITIVITY] = b"\x01\x02\x00\x03"

        boost = await self.fan.getBoostMode()
        speeds = await self.fan.getFanSpeedSettings()
        sensitivity = await self.fan.getSensorsSensitivity()

        self.assertEqual(boost.Speed, 2500)
        self.assertEqual(boost.Seconds, 600)
        self.assertEqual(speeds.Humidity, 2250)
        self.assertEqual(speeds.Light, 1625)
        self.assertEqual(speeds.Trickle, 1000)
        self.assertEqual(sensitivity.Humidity, 2)
        self.assertEqual(sensitivity.Light, 0)

    async def test_set_silent_hours_accepts_time_values(self):
        await self.fan.setSilentHours(True, dt.time(22, 30), dt.time(6, 15))

        self.assertEqual(self.transport.writes[-1][1], b"\x01\x16\x1e\x06\x0f")


if __name__ == "__main__":
    unittest.main()
