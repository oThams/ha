"""Support for Intuis Connect with Netatmo electric radiators."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.climate import (
    ATTR_PRESET_MODE,
    DEFAULT_MIN_TEMP,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_HOME,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_SUGGESTED_AREA,
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    STATE_OFF,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_END_DATETIME,
    ATTR_HEATING_POWER_REQUEST,
    ATTR_SCHEDULE_NAME,
    ATTR_SELECTED_SCHEDULE,
    CONF_URL_ENERGY,
    DATA_SCHEDULES,
    DEVICE_TYPE_NLC,
    DOMAIN,
    EVENT_TYPE_CANCEL_SET_POINT,
    EVENT_TYPE_SCHEDULE,
    EVENT_TYPE_SET_POINT,
    EVENT_TYPE_THERM_MODE,
    INTUIS_CREATE_CLIMATE,
    MANUFACTURER,
    SERVICE_SET_PRESET_MODE_WITH_END_DATETIME,
    SERVICE_SET_SCHEDULE,
)
from .data_handler import IntuisRoom

_LOGGER = logging.getLogger(__name__)

PRESET_FROST_GUARD = "Frost Guard"
PRESET_SCHEDULE = "Schedule"
PRESET_MANUAL = "Manual"

SUPPORT_FLAGS = (
    ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
)
SUPPORT_PRESET = [PRESET_AWAY, PRESET_BOOST, PRESET_FROST_GUARD, PRESET_SCHEDULE]

THERM_MODES = (PRESET_SCHEDULE, PRESET_FROST_GUARD, PRESET_AWAY)

STATE_NETATMO_SCHEDULE = "schedule"
STATE_NETATMO_HG = "hg"
STATE_NETATMO_MAX = "max"
STATE_NETATMO_AWAY = PRESET_AWAY
STATE_NETATMO_OFF = STATE_OFF
STATE_NETATMO_MANUAL = "manual"
STATE_NETATMO_HOME = "home"

PRESET_MAP_NETATMO = {
    PRESET_FROST_GUARD: STATE_NETATMO_HG,
    PRESET_BOOST: STATE_NETATMO_MAX,
    PRESET_SCHEDULE: STATE_NETATMO_SCHEDULE,
    PRESET_AWAY: STATE_NETATMO_AWAY,
    STATE_NETATMO_OFF: STATE_NETATMO_OFF,
}

NETATMO_MAP_PRESET = {
    STATE_NETATMO_HG: PRESET_FROST_GUARD,
    STATE_NETATMO_MAX: PRESET_BOOST,
    STATE_NETATMO_SCHEDULE: PRESET_SCHEDULE,
    STATE_NETATMO_AWAY: PRESET_AWAY,
    STATE_NETATMO_OFF: STATE_NETATMO_OFF,
    STATE_NETATMO_MANUAL: STATE_NETATMO_MANUAL,
    STATE_NETATMO_HOME: PRESET_SCHEDULE,
}

HVAC_MAP_NETATMO = {
    PRESET_SCHEDULE: HVACMode.AUTO,
    STATE_NETATMO_HG: HVACMode.AUTO,
    PRESET_FROST_GUARD: HVACMode.AUTO,
    PRESET_BOOST: HVACMode.HEAT,
    STATE_NETATMO_OFF: HVACMode.OFF,
    STATE_NETATMO_MANUAL: HVACMode.AUTO,
    PRESET_MANUAL: HVACMode.AUTO,
    STATE_NETATMO_AWAY: HVACMode.AUTO,
}

CURRENT_HVAC_MAP_NETATMO = {True: HVACAction.HEATING, False: HVACAction.IDLE}

DEFAULT_MAX_TEMP = 30


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Intuis climate platform."""

    @callback
    def _create_entity(intuis_device: IntuisRoom) -> None:
        if not intuis_device.room.climate_type:
            msg = f"No climate type found for this room: {intuis_device.room.name}"
            _LOGGER.debug(msg)
            return
        entity = IntuisRadiator(intuis_device)
        async_add_entities([entity])

    entry.async_on_unload(
        async_dispatcher_connect(hass, INTUIS_CREATE_CLIMATE, _create_entity)
    )

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_SCHEDULE,
        {vol.Required(ATTR_SCHEDULE_NAME): cv.string},
        "_async_service_set_schedule",
    )
    platform.async_register_entity_service(
        SERVICE_SET_PRESET_MODE_WITH_END_DATETIME,
        {
            vol.Required(ATTR_PRESET_MODE): vol.In(THERM_MODES),
            vol.Required(ATTR_END_DATETIME): cv.datetime,
        },
        "_async_service_set_preset_mode_with_end_datetime",
    )


