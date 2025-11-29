"""Number entities for Monoprice 6-Zone Amplifier tone controls."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from serial import SerialException

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BALANCE_MAX,
    BALANCE_MIN,
    BASS_MAX,
    BASS_MIN,
    DOMAIN,
    MONOPRICE_OBJECT,
    NUMBER_BALANCE,
    NUMBER_BASS,
    NUMBER_TREBLE,
    TREBLE_MAX,
    TREBLE_MIN,
    ZONES,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1


@dataclass(frozen=True)
class MonopriceNumberEntityDescription(NumberEntityDescription):
    """Describes a Monoprice number entity."""

    get_value: Callable | None = None
    set_value: Callable | None = None


NUMBER_DESCRIPTIONS: tuple[MonopriceNumberEntityDescription, ...] = (
    MonopriceNumberEntityDescription(
        key=NUMBER_TREBLE,
        name="Treble",
        icon="mdi:music-clef-treble",
        native_min_value=TREBLE_MIN,
        native_max_value=TREBLE_MAX,
        native_step=1,
        mode=NumberMode.SLIDER,
        get_value=lambda status: status.treble,
        set_value=lambda monoprice, zone, value: monoprice.set_treble(zone, int(value)),
    ),
    MonopriceNumberEntityDescription(
        key=NUMBER_BASS,
        name="Bass",
        icon="mdi:music-clef-bass",
        native_min_value=BASS_MIN,
        native_max_value=BASS_MAX,
        native_step=1,
        mode=NumberMode.SLIDER,
        get_value=lambda status: status.bass,
        set_value=lambda monoprice, zone, value: monoprice.set_bass(zone, int(value)),
    ),
    MonopriceNumberEntityDescription(
        key=NUMBER_BALANCE,
        name="Balance",
        icon="mdi:arrow-left-right",
        native_min_value=BALANCE_MIN,
        native_max_value=BALANCE_MAX,
        native_step=1,
        mode=NumberMode.SLIDER,
        get_value=lambda status: status.balance,
        set_value=lambda monoprice, zone, value: monoprice.set_balance(zone, int(value)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Monoprice number entities from a config entry."""
    monoprice = hass.data[DOMAIN][config_entry.entry_id][MONOPRICE_OBJECT]

    entities: list[MonopriceNumber] = []

    for zone_id, zone_name in ZONES.items():
        # Check if zone responds (handles case where second amp isn't connected)
        try:
            status = await hass.async_add_executor_job(
                monoprice.zone_status, zone_id
            )
            if status is None:
                _LOGGER.debug("Zone %s not responding, skipping number entities", zone_id)
                continue
        except SerialException:
            _LOGGER.debug("Zone %s not available, skipping number entities", zone_id)
            continue

        for description in NUMBER_DESCRIPTIONS:
            entities.append(
                MonopriceNumber(
                    monoprice=monoprice,
                    entry_id=config_entry.entry_id,
                    zone_id=zone_id,
                    zone_name=zone_name,
                    description=description,
                )
            )

    async_add_entities(entities, True)


class MonopriceNumber(NumberEntity):
    """Representation of a Monoprice tone control."""

    entity_description: MonopriceNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        monoprice,
        entry_id: str,
        zone_id: int,
        zone_name: str,
        description: MonopriceNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        self._monoprice = monoprice
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._entry_id = entry_id
        self.entity_description = description

        self._attr_unique_id = f"{entry_id}_{zone_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{zone_id}")},
            name=f"Monoprice {zone_name}",
            manufacturer="Monoprice",
            model="6-Zone Amplifier",
        )

        self._attr_native_value: float | None = None

    def update(self) -> None:
        """Fetch the latest state from the device."""
        try:
            status = self._monoprice.zone_status(self._zone_id)
        except SerialException:
            _LOGGER.warning(
                "Could not update %s for zone %s",
                self.entity_description.key,
                self._zone_id,
            )
            return

        if status and self.entity_description.get_value:
            self._attr_native_value = self.entity_description.get_value(status)

    def set_native_value(self, value: float) -> None:
        """Set the value."""
        if self.entity_description.set_value:
            try:
                self.entity_description.set_value(
                    self._monoprice, self._zone_id, value
                )
                self._attr_native_value = value
            except SerialException:
                _LOGGER.error(
                    "Could not set %s for zone %s to %s",
                    self.entity_description.key,
                    self._zone_id,
                    value,
                )
