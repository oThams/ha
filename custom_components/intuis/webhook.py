"""The Intuis webhook handler."""

import logging

from aiohttp.web import Request

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    DOMAIN,
    EVENT_TYPE_CANCEL_SET_POINT,
    EVENT_TYPE_SCHEDULE,
    EVENT_TYPE_SET_POINT,
    EVENT_TYPE_THERM_MODE,
)

_LOGGER = logging.getLogger(__name__)


async def async_handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: Request
) -> None:
    """Handle webhook callback."""
    try:
        data = await request.json()
    except ValueError as err:
        _LOGGER.error("Error in data: %s", err)
        return None

    _LOGGER.debug("Got Intuis webhook data: %s", data)

    event_type = data.get("event_type")

    # Only handle climate-related events for Intuis
    if event_type in (
        EVENT_TYPE_SET_POINT,
        EVENT_TYPE_THERM_MODE,
        EVENT_TYPE_CANCEL_SET_POINT,
        EVENT_TYPE_SCHEDULE,
    ):
        async_send_event(hass, event_type, data)


def async_send_event(hass: HomeAssistant, event_type: str, data: dict) -> None:
    """Send events."""
    _LOGGER.debug("%s: %s", event_type, data)
    async_dispatcher_send(
        hass,
        f"signal-{DOMAIN}-webhook-{event_type}",
        {"type": event_type, "data": data},
    )
