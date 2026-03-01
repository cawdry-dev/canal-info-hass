"""Config flow for Canal & River Trust Stoppages integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_WATERWAYS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    WATERWAY_MAP,
)

# Default scan interval in minutes for the UI
DEFAULT_SCAN_INTERVAL_MINUTES = int(DEFAULT_SCAN_INTERVAL.total_seconds()) // 60


def _waterway_selector() -> SelectSelector:
    """Build a multi-select dropdown selector for waterways."""
    return SelectSelector(
        SelectSelectorConfig(
            options=[
                {"value": code, "label": name}
                for code, name in sorted(WATERWAY_MAP.items(), key=lambda x: x[1])
            ],
            multiple=True,
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


class CanalRiverTrustConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Canal & River Trust Stoppages."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
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

        data_schema = vol.Schema(
            {
                vol.Required(CONF_WATERWAYS): _waterway_selector(),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL_MINUTES,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=1440,
                        step=1,
                        unit_of_measurement="minutes",
                        mode=NumberSelectorMode.BOX,
                    )
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
        return CanalRiverTrustOptionsFlow()


class CanalRiverTrustOptionsFlow(OptionsFlow):
    """Handle options flow for Canal & River Trust Stoppages."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
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

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_WATERWAYS,
                    default=current_waterways,
                ): _waterway_selector(),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=5,
                        max=1440,
                        step=1,
                        unit_of_measurement="minutes",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )

