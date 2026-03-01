"""Geo-location platform for Canal & River Trust stoppages."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.location import distance as haversine_distance

from .const import CRT_BASE_URL, DOMAIN, REASON_MAP, TYPE_MAP, WATERWAY_MAP
from .coordinator import CRTDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Canal & River Trust geo-location entities from a config entry."""
    coordinator: CRTDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    current_entities: dict[str, CRTStoppageEvent] = {}

    @callback
    def _async_update_entities() -> None:
        """Handle coordinator data updates."""
        if not coordinator.last_update_success or coordinator.data is None:
            return

        new_entities: list[CRTStoppageEvent] = []
        seen_ids: set[str] = set()

        for feature in coordinator.data:
            props = feature.get("properties", {})
            stoppage_id = str(props.get("id", ""))
            if not stoppage_id:
                continue

            # Extract coordinates from GeometryCollection
            coords = _extract_coordinates(feature.get("geometry"))
            if coords is None:
                continue

            seen_ids.add(stoppage_id)

            if stoppage_id not in current_entities:
                entity = CRTStoppageEvent(
                    hass, coordinator, feature, coords
                )
                current_entities[stoppage_id] = entity
                new_entities.append(entity)
            else:
                current_entities[stoppage_id].update_from_feature(
                    feature, coords
                )

        # Remove entities for stoppages no longer present
        removed_ids = set(current_entities.keys()) - seen_ids
        for removed_id in removed_ids:
            entity = current_entities.pop(removed_id)
            entity.async_remove_self()

        if new_entities:
            async_add_entities(new_entities)

    # Register listener and trigger initial population
    entry.async_on_unload(
        coordinator.async_add_listener(_async_update_entities)
    )

    # Populate entities from existing data if coordinator already has data
    if coordinator.data is not None:
        _async_update_entities()


def _extract_coordinates(
    geometry: dict[str, Any] | None,
) -> tuple[float, float] | None:
    """Extract latitude and longitude from a GeoJSON geometry.

    The API returns a GeometryCollection with Point geometries.
    GeoJSON coordinates are [longitude, latitude].
    """
    if geometry is None:
        return None

    geom_type = geometry.get("type", "")

    if geom_type == "GeometryCollection":
        geometries = geometry.get("geometries", [])
        for geom in geometries:
            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [])
                if len(coords) >= 2:
                    return (coords[1], coords[0])  # (lat, lon)
        return None

    if geom_type == "Point":
        coords = geometry.get("coordinates", [])
        if len(coords) >= 2:
            return (coords[1], coords[0])  # (lat, lon)

    return None


class CRTStoppageEvent(GeolocationEvent):
    """Represent a Canal & River Trust stoppage as a geo-location event."""

    _attr_icon = "mdi:map-marker-alert"
    _attr_source = DOMAIN
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: CRTDataCoordinator,
        feature: dict[str, Any],
        coords: tuple[float, float],
    ) -> None:
        """Initialise the stoppage geo-location event."""
        self.hass = hass
        self._coordinator = coordinator
        self._stoppage_id: str = str(feature["properties"]["id"])
        self._attr_unique_id = f"{DOMAIN}_stoppage_{self._stoppage_id}"
        self._update_internal(feature, coords)

    def _update_internal(
        self,
        feature: dict[str, Any],
        coords: tuple[float, float],
    ) -> None:
        """Update internal state from a GeoJSON feature."""
        props = feature.get("properties", {})

        self._attr_name = props.get("title", "Unknown Stoppage")
        self._attr_latitude = coords[0]
        self._attr_longitude = coords[1]
        self._props = props

        # Calculate distance from Home Assistant home coordinates
        home_lat = self.hass.config.latitude
        home_lon = self.hass.config.longitude
        dist_metres = haversine_distance(
            home_lat, home_lon, coords[0], coords[1]
        )
        self._attr_distance = (
            round(dist_metres / 1000.0, 1) if dist_metres is not None else None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes for the stoppage."""
        props = self._props
        type_id = props.get("typeId")
        reason_id = props.get("reasonId")

        # Resolve waterway names from codes
        waterway_codes = props.get("waterways", [])
        if isinstance(waterway_codes, list):
            waterways = ", ".join(
                WATERWAY_MAP.get(code, code) for code in waterway_codes
            )
        else:
            waterways = str(waterway_codes)

        path = props.get("path", "")
        url = f"{CRT_BASE_URL}{path}" if path else None

        return {
            "type": TYPE_MAP.get(type_id, str(type_id)) if type_id is not None else None,
            "reason": REASON_MAP.get(reason_id, str(reason_id)) if reason_id is not None else None,
            "waterway": waterways or None,
            "start_date": props.get("start"),
            "end_date": props.get("end"),
            "description": props.get("description", ""),
            "url": url,
        }

    @callback
    def update_from_feature(
        self,
        feature: dict[str, Any],
        coords: tuple[float, float],
    ) -> None:
        """Update entity from a new feature and schedule a state write."""
        self._update_internal(feature, coords)
        self.async_write_ha_state()

    @callback
    def async_remove_self(self) -> None:
        """Remove this entity."""
        self.hass.async_create_task(self.async_remove())

