from homeassistant.components import select
from homeassistant.helpers.entity import EntityCategory

from .coordinator import BaseEntity
from .constants import (DOMAIN)

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    async_setup_entities([_Mode(coordinator)])

class _Mode(BaseEntity, select.SelectEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"mode", "Monitoring Mode")
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_options = ["Quiet", "Manual", "Significant", "Move"]

    @property
    def current_option(self):
        value = self.coordinator.data.get("mode")
        if value == None:
            value = self.coordinator.data.get("location", {}).get("monitoring")
        return {-1: "Quiet", 0: "Manual", 1: "Significant", 2: "Move"}.get(value)

    async def async_select_option(self, option: str) -> None:
        mode = {"Quiet": -1, "Manual": 0, "Significant": 1, "Move": 2}.get(option)
        await self.coordinator.async_update_mode(mode)
