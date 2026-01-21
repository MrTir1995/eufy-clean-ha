#!/usr/bin/env python3
"""Script to check Eufy account details and available API endpoints."""

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components"))

from eufy_clean.const import EUFY_API_BASE


async def main():
    """Check Eufy account details."""
    print("=" * 70)
    print("Eufy Account Information Check")
    print("=" * 70)

    email = input("Enter your Eufy account email: ").strip()
    password = input("Enter your Eufy account password: ").strip()

    print("\n" + "=" * 70)

    async with aiohttp.ClientSession() as session:
        # Step 1: Login
        print("\n1. Login to Eufy Cloud...")
        headers = {"Content-Type": "application/json"}
        data = {
            "client_id": "eufyhome-app",
            "client_secret": "GQCpr9dSp3uQpsOMgJ4xQ",
            "email": email,
            "password": password,
        }

        try:
            url = f"{EUFY_API_BASE}user/email/login"
            print(f"   URL: {url}")
            async with session.post(
                url, json=data, headers=headers, timeout=10
            ) as response:
                result = await response.json()

                if result.get("error"):
                    print(
                        f"   ✗ Login failed: {result.get('message', {}).get('message')}"
                    )
                    return

                print("   ✓ Login successful!")
                print("\n" + "=" * 70)
                print("Login Response (formatted):")
                print("=" * 70)
                print(json.dumps(result, indent=2))

                # Extract useful info
                user_info = result.get("user_info", {})
                token = result.get("access_token")
                user_id = user_info.get("id")
                request_host = user_info.get("request_host")

                print("\n" + "=" * 70)
                print("Extracted Information:")
                print("=" * 70)
                print(f"User ID: {user_id}")
                print(f"Token: {token[:20] if token else 'N/A'}...")
                print(f"Request Host: {request_host}")
                print(f"Phone Code: {user_info.get('phone_code')}")
                print(f"Country: {user_info.get('country')}")

        except Exception as e:
            print(f"   ✗ Login error: {e}")
            import traceback

            traceback.print_exc()
            return

        # Step 2: Try different device endpoints
        print("\n" + "=" * 70)
        print("2. Trying different device endpoints...")
        print("=" * 70)

        endpoints = [
            "device/v2",
            "device/list",
            "device/v2/list",
            "device/list/devices-and-groups",
        ]

        for endpoint in endpoints:
            print(f"\n   Testing: {endpoint}")
            try:
                # Normalize base URL
                base = request_host if request_host else EUFY_API_BASE
                if not base.endswith("/"):
                    base = base + "/"
                if not base.endswith("/v1/"):
                    base = base + "v1/"

                from urllib.parse import urljoin

                url = urljoin(base, endpoint)
                print(f"   Full URL: {url}")

                headers = {
                    "token": token,
                    "uid": str(user_id),
                    "category": "Home",
                    "User-Agent": "EufyHome-Android-2.4.0",
                }

                async with session.get(url, headers=headers, timeout=10) as response:
                    status = response.status
                    print(f"   Status: {status}")

                    if status == 200:
                        result = await response.json()
                        print(f"   Response keys: {list(result.keys())}")

                        # Check for devices
                        data = result.get("data", [])
                        if isinstance(data, dict):
                            devices = data.get("items", []) or data.get("devices", [])
                        elif isinstance(data, list):
                            devices = data
                        else:
                            devices = []

                        print(f"   Devices found: {len(devices)}")
                        if devices:
                            print("\n   ✅ SUCCESS! Devices found at this endpoint:")
                            print(json.dumps(result, indent=2))
                    else:
                        print(f"   ✗ Failed with status {status}")

            except Exception as e:
                print(f"   ✗ Error: {e}")

        print("\n" + "=" * 70)
        print("3. Checking if Tuya API is needed...")
        print("=" * 70)
        print("\n💡 Wichtiger Hinweis:")
        print("Eufy verwendet intern die Tuya IoT Plattform für RoboVac Geräte.")
        print("Die Geräte werden möglicherweise NICHT über die Eufy API exponiert,")
        print("sondern nur über die Tuya API mit dem Username 'eh-{user_id}'.")
        print(f"\nIhr Tuya Username wäre: eh-{user_id}")
        print(
            "\nDie Integration müsste erweitert werden, um die Tuya API zu verwenden."
        )


if __name__ == "__main__":
    asyncio.run(main())
