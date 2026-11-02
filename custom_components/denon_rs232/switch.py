"""Switch entities: power, mute, Cinema EQ, Tone Defeat, PLIIz height, zones."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DenonConfigEntry
from .denon_control import DenonDevice, DenonState
from .entity import DenonEntity


@dataclass(frozen=True, kw_only=True)
class SwitchDef:
    """One switch entity."""

    key: str
    name: str
    is_on: Callable[[DenonState], bool | None]
    turn: Callable[[DenonDevice, bool], Awaitable[None]]
    icon: str | None = None
    enabled: bool = True


def _ps_on(key: str) -> Callable[[DenonState], bool | None]:
    def is_on(st: DenonState) -> bool | None:
        value = st.parameters.get(key)
        return None if value is None else value.upper() == "ON"

    return is_on


async def _power(dev: DenonDevice, on: bool) -> None:
    await (dev.power_on() if on else dev.power_off())


SWITCHES: tuple[SwitchDef, ...] = (
    SwitchDef(key="power", name="Power", icon="mdi:power", is_on=lambda st: st.power, turn=_power),
    SwitchDef(key="mute", name="Mute", icon="mdi:volume-off",
              is_on=lambda st: st.muted, turn=lambda d, on: d.mute(on)),
    SwitchDef(key="cinema_eq", name="Cinema EQ", icon="mdi:movie-open-settings",
              is_on=_ps_on("CINEMA EQ"), turn=lambda d, on: d.set_parameter_on_off("CINEMA EQ", on)),
    SwitchDef(key="tone_defeat", name="Tone defeat", icon="mdi:tune-variant",
              is_on=_ps_on("TONE DEFEAT"), turn=lambda d, on: d.set_parameter_on_off("TONE DEFEAT", on)),
    SwitchDef(key="pliiz_height", name="PLIIz height", enabled=False,
              is_on=_ps_on("FH"), turn=lambda d, on: d.set_parameter_on_off("FH", on)),
    SwitchDef(key="main_zone", name="Main zone", enabled=False,
              is_on=lambda st: st.main_zone, turn=lambda d, on: d.main_zone(on)),
    SwitchDef(key="zone2_power", name="Zone 2", enabled=False,
              is_on=lambda st: st.zones[2].power, turn=lambda d, on: d.zone_power(2, on)),
    SwitchDef(key="zone3_power", name="Zone 3", enabled=False,
              is_on=lambda st: st.zones[3].power, turn=lambda d, on: d.zone_power(3, on)),
    SwitchDef(key="zone4_power", name="Zone 4", enabled=False,
              is_on=lambda st: st.zones[4].power, turn=lambda d, on: d.zone_power(4, on)),
    SwitchDef(key="zone2_mute", name="Zone 2 mute", enabled=False,
              is_on=lambda st: st.zones[2].muted, turn=lambda d, on: d.zone_mute(2, on)),
    SwitchDef(key="zone3_mute", name="Zone 3 mute", enabled=False,
              is_on=lambda st: st.zones[3].muted, turn=lambda d, on: d.zone_mute(3, on)),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DenonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the switches."""
    async_add_entities(DenonSwitch(entry, d) for d in SWITCHES)


class DenonSwitch(DenonEntity, SwitchEntity):
    """On/off protocol parameter."""

    def __init__(self, entry: DenonConfigEntry, definition: SwitchDef) -> None:
        super().__init__(entry, definition.key)
        self._def = definition
        self._attr_name = definition.name
        self._attr_icon = definition.icon
        self._attr_entity_registry_enabled_default = definition.enabled

    @property
    def is_on(self) -> bool | None:
        return self._def.is_on(self.denon)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._def.turn(self.client, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._def.turn(self.client, False)