class IntuisRadiator(ClimateEntity):
    """Representation of an Intuis electric radiator."""

    _attr_hvac_mode = HVACMode.AUTO
    _attr_max_temp = DEFAULT_MAX_TEMP
    _attr_preset_modes = SUPPORT_PRESET
    _attr_supported_features = SUPPORT_FLAGS
    _attr_target_temperature_step = PRECISION_HALVES
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, intuis_device: IntuisRoom) -> None:
        """Initialize the radiator."""
        ClimateEntity.__init__(self)

        self._room = intuis_device.room
        self._data_handler = intuis_device.data_handler
        self._id = self._room.entity_id
        self._home_id = intuis_device.home_id
        self._signal_name = intuis_device.signal_name

        self._config_url = CONF_URL_ENERGY

        self._attr_name = self._room.name
        self._away: bool | None = None
        self._connected: bool | None = None

        self._away_temperature: float | None = None
        self._hg_temperature: float | None = None
        self._selected_schedule = None

        # Intuis modules (NLC) support AUTO and HEAT modes
        self._attr_hvac_modes = [HVACMode.AUTO, HVACMode.HEAT, HVACMode.OFF]

        self._attr_unique_id = f"{self._room.entity_id}-{DEVICE_TYPE_NLC}"
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        """Entity created."""
        await super().async_added_to_hass()

        # Subscribe to data updates
        await self._data_handler.subscribe(
            "home",
            self._signal_name,
            self.async_update_callback,
        )

        # Subscribe to webhook events
        for event_type in (
            EVENT_TYPE_SET_POINT,
            EVENT_TYPE_THERM_MODE,
            EVENT_TYPE_CANCEL_SET_POINT,
            EVENT_TYPE_SCHEDULE,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"signal-{DOMAIN}-webhook-{event_type}",
                    self.handle_event,
                )
            )

        # Initial update
        self.async_update_callback()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from data updates."""
        await self._data_handler.unsubscribe(
            "home",
            self.async_update_callback,
        )

    @callback
    def handle_event(self, event: dict) -> None:
        """Handle webhook events."""
        data = event["data"]

        if self._room.home.entity_id != data.get("home_id"):
            return

        if data["event_type"] == EVENT_TYPE_SCHEDULE and "schedule_id" in data:
            schedule = self.hass.data[DOMAIN][DATA_SCHEDULES].get(
                self._room.home.entity_id, {}
            ).get(data["schedule_id"])
            self._selected_schedule = getattr(schedule, "name", None)
            self._attr_extra_state_attributes[
                ATTR_SELECTED_SCHEDULE
            ] = self._selected_schedule
            self.async_write_ha_state()
            self._data_handler.async_force_update(self._signal_name)
            return

        home = data.get("home")
        if not home or self._room.home.entity_id != home.get("id"):
            return

        if data["event_type"] == EVENT_TYPE_THERM_MODE:
            self._attr_preset_mode = NETATMO_MAP_PRESET[home[EVENT_TYPE_THERM_MODE]]
            self._attr_hvac_mode = HVAC_MAP_NETATMO[self._attr_preset_mode]
            if self._attr_preset_mode == PRESET_FROST_GUARD:
                self._attr_target_temperature = self._hg_temperature
            elif self._attr_preset_mode == PRESET_AWAY:
                self._attr_target_temperature = self._away_temperature
            elif self._attr_preset_mode in [PRESET_SCHEDULE, PRESET_HOME]:
                self.async_update_callback()
                self._data_handler.async_force_update(self._signal_name)
            self.async_write_ha_state()
            return

        for room in home.get("rooms", []):
            if (
                data["event_type"] == EVENT_TYPE_SET_POINT
                and self._room.entity_id == room["id"]
            ):
                if room["therm_setpoint_mode"] == STATE_NETATMO_OFF:
                    self._attr_hvac_mode = HVACMode.OFF
                    self._attr_preset_mode = STATE_NETATMO_OFF
                    self._attr_target_temperature = 0
                elif room["therm_setpoint_mode"] == STATE_NETATMO_MAX:
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_preset_mode = PRESET_MAP_NETATMO[PRESET_BOOST]
                    self._attr_target_temperature = DEFAULT_MAX_TEMP
                elif room["therm_setpoint_mode"] == STATE_NETATMO_MANUAL:
                    self._attr_hvac_mode = HVACMode.HEAT
                    self._attr_target_temperature = room["therm_setpoint_temperature"]
                else:
                    self._attr_target_temperature = room["therm_setpoint_temperature"]
                    if self._attr_target_temperature == DEFAULT_MAX_TEMP:
                        self._attr_hvac_mode = HVACMode.HEAT
                self.async_write_ha_state()
                return

            if (
                data["event_type"] == EVENT_TYPE_CANCEL_SET_POINT
                and self._room.entity_id == room["id"]
            ):
                if self._attr_hvac_mode == HVACMode.OFF:
                    self._attr_hvac_mode = HVACMode.AUTO
                    self._attr_preset_mode = PRESET_MAP_NETATMO[PRESET_SCHEDULE]

                self.async_update_callback()
                self.async_write_ha_state()
                return

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation if supported."""
        # For Intuis modules, check heating power request
        if (
            heating_req := getattr(self._room, "heating_power_request", 0)
        ) is not None and heating_req > 0:
            return HVACAction.HEATING
        return HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        elif hvac_mode == HVACMode.AUTO:
            await self.async_set_preset_mode(PRESET_SCHEDULE)
        elif hvac_mode == HVACMode.HEAT:
            await self.async_set_preset_mode(PRESET_BOOST)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode in (PRESET_BOOST, STATE_NETATMO_MAX):
            # For Intuis radiators, boost mode sets manual max temp
            await self._room.async_therm_set(
                STATE_NETATMO_MANUAL,
                DEFAULT_MAX_TEMP,
            )
        elif preset_mode in THERM_MODES:
            await self._room.home.async_set_thermmode(PRESET_MAP_NETATMO[preset_mode])
        else:
            _LOGGER.error("Preset mode '%s' not available", preset_mode)

        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature for 2 hours."""
        await self._room.async_therm_set(
            STATE_NETATMO_MANUAL, min(kwargs[ATTR_TEMPERATURE], DEFAULT_MAX_TEMP)
        )
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        # For Intuis radiators, set minimum temperature
        await self._room.async_therm_set(
            STATE_NETATMO_MANUAL,
            DEFAULT_MIN_TEMP,
        )
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self._room.async_therm_set(STATE_NETATMO_HOME)
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """If the device hasn't been able to connect, mark as unavailable."""
        return bool(self._connected)

    @callback
    def async_update_callback(self) -> None:
        """Update the entity's state."""
        if not self._room.reachable:
            if self.available:
                self._connected = False
            return

        self._connected = True

        self._away_temperature = self._room.home.get_away_temp()
        self._hg_temperature = self._room.home.get_hg_temp()
        self._attr_current_temperature = self._room.therm_measured_temperature
        self._attr_target_temperature = self._room.therm_setpoint_temperature
        self._attr_preset_mode = NETATMO_MAP_PRESET[
            getattr(self._room, "therm_setpoint_mode", STATE_NETATMO_SCHEDULE)
        ]
        self._attr_hvac_mode = HVAC_MAP_NETATMO[self._attr_preset_mode]
        self._away = self._attr_hvac_mode == HVAC_MAP_NETATMO[STATE_NETATMO_AWAY]

        self._selected_schedule = getattr(
            self._room.home.get_selected_schedule(), "name", None
        )
        self._attr_extra_state_attributes[
            ATTR_SELECTED_SCHEDULE
        ] = self._selected_schedule

        # Add heating power request for Intuis modules
        self._attr_extra_state_attributes[
            ATTR_HEATING_POWER_REQUEST
        ] = self._room.heating_power_request

    async def _async_service_set_schedule(self, **kwargs: Any) -> None:
        """Set schedule service."""
        schedule_name = kwargs.get(ATTR_SCHEDULE_NAME)
        schedule_id = None
        for sid, schedule in self.hass.data[DOMAIN][DATA_SCHEDULES][
            self._room.home.entity_id
        ].items():
            if schedule.name == schedule_name:
                schedule_id = sid
                break

        if not schedule_id:
            _LOGGER.error("%s is not a valid schedule", kwargs.get(ATTR_SCHEDULE_NAME))
            return

        await self._room.home.async_switch_schedule(schedule_id=schedule_id)
        _LOGGER.debug(
            "Setting %s schedule to %s (%s)",
            self._room.home.entity_id,
            kwargs.get(ATTR_SCHEDULE_NAME),
            schedule_id,
        )

    async def _async_service_set_preset_mode_with_end_datetime(
        self, **kwargs: Any
    ) -> None:
        """Set preset mode with end datetime service."""
        preset_mode = kwargs[ATTR_PRESET_MODE]
        end_datetime = kwargs[ATTR_END_DATETIME]
        end_timestamp = int(dt_util.as_timestamp(end_datetime))

        await self._room.home.async_set_thermmode(
            mode=PRESET_MAP_NETATMO[preset_mode], end_time=end_timestamp
        )
        _LOGGER.debug(
            "Setting %s preset to %s with optional end datetime to %s",
            self._room.home.entity_id,
            preset_mode,
            end_timestamp,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info for the radiator."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            name=self._room.name,
            manufacturer=MANUFACTURER,
            model=DEVICE_TYPE_NLC,
            suggested_area=self._room.name,
            configuration_url=self._config_url,
        )
