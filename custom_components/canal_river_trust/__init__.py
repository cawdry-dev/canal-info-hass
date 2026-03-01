"""Canal & River Trust Stoppages integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_WATERWAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import CRTDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Canal & River Trust Stoppages from a config entry."""
    waterways: list[str] = entry.data.get(CONF_WATERWAYS, [])
    scan_interval_minutes: int | None = entry.data.get(CONF_SCAN_INTERVAL)

    scan_interval: timedelta | None = None
    if scan_interval_minutes is not None:
        scan_interval = timedelta(minutes=scan_interval_minutes)

    coordinator = CRTDataCoordinator(
        hass,
        waterways=waterways,
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Canal & River Trust Stoppages config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

