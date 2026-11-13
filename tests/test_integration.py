"""End-to-end tests against the Denon simulator."""

from __future__ import annotations

import asyncio

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.denon_rs232.const import DOMAIN
from custom_components.denon_rs232.sensor import audio_format


async def _wait(predicate, timeout: float = 5.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("condition not met in time")
        await asyncio.sleep(0.05)


async def _setup(hass: HomeAssistant, port: int) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="Denon", data={"host": "127.0.0.1", "port": port}, unique_id=f"127.0.0.1:{port}"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _state(hass: HomeAssistant, entity_id: str) -> str | None:
    st = hass.states.get(entity_id)
    return st.state if st else None


async def test_config_flow_ok(hass: HomeAssistant, denon_sim) -> None:
    _sim, port = denon_sim
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Denon", "host": "127.0.0.1", "port": port}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"host": "127.0.0.1", "port": port}
    await hass.async_block_till_done()


async def test_config_flow_cannot_connect(hass: HomeAssistant, socket_enabled) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Denon", "host": "127.0.0.1", "port": 1}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_entities_and_commands(hass: HomeAssistant, denon_sim) -> None:
    sim, port = denon_sim
    entry = await _setup(hass, port)

    await _wait(lambda: _state(hass, "media_player.denon") == "on")
    await _wait(lambda: "sound_mode" in hass.states.get("media_player.denon").attributes)
    mp = hass.states.get("media_player.denon")
    assert mp.attributes["source"] == "DVD"
    assert mp.attributes["sound_mode"] == "Stereo"
    assert mp.attributes["volume_db"] == -50.0

    # Channel trims come from the CV? query sent at connection
    await _wait(lambda: _state(hass, "number.denon_front_l_trim") == "-9.5")
    assert _state(hass, "number.denon_subwoofer_2_trim") == "0.0"

    # Set a trim
    await hass.services.async_call(
        "number", "set_value", {"entity_id": "number.denon_front_l_trim", "value": -3.5}, blocking=True
    )
    await _wait(lambda: sim.channels["FL"] == "465")
    await _wait(lambda: _state(hass, "number.denon_front_l_trim") == "-3.5")

    # Source through the media player
    await hass.services.async_call(
        "media_player", "select_source", {"entity_id": "media_player.denon", "source": "CD"}, blocking=True
    )
    await _wait(lambda: hass.states.get("media_player.denon").attributes.get("source") == "CD")
    assert _state(hass, "select.denon_source") == "CD"

    # Dynamic volume level enables Dynamic EQ + Volume first (unit rule)
    await hass.services.async_call(
        "select", "select_option", {"entity_id": "select.denon_dynamic_volume", "option": "Midnight"}, blocking=True
    )
    await _wait(lambda: _state(hass, "select.denon_dynamic_volume") == "Midnight")
    assert _state(hass, "select.denon_dynamic_eq") == "Dynamic EQ + Volume"

    # Mute switch + volume sensor
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.denon_mute"}, blocking=True)
    await _wait(lambda: _state(hass, "switch.denon_mute") == "on")
    assert _state(hass, "sensor.denon_volume") == "-50.0"

    # Quick button
    await hass.services.async_call("button", "press", {"entity_id": "button.denon_quick_2"}, blocking=True)
    await _wait(lambda: sim.quick == "QUICK2")

    # Optional entities are registered but disabled by default
    reg = er.async_get(hass)
    assert reg.async_get("number.denon_front_height_l_trim").disabled_by is not None
    assert reg.async_get("select.denon_audyssey_dsx").disabled_by is not None

    # Power off -> media player off
    await hass.services.async_call("media_player", "turn_off", {"entity_id": "media_player.denon"}, blocking=True)
    await _wait(lambda: _state(hass, "media_player.denon") == "off")

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_reconnects_after_link_loss(hass: HomeAssistant, denon_sim) -> None:
    sim, port = denon_sim
    entry = await _setup(hass, port)
    await _wait(lambda: _state(hass, "media_player.denon") == "on")

    for writer in list(sim.clients):
        writer.close()
    await _wait(lambda: _state(hass, "media_player.denon") == "unavailable")
    await _wait(lambda: _state(hass, "media_player.denon") == "on", timeout=10)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def test_audio_format() -> None:
    assert audio_format("DOLBY TRUEHD") == "Dolby TrueHD"
    assert audio_format("DTS HD MSTR") == "DTS-HD Master Audio"
    assert audio_format("DTS SURROUND") == "DTS"
    assert audio_format("DTS NEO:X C") == "PCM / Analog"
    assert audio_format("MULTI CH IN") == "PCM multichannel"
    assert audio_format("STEREO") == "PCM / Analog"
    assert audio_format(None) is None


def test_decoding_names() -> None:
    from custom_components.denon_rs232.denon_control.const import decoding_label

    assert decoding_label("DOLBY HD") == "Dolby TrueHD"
    assert decoding_label("DTS HD MSTR") == "DTS-HD MA"
    assert decoding_label("DOLBY PL2 C") == "Pro Logic II"
    assert decoding_label("STEREO") == "Stereo"
