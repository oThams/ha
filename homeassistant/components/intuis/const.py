"""Constants used by the Intuis component."""

from homeassistant.const import Platform

DOMAIN = "intuis"
MANUFACTURER = "Intuis"
DEFAULT_ATTRIBUTION = "Data provided by Netatmo"

PLATFORMS = [Platform.CLIMATE]

# OAuth2 configuration
OAUTH2_AUTHORIZE = "https://api.netatmo.com/oauth2/authorize"
OAUTH2_TOKEN = "https://api.netatmo.com/oauth2/token"

# API configuration
API = "api"
AUTH = "intuis_auth"
DATA_HANDLER = "intuis_data_handler"
SIGNAL_NAME = "signal_name"

# Data storage keys
DATA_HOMES = "intuis_homes"
DATA_SCHEDULES = "intuis_schedules"

# URLs
CONF_URL_ENERGY = "https://my.netatmo.com/app/energy"

# Entity creation signals
INTUIS_CREATE_CLIMATE = "intuis_create_climate"

# Attributes
ATTR_SCHEDULE_NAME = "schedule_name"
ATTR_SELECTED_SCHEDULE = "selected_schedule"
ATTR_END_DATETIME = "end_datetime"
ATTR_HEATING_POWER_REQUEST = "heating_power_request"

# Services
SERVICE_SET_SCHEDULE = "set_schedule"
SERVICE_SET_PRESET_MODE_WITH_END_DATETIME = "set_preset_mode_with_end_datetime"

# Events
EVENT_TYPE_SET_POINT = "set_point"
EVENT_TYPE_THERM_MODE = "therm_mode"
EVENT_TYPE_CANCEL_SET_POINT = "cancel_set_point"
EVENT_TYPE_SCHEDULE = "schedule"

# Device types
DEVICE_TYPE_NLC = "NLC"  # Intuis Connect module
