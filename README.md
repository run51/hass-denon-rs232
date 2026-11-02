# Denon AV receivers & processors (RS-232) — Home Assistant integration

Controls Denon AV receivers and processors from Home Assistant through their **RS-232
port** and a serial-to-IP bridge — typically the **Unfolded Circle Dock 3** (external
port 2, TCP 5000), but also Global Caché IP2SL/iTach, USR-TCP232, ser2net…

Built and tested with the RS-232 commands of the **Denon AVP-A1HD** (with the 2011
"3D upgrade"). It works with other Denon units of the same generation that use the same
ASCII protocol (AVC-A1HD, AVR-3808CI / 4308CI / 5308CI…) — see the compatibility table of
the sister project [uc-integration-denon-rs232](https://github.com/run51/uc-integration-denon-rs232).

- **Local push**: the unit reports every change by itself; Home Assistant is updated in
  real time (one safety refresh every 30 s).
- **Shares the bridge with the Unfolded Circle Remote**: the Dock 3 accepts several TCP
  clients at once and forwards the unit's replies to all of them, so this integration and
  the [Remote 3 integration](https://github.com/run51/uc-integration-denon-rs232) can run
  side by side.

## Entities

| Type | Entities |
|---|---|
| Media player | Power, volume, mute, source, sound mode |
| Number | Master volume (dB); **channel level trims** −12…+12 dB: FL, C, FR, SL, SR, SBL, SBR, SW1, SW2, SW3 (SB, front height/wide and transducer available, disabled by default) |
| Select | Source, surround mode, input mode, quick select, Room EQ, Dynamic EQ, Dynamic Volume, Reference Level, audio restorer (+ DSX, PLIIz gain, PL mode, DRC, D.COMP, zone sources, disabled by default) |
| Switch | Power, mute, Cinema EQ, Tone Defeat (+ PLIIz height, main zone, zones 2/3/4, disabled by default) |
| Button | Volume up / down, Quick 1 / 2 / 3 |
| Sensor | Volume (dB), current source, surround mode, input mode, audio format (Dolby TrueHD, DTS-HD MA, PCM…) |

Choosing a Dynamic Volume level (Day / Evening / Midnight) switches Dynamic EQ to
"Dynamic EQ + Volume" first: the unit ignores the level otherwise.

## Installation

### HACS

1. HACS → ⋮ → *Custom repositories* → add `https://github.com/run51/hass-denon-rs232`,
   category *Integration*.
2. Install *Denon AV receivers & processors (RS-232)*, then restart Home Assistant.
3. Settings → Devices & services → *Add integration* → *Denon AV receivers & processors
   (RS-232)*.

### Manual

Copy `custom_components/denon_rs232` into your Home Assistant `config/custom_components/`
folder and restart.

## Setup

- **Bridge IP address**: the address of the dock / bridge (not of the Denon).
- **TCP port**: `5000` for the Dock 3 (external port 2).

The setup checks that the Denon answers `PW?` before saving.

Hardware notes (cable pinout, dock settings) are in the
[Remote 3 integration README](https://github.com/run51/uc-integration-denon-rs232#hardware).

## Development

```bash
uv venv -p 3.13 .venv
uv pip install -p .venv/bin/python pytest-homeassistant-custom-component
.venv/bin/python -m pytest
```

The tests run the integration against `tests/denon_simulator.py`, a fake Denon over TCP.
The protocol library (`custom_components/denon_rs232/denon_control`) is shared with the
Remote 3 integration.

License: MPL-2.0.
