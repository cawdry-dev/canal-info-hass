"""Data update coordinator for Canal & River Trust Stoppages."""

from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any

from aiohttp import ClientError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE_URL, DEFAULT_SCAN_INTERVAL, LOOKAHEAD_DAYS

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

        return filtered

