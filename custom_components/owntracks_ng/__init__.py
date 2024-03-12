from __future__ import annotations
from .constants import DOMAIN, PLATFORMS
from .coordinator import Coordinator, Platform

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from aiohttp.web import json_response
from homeassistant.components import webhook


import voluptuous as vol
import homeassistant.helpers.config_validation as cv

import logging
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
    }, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)

async def _async_handle_webhook(hass, webhook_id, request):
    try:
        message = await request.json()
    except ValueError:
        _LOGGER.warning(f"Invalid JSON in Webhook")
        return json_response([])
    _LOGGER.debug(f"JSON: {message}")
    if coordinator := hass.data[DOMAIN]["devices"].get(hass.data[DOMAIN]["webhooks"].get(webhook_id)):
        return json_response(await coordinator.async_handle_webhook(message))
    # return json_response([{"_type": "cmd", "action": "setConfiguration", "configuration": {"_type": "configuration", "monitoring": 2}}])
    _LOGGER.warning(f"Invalid Webhook ID: {webhook_id}")
    return json_response([])

async def _async_update_entry(hass, entry):
    _LOGGER.debug(f"_async_update_entry: {entry}")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

async def async_setup_entry(hass: HomeAssistant, entry):
    data = entry.as_dict()["options"]
    hook_id = data["webhook"]
    hass.data[DOMAIN]["webhooks"][hook_id] = entry.entry_id

    webhook.async_register(hass, DOMAIN, "OwnTracks NG", hook_id, _async_handle_webhook)

    platform = hass.data[DOMAIN]["platform"]
    coordinator = Coordinator(platform, entry)
    hass.data[DOMAIN]["devices"][entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_entry))
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_load()

    for p in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, p)
        )
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    data = entry.as_dict()["options"]
    hook_id = data["webhook"]
    webhook.async_unregister(hass, hook_id)
    hass.data[DOMAIN]["webhooks"].pop(hook_id)

    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    for p in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, p)
    await coordinator.async_unload()
    hass.data[DOMAIN]["devices"].pop(entry.entry_id)
    return True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    platform = Platform(hass)
    await platform.async_load()
    hass.data[DOMAIN] = {"devices": {}, "webhooks": {}, "platform": platform}
    return True
