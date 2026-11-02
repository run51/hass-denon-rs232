"""Denon AV receivers & processors over RS-232 (through a serial-to-IP bridge)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PORT
from .hub import DenonHub

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

type DenonConfigEntry = ConfigEntry[DenonHub]


async def async_setup_entry(hass: HomeAssistant, entry: DenonConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    hub = DenonHub(hass, entry.data[CONF_HOST], entry.data[CONF_PORT])
    entry.runtime_data = hub
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hub.start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DenonConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.stop()
    return unloaded
