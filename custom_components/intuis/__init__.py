"""The Intuis Connect with Netatmo integration."""

from __future__ import annotations

from http import HTTPStatus
import logging
import secrets
from typing import Any

import aiohttp
import pyatmo

from homeassistant.components import cloud
from homeassistant.components.webhook import (
    async_generate_url as webhook_generate_url,
    async_register as webhook_register,
    async_unregister as webhook_unregister,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_WEBHOOK_ID, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import (
    aiohttp_client,
    config_entry_oauth2_flow,
)
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.start import async_at_started

from .api import AsyncConfigEntryIntuisAuth, get_api_scopes
from .const import (
    AUTH,
    DATA_HANDLER,
    DATA_HOMES,
    DATA_SCHEDULES,
    DOMAIN,
    PLATFORMS,
)
from .data_handler import IntuisDataHandler
from .webhook import async_handle_webhook

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intuis from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    # Set unique id if none was set (migration)
    if not entry.unique_id:
        hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as ex:
        _LOGGER.warning("API error: %s (%s)", ex.status, ex.message)
        if ex.status in (
            HTTPStatus.BAD_REQUEST,
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
        ):
            raise ConfigEntryAuthFailed("Token not valid, trigger renewal") from ex
        raise ConfigEntryNotReady from ex

    required_scopes = get_api_scopes(entry.data.get("auth_implementation", ""))
    if not (set(session.token.get("scope", [])) & set(required_scopes)):
        _LOGGER.warning(
            "Session is missing scopes: %s",
            set(required_scopes) - set(session.token.get("scope", [])),
        )
        raise ConfigEntryAuthFailed("Token scope not valid, trigger renewal")

    # Initialize data storage
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_HOMES, {})
    hass.data[DOMAIN].setdefault(DATA_SCHEDULES, {})

    hass.data[DOMAIN][entry.entry_id] = {
        AUTH: AsyncConfigEntryIntuisAuth(
            aiohttp_client.async_get_clientsession(hass), session
        )
    }

    data_handler = IntuisDataHandler(hass, entry)
    hass.data[DOMAIN][entry.entry_id][DATA_HANDLER] = data_handler
    await data_handler.async_setup()

    async def unregister_webhook(_: Any) -> None:
        if CONF_WEBHOOK_ID not in entry.data:
            return
        _LOGGER.debug("Unregister Intuis webhook (%s)", entry.data[CONF_WEBHOOK_ID])
        webhook_unregister(hass, entry.data[CONF_WEBHOOK_ID])
        try:
            await hass.data[DOMAIN][entry.entry_id][AUTH].async_dropwebhook()
        except pyatmo.ApiError:
            _LOGGER.debug(
                "No webhook to be dropped for %s", entry.data[CONF_WEBHOOK_ID]
            )

    async def register_webhook(_: Any) -> None:
        if CONF_WEBHOOK_ID not in entry.data:
            data = {**entry.data, CONF_WEBHOOK_ID: secrets.token_hex()}
            hass.config_entries.async_update_entry(entry, data=data)

        if cloud.async_active_subscription(hass):
            if cloud.async_is_connected(hass):
                webhook_url = await cloud.async_create_cloudhook(
                    hass, entry.data[CONF_WEBHOOK_ID]
                )
            else:
                _LOGGER.warning("Cloud not connected, using local webhook")
                webhook_url = webhook_generate_url(hass, entry.data[CONF_WEBHOOK_ID])
        else:
            webhook_url = webhook_generate_url(hass, entry.data[CONF_WEBHOOK_ID])

        if entry.data.get(
            "auth_implementation"
        ) == cloud.DOMAIN and not webhook_url.startswith("https://"):
            _LOGGER.warning(
                "Webhook not registered - "
                "https and port 443 is required to register the webhook"
            )
            return

        webhook_register(
            hass,
            DOMAIN,
            "Intuis Connect with Netatmo",
            entry.data[CONF_WEBHOOK_ID],
            async_handle_webhook,
        )

        try:
            await hass.data[DOMAIN][entry.entry_id][AUTH].async_addwebhook(webhook_url)
            _LOGGER.info("Register Intuis webhook: %s", webhook_url)
        except pyatmo.ApiError as err:
            _LOGGER.error("Error during webhook registration - %s", err)
        else:
            entry.async_on_unload(
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, unregister_webhook)
            )

    if cloud.async_active_subscription(hass) and cloud.async_is_connected(hass):
        await register_webhook(None)
    else:
        entry.async_on_unload(async_at_started(hass, register_webhook))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN]

    if CONF_WEBHOOK_ID in entry.data:
        webhook_unregister(hass, entry.data[CONF_WEBHOOK_ID])
        try:
            await data[entry.entry_id][AUTH].async_dropwebhook()
        except pyatmo.ApiError:
            _LOGGER.debug("No webhook to be dropped")
        _LOGGER.info("Unregister Intuis webhook")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and entry.entry_id in data:
        data.pop(entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Cleanup when entry is removed."""
    if CONF_WEBHOOK_ID in entry.data and cloud.async_active_subscription(hass):
        try:
            _LOGGER.debug(
                "Removing Intuis cloudhook (%s)", entry.data[CONF_WEBHOOK_ID]
            )
            await cloud.async_delete_cloudhook(hass, entry.data[CONF_WEBHOOK_ID])
        except cloud.CloudNotAvailable:
            pass
