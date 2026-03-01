"""Sensor platform for the Canal & River Trust integration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_WATERWAYS,
    CRT_BASE_URL,
    DOMAIN,
    REASON_MAP,
    TYPE_MAP,
    WATERWAY_MAP,
)
from .coordinator import CRTDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Navigation closure type IDs
_CLOSURE_TYPE_IDS = {1, 9}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Canal & River Trust sensors from a config entry."""
    coordinator: CRTDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    waterways: list[str] = entry.data.get(CONF_WATERWAYS, [])

    entities: list[SensorEntity] = []

    for code in waterways:
        name = WATERWAY_MAP.get(code, code)
        entities.append(CRTStoppageCountSensor(coordinator, entry, code, name))
        entities.append(CRTNextClosureSensor(coordinator, entry, code, name))

    entities.append(CRTTotalStoppagesSensor(coordinator, entry, waterways))

    async_add_entities(entities)


def _features_for_waterway(
    features: list[dict[str, Any]], code: str
) -> list[dict[str, Any]]:
    """Return features matching a given waterway code."""
    result: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties", {})
        waterways_val = props.get("waterways", "")
        if isinstance(waterways_val, str):
            codes = [c.strip() for c in waterways_val.split(",")]
        elif isinstance(waterways_val, list):
            codes = waterways_val
        else:
            codes = []
        if code in codes:
            result.append(feature)
    return result


def _stoppage_dict(feature: dict[str, Any]) -> dict[str, Any]:
    """Build a stoppage summary dict from a GeoJSON feature."""
    props = feature.get("properties", {})
    path = props.get("path", "")
    return {
        "id": props.get("id"),
        "title": props.get("title"),
        "type": TYPE_MAP.get(props.get("typeId"), "Unknown"),
        "reason": REASON_MAP.get(props.get("reasonId"), "Unknown"),
        "start": props.get("start"),
        "end": props.get("end"),
        "state": props.get("state"),
        "description": props.get("description", ""),
        "url": f"{CRT_BASE_URL}{path}" if path else None,
    }



class CRTStoppageCountSensor(
    CoordinatorEntity[CRTDataCoordinator], SensorEntity
):
    """Sensor showing the number of active stoppages for a waterway."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:ferry"

    def __init__(
        self,
        coordinator: CRTDataCoordinator,
        entry: ConfigEntry,
        waterway_code: str,
        waterway_name: str,
    ) -> None:
        """Initialise the stoppage count sensor."""
        super().__init__(coordinator)
        self._waterway_code = waterway_code
        self._attr_name = f"{waterway_name} Stoppages"
        self._attr_unique_id = f"crt_{waterway_code.lower()}_stoppages"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Canal & River Trust Stoppages",
            "manufacturer": "Canal & River Trust",
        }

    @property
    def native_value(self) -> int:
        """Return the number of active stoppages."""
        if self.coordinator.data is None:
            return 0
        features = _features_for_waterway(
            self.coordinator.data, self._waterway_code
        )
        return len(features)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return stoppage details as attributes."""
        if self.coordinator.data is None:
            return {"stoppages": []}
        features = _features_for_waterway(
            self.coordinator.data, self._waterway_code
        )
        return {"stoppages": [_stoppage_dict(f) for f in features]}


class CRTNextClosureSensor(
    CoordinatorEntity[CRTDataCoordinator], SensorEntity
):
    """Sensor showing the next navigation closure for a waterway."""

    _attr_icon = "mdi:calendar-alert"

    def __init__(
        self,
        coordinator: CRTDataCoordinator,
        entry: ConfigEntry,
        waterway_code: str,
        waterway_name: str,
    ) -> None:
        """Initialise the next closure sensor."""
        super().__init__(coordinator)
        self._waterway_code = waterway_code
        self._attr_name = f"{waterway_name} Next Closure"
        self._attr_unique_id = f"crt_{waterway_code.lower()}_next_closure"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Canal & River Trust Stoppages",
            "manufacturer": "Canal & River Trust",
        }

    def _next_closure(self) -> dict[str, Any] | None:
        """Find the next upcoming navigation closure."""
        if self.coordinator.data is None:
            return None
        features = _features_for_waterway(
            self.coordinator.data, self._waterway_code
        )
        closures: list[dict[str, Any]] = []
        for feature in features:
            props = feature.get("properties", {})
            type_id = props.get("typeId")
            if type_id in _CLOSURE_TYPE_IDS:
                closures.append(feature)

        if not closures:
            return None

        # Sort by start date and return the earliest
        def _sort_key(f: dict[str, Any]) -> str:
            return f.get("properties", {}).get("start", "") or ""

        closures.sort(key=_sort_key)
        return closures[0]

    @property
    def native_value(self) -> str | None:
        """Return the start date of the next closure."""
        closure = self._next_closure()
        if closure is None:
            return "None"
        start = closure.get("properties", {}).get("start")
        if start:
            try:
                return datetime.fromisoformat(start).date().isoformat()
            except (ValueError, TypeError):
                return start
        return "None"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details of the next closure."""
        closure = self._next_closure()
        if closure is None:
            return {}
        props = closure.get("properties", {})
        return {
            "title": props.get("title"),
            "description": props.get("description", ""),
            "start": props.get("start"),
            "end": props.get("end"),
        }


class CRTTotalStoppagesSensor(
    CoordinatorEntity[CRTDataCoordinator], SensorEntity
):
    """Sensor showing the total stoppages across all monitored waterways."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:alert-circle"

    def __init__(
        self,
        coordinator: CRTDataCoordinator,
        entry: ConfigEntry,
        waterways: list[str],
    ) -> None:
        """Initialise the total stoppages sensor."""
        super().__init__(coordinator)
        self._waterways = waterways
        self._attr_name = "CRT Total Stoppages"
        self._attr_unique_id = f"crt_total_stoppages_{entry.entry_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Canal & River Trust Stoppages",
            "manufacturer": "Canal & River Trust",
        }

    @property
    def native_value(self) -> int:
        """Return the total number of stoppages."""
        if self.coordinator.data is None:
            return 0
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return per-waterway stoppage counts."""
        if self.coordinator.data is None:
            return {"per_waterway": {}}
        per_waterway: dict[str, int] = {}
        for code in self._waterways:
            features = _features_for_waterway(self.coordinator.data, code)
            per_waterway[code] = len(features)
        return {"per_waterway": per_waterway}
