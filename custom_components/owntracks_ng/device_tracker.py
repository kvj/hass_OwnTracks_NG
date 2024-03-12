from homeassistant.components import device_tracker, webhook
from homeassistant.helpers.entity import EntityCategory

from .coordinator import BaseEntity
from .constants import (DOMAIN, CONF_WEBHOOK)

from datetime import datetime
from homeassistant.util import dt

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    async_setup_entities([_Position(coordinator)])

class _Position(BaseEntity, device_tracker.TrackerEntity):

    _unrecorded_attributes = frozenset({CONF_WEBHOOK})

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"position", None)
        self._attr_entity_category = None

    @property
    def _data(self):
        return self.coordinator.data.get("location", {})

    @property
    def latitude(self) -> float | None:
        return self._data.get("latitude")

    @property
    def longitude(self) -> float | None:
        return self._data.get("longitude")

    @property
    def battery_level(self) -> int | None:
        return self._data.get("battery_level")

    @property
    def location_accuracy(self) -> int:
        return self._data.get("location_accuracy", 0)

    @property
    def source_type(self) -> device_tracker.SourceType | str:
        return device_tracker.SourceType.GPS

    @property
    def extra_state_attributes(self):
        result = dict()
        result[CONF_WEBHOOK] = webhook.async_generate_path(self.coordinator._config[CONF_WEBHOOK])
        data_ = self._data
        fields = ("altitude", "tid", "velocity", "vertical_accuracy")
        for f in fields:
            if f in data_:
                result[f] = data_[f]
        if "monitoring" in data_:
            result["mode"] = {-1: "quiet", 0: "manual", 1: "significant", 2: "move"}.get(data_["monitoring"])
        if "timestamp" in data_:
            result["timestamp"] = datetime.fromtimestamp(data_["timestamp"], dt.UTC)
        _LOGGER.debug(f"state_attributes: {result}")
        return result
