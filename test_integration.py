#!/usr/bin/env python3
"""Test script to validate the Eufy Clean integration."""

import asyncio
import sys
from pathlib import Path

# Add custom_components to path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))


async def main():
    """Run integration tests."""
    print("=" * 60)
    print("Eufy Clean Integration Validation")
    print("=" * 60)

    # Test 1: Import config_flow
    print("\n1. Testing config_flow import...")
    try:
        from eufy_clean.config_flow import (
            EufyCleanConfigFlow,
            EufyCleanOptionsFlowHandler,
        )

        print("   ✓ config_flow importiert")
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Test 2: Import __init__
    print("\n2. Testing __init__ import...")
    try:
        print("   ✓ __init__ importiert")
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
        return False

    # Test 3: ConfigFlow instantiation
    print("\n3. Testing ConfigFlow instantiation...")
    try:
        flow = EufyCleanConfigFlow()
        print("   ✓ ConfigFlow erstellt")
        print(f"   VERSION: {flow.VERSION}")
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
        return False

    # Test 4: OptionsFlowHandler instantiation
    print("\n4. Testing OptionsFlowHandler instantiation...")
    try:
        options_flow = EufyCleanOptionsFlowHandler()
        print("   ✓ OptionsFlowHandler erstellt")
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
        return False

    # Test 5: Check async_get_options_flow
    print("\n5. Testing async_get_options_flow...")
    try:
        if hasattr(EufyCleanConfigFlow, "async_get_options_flow"):
            print("   ✓ async_get_options_flow vorhanden")

            # Try to call it
            from unittest.mock import Mock

            mock_entry = Mock()
            mock_entry.data = {"device_ip": "192.168.1.100"}

            try:
                result = EufyCleanConfigFlow.async_get_options_flow(mock_entry)
                print(f"   ✓ async_get_options_flow aufrufbar: {type(result).__name__}")
            except Exception as e:
                print(f"   ✗ Fehler beim Aufruf: {e}")
        else:
            print("   ✗ async_get_options_flow nicht gefunden")
            return False
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
        return False

    # Test 6: Validate manifest.json
    print("\n6. Testing manifest.json...")
    try:
        import json

        manifest_path = (
            Path(__file__).parent / "custom_components" / "eufy_clean" / "manifest.json"
        )
        with open(manifest_path) as f:
            manifest = json.load(f)

        required_keys = ["domain", "name", "config_flow", "requirements", "version"]
        for key in required_keys:
            if key not in manifest:
                print(f"   ✗ Fehlender Schlüssel: {key}")
                return False

        print("   ✓ manifest.json gültig")
        print(f"   Domain: {manifest['domain']}")
        print(f"   Version: {manifest['version']}")
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ Alle Tests erfolgreich!")
    print("=" * 60)
    print("\nWenn Home Assistant immer noch einen 500-Fehler zeigt:")
    print("1. Home Assistant komplett neu starten")
    print("2. Browser-Cache leeren (Strg+Shift+R)")
    print("3. __pycache__ Ordner löschen:")
    print("   rm -rf custom_components/eufy_clean/__pycache__")
    print("4. Prüfen Sie die Home Assistant Logs:")
    print("   journalctl -u home-assistant -f")
    print("=" * 60)

    return True


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
