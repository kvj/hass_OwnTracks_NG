from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import storage
from homeassistant.util import dt

from .constants import (
    DOMAIN,
    CONF_DEVICE_TRACKERS,
)

import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class Platform():

    def __init__(self, hass):
        self.hass = hass
        self._storage = storage.Store(hass, 1, DOMAIN)

    async def async_load(self):
        data_ = await self._storage.async_load()
        _LOGGER.debug(f"async_load(): Loaded stored data: {data_}")
        self._storage_data = data_ if data_ else {}

    def get_data(self, key: str, def_={}):
        if key in self._storage_data:
            return self._storage_data[key]
        return def_

    async def async_put_data(self, key: str, data):
        if data:
            self._storage_data = {
                **self._storage_data,
                key: data,
            }
        else:
            if key in self._storage_data:
                del self._storage_data[key]
        await self._storage.async_save(self._storage_data)


class Coordinator(DataUpdateCoordinator):

    def __init__(self, platform, entry):
        super().__init__(
            platform.hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update,
        )
        self._platform = platform
        self._entry = entry
        self._entry_id = entry.entry_id

        self._config = entry.as_dict()["options"]

    async def _async_update(self):
        return self._platform.get_data(self._entry_id)

    async def _async_update_state(self, data: dict):
        self.async_set_updated_data({
            **self.data,
            **data,
        })
        await self._platform.async_put_data(self._entry_id, self.data)

    async def async_load(self):
        _LOGGER.debug(f"async_load: {self._config}")

    async def async_unload(self):
        _LOGGER.debug(f"async_unload:")

    async def _async_build_location(self, entity_id: str):
        state = self.hass.states.get(entity_id)
        if state and "latitude" in state.attributes and "longitude" in state.attributes:
            tid = state.attributes.get("tid", state.attributes.get("friendly_name", entity_id)[:2])
            tst = round(dt.as_timestamp(state.attributes.get("timestamp", state.last_updated)))
            result = {
                "_type": "location", 
                "lat": state.attributes["latitude"], 
                "lon": state.attributes["longitude"], 
                "tid": tid,
                "tst": tst,
                "acc": state.attributes.get("gps_accuracy", 0),
            }
            if "altitude" in state.attributes:
                result["alt"] = state.attributes["altitude"]
            _LOGGER.debug(f"_async_build_location: {state}, {state.attributes}, {result}")
            return result
        return None

    async def async_handle_webhook(self, data: dict):
        mapping = {"acc": "location_accuracy", "alt": "altitude", "batt": "battery_level", "lat": "latitude", "lon": "longitude", "m": "monitoring", "tid": "tid", "tst": "timestamp", "vel": "velocity", "vac": "vertical_accuracy"}
        result = []
        conf = {}
        if data.get("_type") == "location":
            loc_update = {}
            for (key, value) in mapping.items():
                if key in data:
                    loc_update[value] = data[key]
            if "latitude" in loc_update and "longitude" in loc_update:
                _LOGGER.debug(f"async_handle_webhook: Location update: {loc_update}")
                await self._async_update_state({"location": loc_update})
            else:
                _LOGGER.warning(f"async_handle_webhook: Invalid location update: {loc_update}")
        if (m := self.data.get("mode")) != None:
            conf["monitoring"] = m
            await self.async_update_mode(None)
        if len(conf):
            conf["_type"] = "configuration"
            result.append({"_type": "cmd", "action": "setConfiguration", "configuration": conf})
        for id in self._config.get(CONF_DEVICE_TRACKERS, []):
            if obj := await self._async_build_location(id):
                result.append(obj)            
        if len(result):
            _LOGGER.debug(f"async_handle_webhook: response = {result}")
        return result

    async def async_update_mode(self, mode):
        await self._async_update_state({"mode": mode})

class BaseEntity(CoordinatorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    def with_name(self, id: str, name: str):
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{DOMAIN}_{self.coordinator._entry_id}_{id}"
        self._attr_name = name
        return self

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("entry_id", self.coordinator._entry_id), 
            },
            "name": self.coordinator._entry.title,
        }
