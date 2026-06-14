#!/usr/bin/env python3
"""Development script to test BlueBOLT CV2 communication.

Usage:
    BLUEBOLT_HOST=192.168.0.162 BLUEBOLT_MAC=1065a3XXXXXX python scripts/test_device.py

Or pass as arguments:
    python scripts/test_device.py 192.168.0.162 1065a3XXXXXX
"""
import asyncio
import importlib.util
import os
import sys
import types
from pathlib import Path

# Load device.py directly, bypassing custom_components/bluebolt/__init__.py (which
# imports Home Assistant). device.py and const.py have no Home Assistant deps, so
# this script runs on a plain Python install without Home Assistant present.
_PKG = "bluebolt_standalone"
_PKG_DIR = Path(__file__).parent.parent / "custom_components" / "bluebolt"


def _load_device_class():
    package = types.ModuleType(_PKG)
    package.__path__ = [str(_PKG_DIR)]
    sys.modules[_PKG] = package
    for name in ("const", "device"):  # const first; device imports `from .const`
        spec = importlib.util.spec_from_file_location(
            f"{_PKG}.{name}", _PKG_DIR / f"{name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"{_PKG}.{name}"] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{_PKG}.device"].BlueBoltDevice


BlueBoltDevice = _load_device_class()


async def main():
    """Test BlueBOLT CV2 communication."""
    if len(sys.argv) >= 3:
        host = sys.argv[1]
        mac = sys.argv[2]
    else:
        host = os.getenv("BLUEBOLT_HOST")
        mac = os.getenv("BLUEBOLT_MAC")

    if not host or not mac:
        print("Error: HOST and MAC address required")
        print("\nUsage:")
        print("  BLUEBOLT_HOST=192.168.0.162 BLUEBOLT_MAC=1065a3XXXXXX python scripts/test_device.py")
        print("  OR")
        print("  python scripts/test_device.py 192.168.0.162 1065a3XXXXXX")
        sys.exit(1)

    device = BlueBoltDevice(host=host, mac=mac)

    print("=" * 60)
    print("Testing BlueBOLT CV2 Interface")
    print(f"Host: {host}")
    print("=" * 60)

    print("\n1. Testing CV2 connectivity and device discovery...")
    connected = await device.connect()
    print(f"   Connected: {connected}")
    if connected:
        print(f"   Device Class: {device.device_class}")
        print(f"   Device Type:  {device.device_type}")
        print(f"   Device ID:    {device.device_id}")

    if not connected:
        print("\n   Failed to connect to CV2")
        return

    print("\n2. Getting device info via CV2...")
    info = await device.get_device_info()
    print(f"   Firmware:        {info.get('firmware', 'Unknown')}")
    print(f"   Serial number:   {info.get('serial_number')}")
    print(f"   Hardware version: {info.get('hardware_version')}")

    print("\n3. Getting device status via CV2...")
    status = await device.get_status()
    print(f"   Voltage:        {status.get('voltage', 0)} V")
    print(f"   Current:        {status.get('current', 0)} A")
    print(f"   Power:          {status.get('power', 0)} W")
    print(f"   Apparent power: {status.get('apparent_power')} VA")
    print(f"   Power factor:   {status.get('power_factor')}")
    print(f"   Temperature:    {status.get('temperature', 0)} °C")

    print("\n   Power-quality flags (only those the device reports):")
    for key in ("surge_protection_ok", "power_ok", "overvoltage", "undervoltage"):
        if key in status:
            print(f"     {key}: {status[key]}")

    if "battery_level" in status or "voltage_out" in status:
        print("\n   UPS:")
        print(f"     Output voltage: {status.get('voltage_out')} V")
        print(f"     Battery level:  {status.get('battery_level')}")
        print(f"     Load level:     {status.get('load_level')} %")

    print("\n4. Outlet Status:")
    outlets = status.get("outlets", {})
    for outlet_id in sorted(outlets):
        state = "ON" if outlets[outlet_id] else "OFF"
        print(f"   Outlet {outlet_id}: {state}")

    print("\n5. Testing outlet control via CV2 (Outlet 2)...")
    print("   Turning ON outlet 2...")
    success = await device.set_outlet(2, True)
    print(f"   Result: {'Success' if success else 'Failed'}")

    await asyncio.sleep(2)
    status = await device.get_status()
    outlets = status.get("outlets", {})
    print(f"   Outlet 2 is now: {'ON' if outlets.get(2, False) else 'OFF'}")

    print("\n   Turning OFF outlet 2...")
    success = await device.set_outlet(2, False)
    print(f"   Result: {'Success' if success else 'Failed'}")

    await asyncio.sleep(2)
    status = await device.get_status()
    outlets = status.get("outlets", {})
    print(f"   Outlet 2 is now: {'ON' if outlets.get(2, False) else 'OFF'}")

    print("\n6. Testing outlet power-cycle via CV2 (Outlet 2, 5s)...")
    success = await device.cycle_outlet(2, delay=5)
    print(f"   Result: {'Success' if success else 'Failed'}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
