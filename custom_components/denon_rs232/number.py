"""Number entities: master volume in dB and channel level trims."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DenonConfigEntry
from .const import EXTRA_CHANNELS, MAIN_CHANNELS
from .denon_control.const import CHANNEL_NAMES, VOLUME_MIN_DB
from .entity import DenonEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DenonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add master volume and channel trims."""
    entities: list[NumberEntity] = [DenonMasterVolume(entry)]
    entities += [DenonChannelTrim(entry, ch, enabled=True) for ch in MAIN_CHANNELS]
    entities += [DenonChannelTrim(entry, ch, enabled=False) for ch in EXTRA_CHANNELS]
    async_add_entities(entities)


class DenonMasterVolume(DenonEntity, NumberEntity):
    """Master volume in dB (-80 .. +18, 0.5 dB steps)."""

    _attr_name = "Master volume"
    _attr_icon = "mdi:volume-high"
    _attr_native_unit_of_measurement = "dB"
    _attr_native_min_value = VOLUME_MIN_DB
    _attr_native_max_value = 18.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: DenonConfigEntry) -> None:
        super().__init__(entry, "master_volume")

    @property
    def native_value(self) -> float | None:
        return self.denon.volume_db

    async def async_set_native_value(self, value: float) -> None:
        await self.client.set_volume_db(value)


class DenonChannelTrim(DenonEntity, NumberEntity):
    """Channel level (CV), -12 .. +12 dB in 0.5 dB steps."""

    _attr_icon = "mdi:tune-vertical"
    _attr_native_unit_of_measurement = "dB"
    _attr_native_min_value = -12.0
    _attr_native_max_value = 12.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: DenonConfigEntry, channel: str, *, enabled: bool) -> None:
        super().__init__(entry, f"trim_{channel.lower()}")
        self._channel = channel
        self._attr_name = f"{CHANNEL_NAMES.get(channel, channel)} trim"
        self._attr_entity_registry_enabled_default = enabled

    @property
    def native_value(self) -> float | None:
        return self.denon.channel_levels.get(self._channel)

    async def async_set_native_value(self, value: float) -> None:
        await self.client.set_channel_level_db(self._channel, value)
