"""Base entity: device info, availability, push updates from the hub."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import DenonConfigEntry
from .const import DOMAIN
from .denon_control import DenonDevice, DenonState
from .hub import DenonHub


class DenonEntity(Entity):
    """Common behaviour of every Denon entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: DenonConfigEntry, key: str) -> None:
        self._entry = entry
        self._hub: DenonHub = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Denon",
            model="AV receiver / processor (RS-232)",
        )

    @property
    def client(self) -> DenonDevice:
        """Protocol client."""
        return self._hub.client

    @property
    def denon(self) -> DenonState:
        """Raw protocol state."""
        return self._hub.state

    @property
    def available(self) -> bool:
        """Available while the bridge link is up and the unit has answered."""
        return self._hub.connected and self.denon.power is not None

    async def async_added_to_hass(self) -> None:
        """Subscribe to hub updates."""
        self.async_on_remove(self._hub.add_listener(self.async_write_ha_state))


def code_for(option: str | None, options: dict[str, str]) -> str | None:
    """Protocol code for a label (or a code), case-insensitive."""
    if option is None:
        return None
    wanted = option.strip().casefold()
    for code, label in options.items():
        if wanted in (label.casefold(), code.casefold()):
            return code
    return None
