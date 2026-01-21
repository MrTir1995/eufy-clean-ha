"""Constants for the Eufy Clean integration."""

from typing import Final

DOMAIN: Final = "eufy_clean"

# Configuration
CONF_DEVICE_ID: Final = "device_id"
CONF_LOCAL_KEY: Final = "local_key"
CONF_DEVICE_IP: Final = "device_ip"
CONF_MODEL: Final = "model"

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_TIMEOUT: Final = 10

# Tuya Protocol
TUYA_PORT: Final = 6668
TUYA_VERSION: Final = "3.3"

# Eufy Cloud API - Eufy Clean App (for RoboVacs)
EUFY_API_BASE: Final = "https://portal-ww.eufylife.com/app"
EUFY_API_LOGIN: Final = f"{EUFY_API_BASE}/user/email/login"
EUFY_API_DEVICES: Final = f"{EUFY_API_BASE}/user/device/all"
EUFY_CLIENT_ID: Final = "EufyClean-app"
EUFY_CLIENT_SECRET: Final = "nKbJmGvjmTBJ9bQHpXfX"

# Data Point System (DPS) - Standard Mappings
DPS_POWER: Final = "1"
DPS_MODE: Final = "2"
DPS_RETURN_HOME: Final = "3"
DPS_FAN_SPEED_OLD: Final = "5"
DPS_STATUS: Final = "15"
DPS_FIND_ROBOT: Final = "101"
DPS_FAN_SPEED: Final = "102"
DPS_BATTERY: Final = "104"
DPS_ERROR_CODE: Final = "106"

# Vacuum States
STATE_CHARGING: Final = "charging"
STATE_CLEANING: Final = "cleaning"
STATE_DOCKED: Final = "docked"
STATE_ERROR: Final = "error"
STATE_IDLE: Final = "idle"
STATE_PAUSED: Final = "paused"
STATE_RETURNING: Final = "returning"

# Fan Speeds
FAN_SPEED_QUIET: Final = "Quiet"
FAN_SPEED_STANDARD: Final = "Standard"
FAN_SPEED_TURBO: Final = "Turbo"
FAN_SPEED_MAX: Final = "Max"

FAN_SPEEDS: Final = [
    FAN_SPEED_QUIET,
    FAN_SPEED_STANDARD,
    FAN_SPEED_TURBO,
    FAN_SPEED_MAX,
]

# Cleaning Modes
MODE_AUTO: Final = "auto"
MODE_SPOT: Final = "spot"
MODE_EDGE: Final = "edge"
MODE_SINGLE_ROOM: Final = "single_room"

# Error Codes
ERROR_CODES: Final = {
    "0": "No error",
    "1": "Wheel stuck",
    "2": "Side brush stuck",
    "3": "Main brush stuck",
    "4": "Trapped",
    "5": "Cliff sensor error",
    "6": "Low battery",
}
