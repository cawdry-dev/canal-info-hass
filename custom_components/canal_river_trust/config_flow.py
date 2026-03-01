"""Config flow for Canal & River Trust Stoppages integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_WATERWAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    WATERWAY_MAP,
)

# Default scan interval in minutes for the UI
DEFAULT_SCAN_INTERVAL_MINUTES = int(DEFAULT_SCAN_INTERVAL.total_seconds()) // 60


class CanalRiverTrustConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Canal & River Trust Stoppages."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            waterways = user_input.get(CONF_WATERWAYS, [])
            if not waterways:
                errors[CONF_WATERWAYS] = "no_waterways_selected"
            else:
                scan_interval = user_input.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                )
                return self.async_create_entry(
                    title="CRT Stoppages",
                    data={
                        CONF_WATERWAYS: waterways,
                        CONF_SCAN_INTERVAL: scan_interval,
                    },
                )

        waterway_options = {
            code: name for code, name in WATERWAY_MAP.items()
        }

        data_schema = vol.Schema(
            {
                vol.Required(CONF_WATERWAYS): vol.All(
                    vol.Coerce(list),
                    [vol.In(waterway_options)],
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL_MINUTES,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=5),
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> CanalRiverTrustOptionsFlow:
        """Get the options flow for this handler."""
        return CanalRiverTrustOptionsFlow(config_entry)


class CanalRiverTrustOptionsFlow(OptionsFlow):
    """Handle options flow for Canal & River Trust Stoppages."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialise options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            waterways = user_input.get(CONF_WATERWAYS, [])
            if not waterways:
                errors[CONF_WATERWAYS] = "no_waterways_selected"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_WATERWAYS: waterways,
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                        ),
                    },
                )

        current_waterways = self.config_entry.data.get(CONF_WATERWAYS, [])
        current_scan_interval = self.config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
        )

        waterway_options = {
            code: name for code, name in WATERWAY_MAP.items()
        }

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_WATERWAYS,
                    default=current_waterways,
                ): vol.All(
                    vol.Coerce(list),
                    [vol.In(waterway_options)],
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=5),
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )

