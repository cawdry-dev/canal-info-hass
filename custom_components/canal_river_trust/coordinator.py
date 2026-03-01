"""Data update coordinator for Canal & River Trust Stoppages."""

from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_BASE_URL,
    CRT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    LOOKAHEAD_DAYS,
    REASON_MAP,
    TYPE_MAP,
    WATERWAY_MAP,
)

_LOGGER = logging.getLogger(__name__)


class CRTDataCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator to fetch stoppage data from the Canal & River Trust API."""

    def __init__(
        self,
        hass: HomeAssistant,
        waterways: list[str],
        scan_interval: timedelta | None = None,
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Canal & River Trust Stoppages",
            update_interval=scan_interval or DEFAULT_SCAN_INTERVAL,
        )
        self._waterways = waterways
        self._previous_stoppage_ids: set[str] = set()
        self._stoppage_data: dict[str, dict] = {}
        self._first_fetch = True

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch stoppage data from the CRT API."""
        today = date.today()
        end_date = today + timedelta(days=LOOKAHEAD_DAYS)

        url = API_BASE_URL.format(
            start=today.isoformat(),
            end=end_date.isoformat(),
        )

        session = async_get_clientsession(self.hass)

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
        except ClientError as err:
            raise UpdateFailed(
                f"Error fetching data from Canal & River Trust API: {err}"
            ) from err
        except (ValueError, KeyError) as err:
            raise UpdateFailed(
                f"Error parsing Canal & River Trust API response: {err}"
            ) from err

        features = data.get("features", [])

        # Filter features by configured waterways
        filtered: list[dict[str, Any]] = []
        for feature in features:
            properties = feature.get("properties", {})
            feature_waterways = properties.get("waterways", "")

            # The waterways field may be a comma-separated string of codes
            if isinstance(feature_waterways, str):
                feature_codes = [
                    code.strip() for code in feature_waterways.split(",")
                ]
            elif isinstance(feature_waterways, list):
                feature_codes = feature_waterways
            else:
                feature_codes = []

            if any(code in self._waterways for code in feature_codes):
                filtered.append(feature)

        # Collect current stoppage IDs and build event data cache
        current_ids: set[str] = set()
        current_data: dict[str, dict] = {}

        for feature in filtered:
            properties = feature.get("properties", {})
            stoppage_id = str(properties.get("id", ""))
            if not stoppage_id:
                continue

            feature_waterways = properties.get("waterways", "")
            if isinstance(feature_waterways, str):
                waterway_codes = [
                    code.strip() for code in feature_waterways.split(",")
                ]
            elif isinstance(feature_waterways, list):
                waterway_codes = feature_waterways
            else:
                waterway_codes = []

            # Use the first matching waterway code for the event data
            waterway_code = waterway_codes[0] if waterway_codes else ""
            waterway_name = WATERWAY_MAP.get(waterway_code, waterway_code)

            path = properties.get("path", "")
            event_data = {
                "id": stoppage_id,
                "title": properties.get("title", ""),
                "type": TYPE_MAP.get(properties.get("typeId", 0), "Unknown"),
                "reason": REASON_MAP.get(properties.get("reasonId", 0), "Unknown"),
                "waterway": waterway_name,
                "waterway_code": waterway_code,
                "start": properties.get("start", ""),
                "end": properties.get("end", ""),
                "description": properties.get("description", ""),
                "url": f"{CRT_BASE_URL}{path}" if path else "",
            }

            current_ids.add(stoppage_id)
            current_data[stoppage_id] = event_data

        # Fire events for new and resolved stoppages (skip first fetch)
        if not self._first_fetch:
            new_ids = current_ids - self._previous_stoppage_ids
            resolved_ids = self._previous_stoppage_ids - current_ids

            for sid in new_ids:
                self.hass.bus.async_fire("crt_new_stoppage", current_data[sid])

            for sid in resolved_ids:
                cached = self._stoppage_data.get(sid, {})
                if cached:
                    self.hass.bus.async_fire("crt_stoppage_resolved", cached)

        self._first_fetch = False
        self._previous_stoppage_ids = current_ids
        self._stoppage_data = current_data

        return filtered

