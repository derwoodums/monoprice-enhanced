"""Config flow for Monoprice Enhanced integration."""

from __future__ import annotations

import logging
from typing import Any

from pymonoprice import get_monoprice
from serial import SerialException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_NOT_FIRST_RUN,
    CONF_SOURCES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SOURCES = {
    1: "Source 1",
    2: "Source 2",
    3: "Source 3",
    4: "Source 4",
    5: "Source 5",
    6: "Source 6",
}

ZONES = {
    11: "Zone 1",
    12: "Zone 2",
    13: "Zone 3",
    14: "Zone 4",
    15: "Zone 5",
    16: "Zone 6",
}

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(source, default=SOURCES[source]): str
        for source in SOURCES
    }
)


async def validate_input(hass, data):
    """Validate the user input allows us to connect."""
    try:
        await hass.async_add_executor_job(get_monoprice, data[CONF_PORT])
    except SerialException as err:
        _LOGGER.error("Error connecting to Monoprice: %s", err)
        raise

    return {"title": f"Monoprice {data[CONF_PORT]}"}


class MonopriceEnhancedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Monoprice Enhanced."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except SerialException:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Set first run flag
                user_input[CONF_NOT_FIRST_RUN] = True
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PORT): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MonopriceEnhancedOptionsFlow:
        """Get the options flow for this handler."""
        return MonopriceEnhancedOptionsFlow(config_entry)


class MonopriceEnhancedOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Monoprice Enhanced."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_SOURCES: user_input},
            )

        current_sources = self.config_entry.options.get(CONF_SOURCES, SOURCES)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        str(source),
                        default=current_sources.get(str(source), SOURCES[source]),
                    ): str
                    for source in SOURCES
                }
            ),
        )
