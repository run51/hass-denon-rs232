"""Sensor entities: volume, source, surround mode, incoming audio format…"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DenonConfigEntry
from .denon_control import DenonState
from .denon_control.const import INPUT_MODES, SOURCES, decoding_label
from .entity import DenonEntity


def audio_format(surround: str | None) -> str | None:
    """Incoming audio format, deduced from the surround mode reported by the unit.

    The unit names the decoder in its MS reply (e.g. "DOLBY TRUEHD", "DTS HD MSTR",
    "MULTI CH IN", "DSD DIRECT"); stereo and analog sources fall back to "PCM / Analog".
    """
    if not surround:
        return None
    mode = surround.upper()
    if mode.startswith("QUICK"):
        return None
    if "TRUEHD" in mode or mode.startswith("DOLBY HD"):
        fmt = "Dolby TrueHD"
    elif "DOLBY D+" in mode or mode.startswith("DOLBY D +"):
        fmt = "Dolby Digital Plus"
    elif "DOLBY DIGITAL" in mode or mode.startswith("DOLBY D"):
        fmt = "Dolby Digital"
    elif "DTS HD MSTR" in mode or "DTS-HD MSTR" in mode:
        fmt = "DTS-HD Master Audio"
    elif mode.startswith("DTS HD"):
        fmt = "DTS-HD"
    elif mode.startswith("DTS EXPRESS"):
        fmt = "DTS Express"
    elif mode.startswith("DTS") and "NEO" not in mode:
        fmt = "DTS"
    elif mode.startswith("DSD"):
        fmt = "DSD"
    elif "MULTI CH" in mode or mode.startswith("PCM"):
        fmt = "PCM multichannel"
    else:
        fmt = "PCM / Analog"
    return fmt


@dataclass(frozen=True, kw_only=True)
class SensorDef:
    """One sensor entity."""

    key: str
    name: str
    value: Callable[[DenonState], str | float | None]
    icon: str | None = None
    unit: str | None = None
    enabled: bool = True


def _label(table: dict[str, str], code: str | None) -> str | None:
    if not code:
        return None
    return table.get(code, code.title())


SENSORS: tuple[SensorDef, ...] = (
    SensorDef(key="volume_db", name="Volume", icon="mdi:volume-high", unit="dB",
              value=lambda st: st.volume_db),
    SensorDef(key="current_source", name="Current source", icon="mdi:import",
              value=lambda st: _label(SOURCES, st.source)),
    SensorDef(key="current_surround", name="Current surround mode", icon="mdi:surround-sound",
              value=lambda st: decoding_label(st.surround) if st.surround else None),
    SensorDef(key="current_input_mode", name="Current input mode", icon="mdi:video-input-hdmi",
              value=lambda st: _label(INPUT_MODES, st.input_mode)),
    SensorDef(key="audio_format", name="Audio format", icon="mdi:waveform",
              value=lambda st: audio_format(st.surround)),
    SensorDef(key="quick_select", name="Current quick select", icon="mdi:numeric", enabled=False,
              value=lambda st: st.quick_select),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DenonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors."""
    async_add_entities(DenonSensor(entry, d) for d in SENSORS)


class DenonSensor(DenonEntity, SensorEntity):
    """Read-only state of the unit."""

    def __init__(self, entry: DenonConfigEntry, definition: SensorDef) -> None:
        super().__init__(entry, definition.key)
        self._def = definition
        self._attr_name = definition.name
        self._attr_icon = definition.icon
        self._attr_native_unit_of_measurement = definition.unit
        self._attr_entity_registry_enabled_default = definition.enabled
        if definition.unit:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> str | float | None:
        return self._def.value(self.denon)
