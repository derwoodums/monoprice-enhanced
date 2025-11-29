"""Support for interfacing with Monoprice 6 zone home audio controller."""

import logging

from serial import SerialException

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_SOURCES,
    DOMAIN,
    FIRST_RUN,
    MONOPRICE_OBJECT,
    SERVICE_RESTORE,
    SERVICE_SNAPSHOT,
    ZONES,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1

SUPPORT_MONOPRICE = (
    MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOURCE
)

MAX_VOLUME = 38

SOURCES = {
    1: "Source 1",
    2: "Source 2",
    3: "Source 3",
    4: "Source 4",
    5: "Source 5",
    6: "Source 6",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Monoprice media player platform."""
    port = config_entry.data[CONF_PORT]
    monoprice = hass.data[DOMAIN][config_entry.entry_id][MONOPRICE_OBJECT]
    sources = config_entry.options.get(CONF_SOURCES, SOURCES)

    # Convert string keys to int if needed
    if sources:
        sources = {int(k): v for k, v in sources.items()}

    entities = []
    for zone_id, zone_name in ZONES.items():
        # Check if zone responds (handles case where second amp isn't connected)
        try:
            status = await hass.async_add_executor_job(
                monoprice.zone_status, zone_id
            )
            if status is None:
                _LOGGER.debug("Zone %s not responding, skipping", zone_id)
                continue
        except SerialException:
            _LOGGER.debug("Zone %s not available, skipping", zone_id)
            continue

        _LOGGER.debug("Adding zone %s: %s", zone_id, zone_name)
        entities.append(
            MonopriceZone(
                monoprice,
                sources,
                config_entry.entry_id,
                zone_id,
                zone_name,
            )
        )

    async_add_entities(entities, True)

    # Register services
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(
        SERVICE_SNAPSHOT,
        {},
        "snapshot",
    )

    platform.async_register_entity_service(
        SERVICE_RESTORE,
        {},
        "restore",
    )


class MonopriceZone(MediaPlayerEntity):
    """Representation of a Monoprice zone."""

    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = SUPPORT_MONOPRICE
    _attr_has_entity_name = True

    def __init__(
        self,
        monoprice,
        sources,
        entry_id,
        zone_id,
        zone_name,
    ):
        """Initialize new zone."""
        self._monoprice = monoprice
        self._sources = sources
        self._zone_id = zone_id
        self._zone_name = zone_name
        self._entry_id = entry_id

        self._attr_unique_id = f"{entry_id}_{zone_id}"
        self._attr_name = zone_name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{zone_id}")},
            name=f"Monoprice {zone_name}",
            manufacturer="Monoprice",
            model="6-Zone Amplifier",
        )

        self._snapshot = None
        self._state = None
        self._volume = None
        self._muted = None
        self._source = None

    def update(self) -> None:
        """Retrieve latest state."""
        try:
            state = self._monoprice.zone_status(self._zone_id)
        except SerialException:
            _LOGGER.warning("Could not update zone %s", self._zone_id)
            return

        if not state:
            return

        self._state = MediaPlayerState.ON if state.power else MediaPlayerState.OFF
        self._volume = state.volume
        self._muted = state.mute
        self._source = state.source

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the zone."""
        return self._state

    @property
    def volume_level(self) -> float | None:
        """Return the volume level."""
        if self._volume is None:
            return None
        return self._volume / MAX_VOLUME

    @property
    def is_volume_muted(self) -> bool | None:
        """Return whether volume is muted."""
        return self._muted

    @property
    def source(self) -> str | None:
        """Return the current source."""
        if self._source is None:
            return None
        return self._sources.get(self._source, f"Source {self._source}")

    @property
    def source_list(self) -> list[str]:
        """Return a list of available sources."""
        return list(self._sources.values())

    def set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        self._monoprice.set_volume(self._zone_id, int(volume * MAX_VOLUME))

    def volume_up(self) -> None:
        """Volume up the media player."""
        if self._volume is None:
            return
        self._monoprice.set_volume(self._zone_id, min(self._volume + 1, MAX_VOLUME))

    def volume_down(self) -> None:
        """Volume down the media player."""
        if self._volume is None:
            return
        self._monoprice.set_volume(self._zone_id, max(self._volume - 1, 0))

    def mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) the media player."""
        self._monoprice.set_mute(self._zone_id, mute)

    def turn_on(self) -> None:
        """Turn the media player on."""
        self._monoprice.set_power(self._zone_id, True)

    def turn_off(self) -> None:
        """Turn the media player off."""
        self._monoprice.set_power(self._zone_id, False)

    def select_source(self, source: str) -> None:
        """Select input source."""
        for source_id, source_name in self._sources.items():
            if source_name == source:
                self._monoprice.set_source(self._zone_id, source_id)
                return

    def snapshot(self) -> None:
        """Save the current state of the zone."""
        self._snapshot = self._monoprice.zone_status(self._zone_id)

    def restore(self) -> None:
        """Restore the saved state of the zone."""
        if self._snapshot:
            self._monoprice.restore_zone(self._snapshot)
