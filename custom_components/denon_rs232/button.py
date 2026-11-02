"""Button entities: volume steps and Quick Select recall."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DenonConfigEntry
from .denon_control import DenonDevice
from .entity import DenonEntity


@dataclass(frozen=True, kw_only=True)
class ButtonDef:
    """One button entity."""

    key: str
    name: str
    press: Callable[[DenonDevice], Awaitable[None]]
    icon: str | None = None


BUTTONS: tuple[ButtonDef, ...] = (
    ButtonDef(key="volume_up", name="Volume up", icon="mdi:volume-plus", press=lambda d: d.volume_up()),
    ButtonDef(key="volume_down", name="Volume down", icon="mdi:volume-minus", press=lambda d: d.volume_down()),
    ButtonDef(key="quick_1", name="Quick 1", icon="mdi:numeric-1-box", press=lambda d: d.quick_select(1)),
    ButtonDef(key="quick_2", name="Quick 2", icon="mdi:numeric-2-box", press=lambda d: d.quick_select(2)),
    ButtonDef(key="quick_3", name="Quick 3", icon="mdi:numeric-3-box", press=lambda d: d.quick_select(3)),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DenonConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the buttons."""
    async_add_entities(DenonButton(entry, d) for d in BUTTONS)


class DenonButton(DenonEntity, ButtonEntity):
    """Momentary command."""

    def __init__(self, entry: DenonConfigEntry, definition: ButtonDef) -> None:
        super().__init__(entry, definition.key)
        self._def = definition
        self._attr_name = definition.name
        self._attr_icon = definition.icon

    async def async_press(self) -> None:
        await self._def.press(self.client)
