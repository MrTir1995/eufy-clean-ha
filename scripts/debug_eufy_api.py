#!/usr/bin/env python3
"""Debug script to test Eufy Cloud API authentication."""

import asyncio
import sys
from pathlib import Path

import aiohttp

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from eufy_clean.eufy_api import EufyCloudAPI


async def main():
    """Test Eufy Cloud API."""
    print("=" * 70)
    print("Eufy Cloud API Debug Script")
    print("=" * 70)

    email = input("Enter your Eufy account email: ").strip()
    password = input("Enter your Eufy account password: ").strip()

    print("\n" + "=" * 70)
    print("Testing Eufy Cloud API...")
    print("=" * 70)

    async with aiohttp.ClientSession() as session:
        api = EufyCloudAPI(session)

        # Test 1: Login
        print("\n1. Testing login...")
        try:
            token = await api.async_login(email, password)
            print(f"   ✓ Login successful!")
            print(f"   Token (first 20 chars): {token[:20]}...")
        except Exception as e:
            print(f"   ✗ Login failed: {e}")
            import traceback

            traceback.print_exc()
            return False

        # Test 2: Get devices
        print("\n2. Getting devices...")
        try:
            devices = await api.async_get_devices()
            print(f"   ✓ Retrieved {len(devices)} devices")

            if not devices:
                print("\n   ⚠ No devices found in your account!")
                print("   This could mean:")
                print("   - Your robots are not linked to this Eufy account")
                print("   - The Eufy Cloud API has changed")
                print("   - The robots are not online/registered properly")
                return False

            print("\n" + "=" * 70)
            print("Device List:")
            print("=" * 70)

            for i, device in enumerate(devices, 1):
                print(f"\nDevice #{i}:")
                print(f"  Name:      {device.get('name')}")
                print(f"  Model:     {device.get('model')}")
                print(f"  Device ID: {device.get('device_id')}")
                print(f"  Local Key: {device.get('local_key', 'N/A')}")
                print(f"  IP:        {device.get('ip', 'N/A')}")

            # Test 3: Check vacuum filter
            print("\n" + "=" * 70)
            print("Checking vacuum device filter...")
            print("=" * 70)

            vacuum_devices = [
                d
                for d in devices
                if d.get("model")
                and any(
                    x in d["model"].lower()
                    for x in ["robovac", "t", "l", "x", "g", "e"]
                )
            ]

            print(f"\nFound {len(vacuum_devices)} vacuum devices after filtering")

            if not vacuum_devices:
                print("\n⚠ WARNING: No vacuum devices passed the filter!")
                print("\nYour device models:")
                for device in devices:
                    print(f"  - {device.get('model')}")
                print("\nThe filter looks for models containing: robovac, t, l, x, g, e")
                print("\nYour RoboVac G10 Hybrid and L60 SES should match!")
                print("The API might be returning different model names.")
                return False

            print("\n✓ Vacuum devices found:")
            for device in vacuum_devices:
                print(f"  - {device.get('name')} ({device.get('model')})")

            print("\n" + "=" * 70)
            print("✓ All tests passed!")
            print("=" * 70)
            print("\nIf you're still seeing errors in Home Assistant:")
            print("1. Enable debug logging in configuration.yaml:")
            print("   logger:")
            print("     default: info")
            print("     logs:")
            print("       custom_components.eufy_clean: debug")
            print("2. Restart Home Assistant")
            print("3. Try adding the integration again")
            print("4. Check the logs for detailed error messages")
            print("=" * 70)

            return True

        except Exception as e:
            print(f"   ✗ Failed to get devices: {e}")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
