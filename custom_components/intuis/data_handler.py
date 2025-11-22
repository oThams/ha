"""The Intuis data handler."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from itertools import islice
import logging
from time import time

import pyatmo

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    AUTH,
    DATA_SCHEDULES,
    DOMAIN,
    INTUIS_CREATE_CLIMATE,
    MANUFACTURER,
    PLATFORMS,
    SIGNAL_NAME,
)

_LOGGER = logging.getLogger(__name__)

HOME = "home"

PUBLISHERS = {
    HOME: "async_update_status",
}

BATCH_SIZE = 3
DEFAULT_INTERVALS = {
    HOME: 300,  # 5 minutes
}
SCAN_INTERVAL = 60


@dataclass
class IntuisRoom:
    """Intuis room class."""

    data_handler: IntuisDataHandler
    room: pyatmo.Room
    home_id: str
    signal_name: str


@dataclass
class IntuisPublisher:
    """Class for keeping track of Intuis data class metadata."""

    name: str
    interval: int
    next_scan: float
    subscriptions: set[CALLBACK_TYPE | None]
    method: str
    kwargs: dict


class IntuisDataHandler:
    """Manages the Intuis data handling."""

    account: pyatmo.AsyncAccount

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize self."""
        self.hass = hass
        self.config_entry = config_entry
        self._auth = hass.data[DOMAIN][config_entry.entry_id][AUTH]
        self.publisher: dict[str, IntuisPublisher] = {}
        self._queue: deque = deque()

    async def async_setup(self) -> None:
        """Set up the Intuis data handler."""
        self.config_entry.async_on_unload(
            async_track_time_interval(
                self.hass, self.async_update, timedelta(seconds=SCAN_INTERVAL)
            )
        )

        self.account = pyatmo.AsyncAccount(self._auth)

        # Subscribe to home data (topology and status)
        await self.subscribe(HOME, HOME, None)

        # Forward entry setups for all platforms
        await self.hass.config_entries.async_forward_entry_setups(
            self.config_entry, PLATFORMS
        )

        # Dispatch initial data
        await self.async_dispatch()

    async def async_update(self, event_time) -> None:
        """Update device.

        We do up to BATCH_SIZE calls in one update in order
        to minimize the calls on the api service.
        """
        for data_class in islice(self._queue, 0, BATCH_SIZE):
            if data_class.next_scan > time():
                continue

            if publisher := data_class.name:
                self.publisher[publisher].next_scan = time() + data_class.interval

                await self.async_fetch_data(publisher)

        self._queue.rotate(BATCH_SIZE)

    @callback
    def async_force_update(self, signal_name: str) -> None:
        """Prioritize data retrieval for given data class entry."""
        self.publisher[signal_name].next_scan = time()
        self._queue.rotate(-(self._queue.index(self.publisher[signal_name])))

    async def subscribe(
        self,
        publisher: str,
        signal_name: str,
        callback_fun: CALLBACK_TYPE | None,
        **kwargs,
    ) -> None:
        """Subscribe to publisher."""
        if publisher not in self.publisher:
            self.publisher[publisher] = IntuisPublisher(
                name=publisher,
                interval=DEFAULT_INTERVALS[publisher],
                next_scan=time() + DEFAULT_INTERVALS[publisher],
                subscriptions=set(),
                method=PUBLISHERS[publisher],
                kwargs=kwargs,
            )
            self._queue.append(self.publisher[publisher])

        self.publisher[publisher].subscriptions.add(callback_fun)

    async def unsubscribe(
        self,
        publisher: str,
        callback_fun: CALLBACK_TYPE | None,
    ) -> None:
        """Unsubscribe from publisher."""
        if publisher in self.publisher:
            if callback_fun in self.publisher[publisher].subscriptions:
                self.publisher[publisher].subscriptions.remove(callback_fun)

            if not self.publisher[publisher].subscriptions:
                self._queue.remove(self.publisher[publisher])
                self.publisher.pop(publisher)

    async def async_fetch_data(self, signal_name: str) -> None:
        """Fetch data for given publisher."""
        try:
            publisher = self.publisher[signal_name]
            method = getattr(self.account, publisher.method)
            await method(**publisher.kwargs)
            _LOGGER.debug("Fetched data for %s", signal_name)
        except pyatmo.ApiError as err:
            _LOGGER.error("Error fetching %s data: %s", signal_name, err)

        # Notify subscribers
        for callback_fun in publisher.subscriptions:
            if callback_fun:
                callback_fun()

    async def async_dispatch(self) -> None:
        """Dispatch all entities."""
        # Fetch initial data
        for publisher_name in self.publisher:
            await self.async_fetch_data(publisher_name)

        # Create climate entities for each room with Intuis modules
        if not self.account.homes:
            _LOGGER.warning("No homes found in Intuis account")
            return

        for home in self.account.homes.values():
            # Store schedules
            self.hass.data[DOMAIN][DATA_SCHEDULES][home.entity_id] = home.schedules

            for room in home.rooms.values():
                # Check if room has climate control (Intuis modules)
                if not room.climate_type:
                    continue

                signal_name = f"{HOME}-{home.entity_id}"
                room_data = IntuisRoom(
                    data_handler=self,
                    room=room,
                    home_id=home.entity_id,
                    signal_name=signal_name,
                )

                # Create climate entity
                async_dispatcher_send(
                    self.hass, INTUIS_CREATE_CLIMATE, room_data
                )
                _LOGGER.debug("Created climate entity for room %s", room.name)
