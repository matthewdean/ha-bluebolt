#!/usr/bin/env python3
"""Development script to test BlueBOLT CV2 communication.

Usage:
    BLUEBOLT_HOST=192.168.0.162 BLUEBOLT_MAC=1065a3XXXXXX python scripts/test_device.py

Or pass as arguments:
    python scripts/test_device.py 192.168.0.162 1065a3XXXXXX
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.bluebolt.cv2 import BlueBoltCV2


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

    cv2 = BlueBoltCV2(host=host, mac=mac)

    print("=" * 60)
    print("Testing BlueBOLT CV2 Interface")
    print(f"Host: {host}")
    print("=" * 60)

    print("\n1. Testing CV2 connectivity and device discovery...")
    connected = await cv2.connect()
    print(f"   Connected: {connected}")
    if connected:
        print(f"   Device Class: {cv2.device_class}")
        print(f"   Device ID: {cv2.device_id}")

    if not connected:
        print("\n   Failed to connect to CV2")
        return

    print("\n2. Getting device info via CV2...")
    info = await cv2.get_device_info()
    print(f"   Firmware: {info.get('firmware', 'Unknown')}")

    print("\n3. Getting device status via CV2...")
    status = await cv2.get_status()
    print(f"   Voltage: {status.get('voltage', 0)} V")
    print(f"   Current: {status.get('current', 0)} A")
    print(f"   Power: {status.get('power', 0)} W")
    print(f"   Temperature: {status.get('temperature', 0)} °C")

    print("\n4. Outlet Status:")
    outlets = status.get("outlets", {})
    for outlet_id in range(1, 9):
        state = "ON" if outlets.get(outlet_id, False) else "OFF"
        print(f"   Outlet {outlet_id}: {state}")

    print("\n5. Testing outlet control via CV2 (Outlet 2)...")
    print("   Turning ON outlet 2...")
    success = await cv2.set_outlet(2, True)
    print(f"   Result: {'Success' if success else 'Failed'}")

    await asyncio.sleep(2)
    status = await cv2.get_status()
    outlets = status.get("outlets", {})
    print(f"   Outlet 2 is now: {'ON' if outlets.get(2, False) else 'OFF'}")

    print("\n   Turning OFF outlet 2...")
    success = await cv2.set_outlet(2, False)
    print(f"   Result: {'Success' if success else 'Failed'}")

    await asyncio.sleep(2)
    status = await cv2.get_status()
    outlets = status.get("outlets", {})
    print(f"   Outlet 2 is now: {'ON' if outlets.get(2, False) else 'OFF'}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
