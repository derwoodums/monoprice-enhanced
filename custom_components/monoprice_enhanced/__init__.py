"""The Monoprice 6-Zone Amplifier Enhanced integration."""

import json
import logging
from pathlib import Path

from pymonoprice import get_monoprice
from serial import SerialException

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_NOT_FIRST_RUN,
    DOMAIN,
    FIRST_RUN,
    MONOPRICE_OBJECT,
    UNDO_UPDATE_LISTENER,
)

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.NUMBER]

_LOGGER = logging.getLogger(__name__)

CARD_JS = "monoprice-zone-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_JS}"


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the Lovelace card as a frontend resource."""
    manifest = json.loads((Path(__file__).parent / "manifest.json").read_text())
    version = manifest.get("version", "0")
    versioned_url = f"{CARD_URL}?v={version}"

    # Serve the JS file at /monoprice_enhanced/monoprice-zone-card.js
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(CARD_URL, str(Path(__file__).parent / CARD_JS), False),
        ])
    except Exception:
        _LOGGER.warning("Could not register static path for Lovelace card")

    # Primary: register as a proper Lovelace resource (survives restarts)
    await _register_card_resource(hass, versioned_url)

    # Fallback: also inject via add_extra_js_url for immediate availability
    add_extra_js_url(hass, versioned_url)

    return True


async def _register_card_resource(hass: HomeAssistant, url: str) -> None:
    """Safely add the card JS to Lovelace resources if not already present."""
    try:
        resources = hass.data.get("lovelace", {}).get("resources")
        if resources is None:
            _LOGGER.debug("Lovelace resources collection not available")
            return

        # Check if any monoprice_enhanced resource already exists
        for item in resources.async_items():
            existing_url = item.get("url", "")
            if DOMAIN in existing_url and CARD_JS in existing_url:
                # Update the URL if version changed, otherwise leave it alone
                if existing_url != url:
                    await resources.async_update_item(
                        item["id"], {"url": url}
                    )
                    _LOGGER.info("Updated Lovelace resource to: %s", url)
                return

        # Not found — add it
        await resources.async_create_item({"res_type": "module", "url": url})
        _LOGGER.info("Registered Lovelace resource: %s", url)
    except Exception:
        _LOGGER.debug("Could not auto-register Lovelace resource", exc_info=True)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Monoprice 6-Zone Amplifier from a config entry."""
    port = entry.data[CONF_PORT]

    try:
        monoprice = await hass.async_add_executor_job(get_monoprice, port)
    except SerialException as err:
        _LOGGER.error("Error connecting to Monoprice controller at %s", port)
        raise ConfigEntryNotReady from err

    # Double negative to handle absence of value
    first_run = not entry.data.get(CONF_NOT_FIRST_RUN)

    undo_listener = entry.add_update_listener(_update_listener)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        MONOPRICE_OBJECT: monoprice,
        UNDO_UPDATE_LISTENER: undo_listener,
        FIRST_RUN: first_run,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
