# Eufy Clean - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/MrTir1995/eufy-clean-ha.svg)](https://github.com/MrTir1995/eufy-clean-ha/releases)

> [🇩🇪 Deutsche Version](README.de.md)

A Home Assistant custom integration for **local control** of Eufy Clean (RoboVac) vacuum cleaners. This integration allows you to control your Eufy robotic vacuum directly from Home Assistant without relying on cloud services.

## ✨ Features

- 🏠 **Local control** - Direct communication with your vacuum using the Tuya protocol (no cloud dependency)
- ⚡ **Real-time updates** - Push-based status updates for instant feedback
- 🎯 **Full vacuum control**:
  - Start/Stop/Pause cleaning
  - Return to dock
  - Fan speed control (Quiet, Standard, Turbo, Max)
  - Battery level monitoring
  - Cleaning status and error reporting
- 🔧 **Easy setup** - Simple configuration flow through the Home Assistant UI
- 🌐 **Multi-language support** - English and German translations included

## 🤖 Supported Devices

This integration supports Eufy Clean vacuum cleaners that use the Tuya protocol for local communication. The following device series are supported:

### Fully Tested Models
- **RoboVac 11C Series** (11C, 11S MAX)
- **RoboVac 15C Series** (15C, 15C MAX)
- **RoboVac 25C Series** (25C, 25C MAX)
- **RoboVac 30C Series** (30C, 30C MAX)
- **RoboVac 35C**

### Compatible Models (Community Tested)
- **G-Series**: G10, G20, G30, G30 Edge, G40, G50 (with gyro navigation)
- **L-Series**: L60, L70 (with LiDAR navigation)
- **X-Series**: X8, X10 (advanced models)

> **Note**: Newer models with LiDAR navigation may have limited map support due to encryption. Basic control (start, stop, dock, fan speed) works reliably.

## 📦 Installation

### Method 1: HACS (Recommended)

1. Open HACS in your Home Assistant
2. Click on "Integrations"
3. Click the three dots menu in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/MrTir1995/eufy-clean-ha`
6. Select category "Integration"
7. Click "Add"
8. Find "Eufy Clean" in the integration list and click "Download"
9. Restart Home Assistant

### Method 2: Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/MrTir1995/eufy-clean-ha/releases)
2. Extract the `eufy_clean` folder from the archive
3. Copy the `eufy_clean` folder to your `<config>/custom_components/` directory
4. Restart Home Assistant

## ⚙️ Configuration

### Step 1: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Eufy Clean"**
4. Click on it to start the setup

### Step 2: Enter Credentials

You'll need your Eufy account credentials (email and password). These are used **only once** during setup to:
- Discover your vacuum devices
- Retrieve the local encryption keys (`device_id` and `local_key`)
- Get the IP address of your vacuum

> **Privacy Note**: Your credentials are used only during initial setup. After setup, all communication with your vacuum is **local** and does not require cloud access.

### Step 3: Select Device

- The integration will automatically discover all Eufy Clean devices in your account
- Select the vacuum you want to add
- Click "Submit"

### Step 4: Configure IP Address (Optional)

If your vacuum's IP address changes, you can update it in the integration options:

1. Go to **Settings** → **Devices & Services**
2. Find the **Eufy Clean** integration
3. Click **"Configure"**
4. Enter the new IP address

## 🎮 Usage

Once configured, your Eufy vacuum will appear as a vacuum entity in Home Assistant.

### Basic Controls

```yaml
# Start cleaning
service: vacuum.start
target:
  entity_id: vacuum.eufy_robovac

# Return to dock
service: vacuum.return_to_base
target:
  entity_id: vacuum.eufy_robovac

# Stop cleaning
service: vacuum.stop
target:
  entity_id: vacuum.eufy_robovac

# Set fan speed
service: vacuum.set_fan_speed
target:
  entity_id: vacuum.eufy_robovac
data:
  # Options: Quiet, Standard, Turbo, Max
  fan_speed: "Turbo"
```

### Automation Example

```yaml
automation:
  - alias: "Start vacuum when leaving home"
    trigger:
      - platform: state
        entity_id: person.me
        to: "not_home"
    action:
      - service: vacuum.start
        target:
          entity_id: vacuum.eufy_robovac
  
  - alias: "Return vacuum to dock when arriving home"
    trigger:
      - platform: state
        entity_id: person.me
        to: "home"
    action:
      - service: vacuum.return_to_base
        target:
          entity_id: vacuum.eufy_robovac
