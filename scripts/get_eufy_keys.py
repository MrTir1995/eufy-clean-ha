#!/usr/bin/env python3
"""
Script to extract Eufy Clean device credentials (device_id and local_key).
Based on the methodology described in the technical documentation.
"""

import json
import sys
from getpass import getpass

import requests


def get_eufy_credentials(email: str, password: str) -> list[dict]:
    """
    Extract device credentials from Eufy Cloud API.
    
    Args:
        email: Eufy account email
        password: Eufy account password
        
    Returns:
        List of devices with their credentials
    """
    print("🔐 Authenticating with Eufy Cloud...")
    
    # Step 1: Login
    login_url = "https://home-api.eufylife.com/v1/user/email/login"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "EufyHome-Android-2.4.0"
    }
    
    login_data = {
        "client_id": "eufyhome-app",
        "client_secret": "GQCpr9dSp3uQpsOMgJ4xQ",
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=login_data, headers=headers, timeout=10)
        response.raise_for_status()
        token = response.json().get("access_token")
        
        if not token:
            print("❌ Failed to get access token")
            return []
            
        print("✅ Authentication successful")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Login failed: {e}")
        return []
    
    # Step 2: Get device list
    print("📱 Fetching device list...")
    
    device_url = "https://home-api.eufylife.com/v1/device/list/devices-and-groups"
    device_headers = {
        "token": token,
        "category": "Home",
        "User-Agent": "EufyHome-Android-2.4.0"
    }
    
    try:
        response = requests.get(device_url, headers=device_headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        devices = []
        for item in data.get("items", []):
            if item.get("device"):
                device = item["device"]
                device_info = {
                    "name": device.get("alias", device.get("name", "Unknown")),
                    "device_id": device.get("id"),
                    "local_key": device.get("local_code") or device.get("localKey"),
                    "model": device.get("product", {}).get("product_code"),
                    "ip": device.get("wifi", {}).get("lan_ip")
                }
                
                if device_info["device_id"] and device_info["local_key"]:
                    devices.append(device_info)
        
        return devices
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to fetch devices: {e}")
        return []


def main():
    """Main execution function."""
    print("=" * 60)
    print("Eufy Clean Local Key Extractor")
    print("=" * 60)
    print()
    
    email = input("Enter your Eufy account email: ").strip()
    password = getpass("Enter your Eufy account password: ")
    
    print()
    devices = get_eufy_credentials(email, password)
    
    if not devices:
        print("\n❌ No devices found or extraction failed")
        sys.exit(1)
    
    print(f"\n✅ Found {len(devices)} device(s):\n")
    print("=" * 60)
    
    for i, device in enumerate(devices, 1):
        print(f"\nDevice {i}: {device['name']}")
        print(f"  Model:      {device['model']}")
        print(f"  Device ID:  {device['device_id']}")
        print(f"  Local Key:  {device['local_key']}")
        print(f"  IP Address: {device['ip'] or 'Not available'}")
    
    print("\n" + "=" * 60)
    
    # Save to file
    output_file = "eufy_credentials.json"
    with open(output_file, "w") as f:
        json.dump(devices, f, indent=2)
    
    print(f"\n💾 Credentials saved to: {output_file}")
    print("\n⚠️  Keep these credentials secure!")
    print("You can now use them in your Home Assistant integration.")


if __name__ == "__main__":
    main()
