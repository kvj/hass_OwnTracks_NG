from collections.abc import Mapping
from typing import Any, cast

from homeassistant import config_entries
from homeassistant.core import async_get_hass
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector
from homeassistant.components import webhook

from homeassistant.const import (
    CONF_NAME,
)

from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from .constants import (
    DOMAIN,
    CONF_WEBHOOK,
    CONF_DEVICE_TRACKERS,
)

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

def _create_webhook(hass) -> str:
    id = webhook.async_generate_id()
    url = webhook.async_generate_url(hass, id)
    return id, url

OPTIONS_SCHEMA = vol.Schema({
    vol.Required(CONF_WEBHOOK, description={"suggested_value": ""}): selector({"text": {}}),
    vol.Required(CONF_DEVICE_TRACKERS, description={"suggested_value": []}): selector({
        "entity": {
            "multiple": True,
            "filter": {
                "domain": ["person", "device_tracker"],
            },
        },
    }),
})

CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): selector({"text": {}}),
}).extend(OPTIONS_SCHEMA.schema)

async def _validate(step, user_input):
    _LOGGER.debug(f"_validate: {user_input}")
    return user_input

async def _suggest_values(step) -> dict:
    id, url = _create_webhook(async_get_hass())
    return {"webhook": id}

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA, _validate, suggested_values=_suggest_values),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA, _validate),
}

class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow for Derivative."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        return cast(str, options[CONF_NAME])