```

### Lovelace Card Example

```yaml
type: entities
title: Eufy RoboVac
entities:
  - entity: vacuum.eufy_robovac
  - type: attribute
    entity: vacuum.eufy_robovac
    attribute: battery_level
    name: Battery
  - type: attribute
    entity: vacuum.eufy_robovac
    attribute: status
    name: Status
  - type: button
    name: Start Cleaning
    action_name: Start
    tap_action:
      action: call-service
      service: vacuum.start
      target:
        entity_id: vacuum.eufy_robovac
  - type: button
    name: Return to Dock
    action_name: Dock
    tap_action:
      action: call-service
      service: vacuum.return_to_base
      target:
        entity_id: vacuum.eufy_robovac
```

## 🔧 Troubleshooting

### Connection Issues

**Problem**: "Failed to connect to Eufy Cloud" during setup

**Solutions**:
- Verify your Eufy account credentials are correct
- Ensure you have an active internet connection during setup
- Check if your Eufy account has devices registered in the Eufy Home app

---

**Problem**: Vacuum shows as "Unavailable" after setup

**Solutions**:
1. **Check if vacuum is powered on** and connected to WiFi
2. **Verify IP address**: The vacuum's IP may have changed
   - Check your router's DHCP leases
   - Update the IP in integration options
3. **Single connection limit**: Eufy vacuums often allow only one TCP connection at a time
   - Force close the Eufy Home app on all devices
   - Restart the integration in Home Assistant
4. **Network isolation**: Ensure your vacuum and Home Assistant are on the same network or can communicate

### Making IP Address Static

To avoid IP address changes, configure a static IP or DHCP reservation for your vacuum:

1. **Router Method** (Recommended):
   - Log into your router's admin panel
   - Find the MAC address of your vacuum in the connected devices list
   - Create a DHCP reservation using the MAC address

2. **Alternative**: Some routers allow static IP assignment directly in the vacuum's network settings

### Multiple Devices

**Problem**: Can only connect to one vacuum at a time

**Solution**: This is a limitation of the Tuya protocol. Some Eufy models only allow one active connection. If you need to control multiple vacuums:
- Add each device separately through the integration
- Ensure the Eufy app is closed when Home Assistant is connected

### Error Codes

Common error codes and their meanings:

| Error Code | Meaning | Solution |
|------------|---------|----------|
| Wheel stuck | Wheel is blocked | Check and remove any obstructions from the wheels |
| Side brush stuck | Side brush is tangled | Clean the side brush |
| Main brush stuck | Main brush is tangled | Clean the main brush |
| Trapped | Vacuum is stuck | Move the vacuum to a clear area |
| Cliff sensor error | Cliff sensor malfunction | Clean the cliff sensors |
| Low battery | Battery is too low | Send vacuum to charging dock |

## 🔐 Security & Privacy

- **Local Control**: After initial setup, all communication is local (no cloud dependency)
- **Credentials**: Your Eufy credentials are only used during setup and are not stored
- **Keys**: Only the device ID and local encryption key are stored (required for local Tuya communication)
- **Network Isolation**: For maximum security, consider isolating IoT devices in a separate VLAN

## 🐛 Known Limitations

- **Map Display**: Live map data is not available due to proprietary encryption (cloud-based)
- **Advanced Features**: Some advanced features may not be available for newer models (room selection, virtual boundaries)
- **Single Connection**: Only one connection per device (close Eufy app when using Home Assistant)
- **LiDAR Models**: Newer LiDAR-equipped models may have limited feature support

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For development setup, see [DEVELOPMENT.md](DEVELOPMENT.md)

## 🙏 Acknowledgments

- [TinyTuya](https://github.com/jasonacox/tinytuya) - Local Tuya protocol implementation
- Home Assistant community for guidance and support
- Eufy users who contributed device testing and feedback

## 📚 Additional Documentation

- [DEVELOPMENT.md](DEVELOPMENT.md) - Development environment setup
- [Technical Reference: Eufy Protocol](Eufy%20Clean%20Steuerung_%20Lokal%20vs.%20Cloud.md) - Deep dive into Eufy/Tuya protocol (German)
- [Integration Development Guide](Home%20Assistant%20Custom%20Integration%20Entwicklung(1).md) - Home Assistant integration architecture (German)

## 📞 Support

- 🐛 [Report Issues](https://github.com/MrTir1995/eufy-clean-ha/issues)
- 💬 [Discussions](https://github.com/MrTir1995/eufy-clean-ha/discussions)
- ⭐ Star this repo if you find it useful!

---

**Made with ❤️ for the Home Assistant community**
