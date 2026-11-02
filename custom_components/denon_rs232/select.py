"""Select entities: source, surround mode, Audyssey and other PS parameters, zones."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DenonConfigEntry
from .denon_control import DenonDevice, DenonState
from .denon_control.const import (
    DCOMP_MODES,
    DIGITAL_INPUT_MODES,
    DRC_MODES,
    DSX_MODES,
    DYNAMIC_EQ_MODES,
    DYNAMIC_VOLUME_SETTINGS,
    INPUT_MODES,
    PL_MODES,
    PLIIZ_HEIGHT_GAINS,
    QUICK_SELECTS,
    REFERENCE_LEVELS,
    RESTORER_MODES,
    ROOM_EQ_MODES,
    SOURCES,
    SURROUND_MODES,
    ZONE4_SOURCES,
)
from .entity import DenonEntity, code_for

ZONE_SOURCES = {"SOURCE": "Main zone", **SOURCES}
ZONE4_OPTIONS = {"SOURCE": "Main zone", **ZONE4_SOURCES}


@dataclass(frozen=True, kw_only=True)
class SelectDef:
    """One select entity."""

    key: str
    name: str
    options: dict[str, str]  # protocol code -> label
    current: Callable[[DenonState], str | None]
    apply: Callable[[DenonDevice, str], Awaitable[None]]
    icon: str | None = None
    enabled: bool = True


def _ps(key: str) -> tuple[Callable[[DenonState], str | None], Callable[[DenonDevice, str], Awaitable[None]]]:
    return (
        lambda st: st.parameters.get(key),
        lambda dev, code: dev.set_parameter(key, code),
    )


def _quick_current(st: DenonState) -> str | None:
    return st.quick_select


SELECTS: tuple[SelectDef, ...] = (
    SelectDef(key="source", name="Source", options=SOURCES, icon="mdi:import",
              current=lambda st: st.source, apply=lambda d, c: d.select_source(c)),
    SelectDef(key="surround_mode", name="Surround mode", options=SURROUND_MODES, icon="mdi:surround-sound",
              current=lambda st: st.surround, apply=lambda d, c: d.select_surround(c)),
    SelectDef(key="input_mode", name="Input mode", options=INPUT_MODES, icon="mdi:video-input-hdmi",
              current=lambda st: st.input_mode, apply=lambda d, c: d.set_input_mode(c)),
    SelectDef(key="digital_mode", name="Digital input mode", options=DIGITAL_INPUT_MODES, enabled=False,
              current=lambda st: st.digital_mode, apply=lambda d, c: d.set_digital_mode(c)),
    SelectDef(key="quick_select", name="Quick select", options=QUICK_SELECTS, icon="mdi:numeric",
              current=_quick_current, apply=lambda d, c: d.quick_select(int(c[-1]))),
    SelectDef(key="room_eq", name="Room EQ", options=ROOM_EQ_MODES, icon="mdi:equalizer",
              current=_ps("ROOM EQ")[0], apply=_ps("ROOM EQ")[1]),
    SelectDef(key="dynamic_eq", name="Dynamic EQ", options=DYNAMIC_EQ_MODES, icon="mdi:waveform",
              current=_ps("DYN")[0], apply=_ps("DYN")[1]),
    SelectDef(key="dynamic_volume", name="Dynamic volume", options=DYNAMIC_VOLUME_SETTINGS, icon="mdi:volume-vibrate",
              current=_ps("DYNSET")[0], apply=_ps("DYNSET")[1]),
    SelectDef(key="reference_level", name="Reference level", options=REFERENCE_LEVELS,
              current=_ps("REFLEV")[0], apply=_ps("REFLEV")[1]),
    SelectDef(key="dsx", name="Audyssey DSX", options=DSX_MODES, enabled=False,
              current=_ps("DSX")[0], apply=_ps("DSX")[1]),
    SelectDef(key="pliiz_gain", name="PLIIz height gain", options=PLIIZ_HEIGHT_GAINS, enabled=False,
              current=_ps("PHG")[0], apply=_ps("PHG")[1]),
    SelectDef(key="audio_restorer", name="Audio restorer", options=RESTORER_MODES, icon="mdi:music-note-plus",
              current=_ps("RSTR")[0], apply=_ps("RSTR")[1]),
    SelectDef(key="pl_mode", name="PL mode", options=PL_MODES, enabled=False,
              current=_ps("MODE")[0], apply=_ps("MODE")[1]),
    SelectDef(key="drc", name="DRC", options=DRC_MODES, enabled=False,
              current=_ps("DRC")[0], apply=_ps("DRC")[1]),
    SelectDef(key="dcomp", name="D.COMP", options=DCOMP_MODES, enabled=False,
              current=_ps("DCO")[0], apply=_ps("DCO")[1]),
    SelectDef(key="zone2_source", name="Zone 2 source", options=ZONE_SOURCES, enabled=False,
              current=lambda st: st.zones[2].source, apply=lambda d, c: d.zone_source(2, c)),
    SelectDef(key="zone3_source", name="Zone 3 source", options=ZONE_SOURCES, enabled=False,
              current=lambda st: st.zones[3].source, apply=lambda d, c: d.zone_source(3, c)),
    SelectDef(key="zone4_source", name="Zone 4 source", options=ZONE4_OPTIONS, enabled=False,
              current=lambda st: st.zones[4].source, apply=lambda d, c: d.zone_source(4, c)),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DenonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the selects."""
    async_add_entities(DenonSelect(entry, d) for d in SELECTS)


class DenonSelect(DenonEntity, SelectEntity):
    """A protocol table exposed as a select."""

    def __init__(self, entry: DenonConfigEntry, definition: SelectDef) -> None:
        super().__init__(entry, definition.key)
        self._def = definition
        self._attr_name = definition.name
        self._attr_icon = definition.icon
        self._attr_options = list(definition.options.values())
        self._attr_entity_registry_enabled_default = definition.enabled

    @property
    def current_option(self) -> str | None:
        code = self._def.current(self.denon)
        if not code:
            return None
        label = self._def.options.get(code.upper()) or self._def.options.get(code)
        return label  # unknown codes (e.g. new surround modes) -> None

    async def async_select_option(self, option: str) -> None:
        code = code_for(option, self._def.options)
        if code is None:
            raise ValueError(f"Unknown option for {self._def.key}: {option}")
        await self._def.apply(self.client, code)
