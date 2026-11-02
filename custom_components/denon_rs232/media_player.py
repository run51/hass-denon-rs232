"""Media player: power, volume, mute, source, sound mode."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DenonConfigEntry
from .denon_control.const import SOURCES, SURROUND_MODES, VOLUME_MIN_DB
from .entity import DenonEntity, code_for

# Volume span used for the 0..1 volume level: -80 dB .. +18 dB.
_VOLUME_SPAN_DB = 98.0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DenonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the media player."""
    async_add_entities([DenonMediaPlayer(entry)])


class DenonMediaPlayer(DenonEntity, MediaPlayerEntity):
    """Main zone of the unit."""

    _attr_name = None  # use the device name
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )
    _attr_source_list = list(SOURCES.values())
    _attr_sound_mode_list = list(SURROUND_MODES.values())

    def __init__(self, entry: DenonConfigEntry) -> None:
        super().__init__(entry, "media_player")

    @property
    def state(self) -> MediaPlayerState | None:
        power = self.denon.power
        if power is None:
            return None
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        db = self.denon.volume_db
        if db is None:
            return None
        return max(0.0, min(1.0, (db - VOLUME_MIN_DB) / _VOLUME_SPAN_DB))

    @property
    def is_volume_muted(self) -> bool | None:
        return self.denon.muted

    @property
    def source(self) -> str | None:
        code = self.denon.source
        return SOURCES.get(code, code) if code else None

    @property
    def sound_mode(self) -> str | None:
        code = self.denon.surround
        return SURROUND_MODES.get(code, code.title()) if code else None

    @property
    def extra_state_attributes(self) -> dict[str, float | str | None]:
        return {
            "volume_db": self.denon.volume_db,
            "sound_mode_raw": self.denon.surround,
        }

    async def async_turn_on(self) -> None:
        await self.client.power_on()

    async def async_turn_off(self) -> None:
        await self.client.power_off()

    async def async_volume_up(self) -> None:
        await self.client.volume_up()

    async def async_volume_down(self) -> None:
        await self.client.volume_down()

    async def async_set_volume_level(self, volume: float) -> None:
        db = VOLUME_MIN_DB + volume * _VOLUME_SPAN_DB
        await self.client.set_volume_db(round(db * 2) / 2)

    async def async_mute_volume(self, mute: bool) -> None:
        await self.client.mute(mute)

    async def async_select_source(self, source: str) -> None:
        code = code_for(source, SOURCES)
        if code is None:
            raise ValueError(f"Unknown source: {source}")
        await self.client.select_source(code)

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        code = code_for(sound_mode, SURROUND_MODES)
        if code is None:
            raise ValueError(f"Unknown sound mode: {sound_mode}")
        await self.client.select_surround(code)
