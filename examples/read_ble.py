import argparse
import asyncio
from collections.abc import Awaitable, Callable

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from pycalima import Calima


async def _find_device(args) -> BLEDevice | str:
    if args.address and not args.scan:
        return args.address

    devices = await BleakScanner.discover(timeout=args.scan_timeout)
    matches = []
    for device in devices:
        name = device.name or ""
        if args.list:
            print(f"{device.address}\t{name}")
        if args.address and device.address.lower() == args.address.lower():
            matches.append(device)
        elif args.name and args.name.lower() in name.lower():
            matches.append(device)
        elif not args.address and not args.name and name.lower().startswith("pax"):
            matches.append(device)

    if args.list:
        raise SystemExit(0)
    if not matches:
        raise SystemExit("No matching fan found. Try --list, --address, or --name.")
    if len(matches) > 1:
        print("Multiple matching devices found; using the first one:")
        for device in matches:
            print(f"{device.address}\t{device.name or ''}")
    return matches[0]


async def _read(label: str, getter: Callable[[], Awaitable[object]]) -> None:
    try:
        print(f"{label}: {await getter()}")
    except Exception as exc:
        print(f"{label}: ERROR {type(exc).__name__}: {exc}")


async def _read_optional(label: str, getter: Callable[[], Awaitable[object]]) -> None:
    try:
        print(f"{label}: {await getter()}")
    except Exception as exc:
        print(f"{label}: unavailable ({type(exc).__name__}: {exc})")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read a Pax Calima-like fan with pycalima over bleak."
    )
    parser.add_argument("--address", help="BLE address/identifier to connect to.")
    parser.add_argument("--name", help="Substring of the BLE device name to connect to.")
    parser.add_argument("--list", action="store_true", help="List nearby BLE devices.")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan first, even when --address is provided.",
    )
    parser.add_argument("--scan-timeout", type=float, default=8.0)
    parser.add_argument("--connect-timeout", type=float, default=20.0)
    parser.add_argument("--pin", help="Optional PIN. Writes auth before reading auth state.")
    parser.add_argument(
        "--config",
        action="store_true",
        help="Also read slower configuration characteristics.",
    )
    args = parser.parse_args()

    device = await _find_device(args)
    print(f"Connecting to {getattr(device, 'address', device)}")

    async with BleakClient(device, timeout=args.connect_timeout) as client:
        async def read_uuid(uuid: str) -> bytes:
            return bytes(await client.read_gatt_char(uuid))

        async def write_uuid(uuid: str, value: bytes) -> None:
            await client.write_gatt_char(uuid, value, response=True)

        fan = Calima(read_uuid, write_uuid)

        if args.pin is not None:
            await fan.setAuth(args.pin)
            await _read("auth", fan.checkAuth)

        await _read_optional("device_name", fan.getDeviceName)
        await _read("alias", fan.getAlias)
        await _read("state", fan.getState)
        await _read("boost", fan.getBoostMode)

        if args.config:
            await _read("mode", fan.getMode)
            await _read("fan_speed_settings", fan.getFanSpeedSettings)
            await _read("light_sensor_settings", fan.getLightSensorSettings)
            await _read("sensor_sensitivity", fan.getSensorsSensitivity)
            await _read("silent_hours", fan.getSilentHours)
            await _read("trickle_days", fan.getTrickleDays)
            await _read("automatic_cycles", fan.getAutomaticCycles)
            await _read("heat_distributor", fan.getHeatDistributor)


if __name__ == "__main__":
    asyncio.run(main())
