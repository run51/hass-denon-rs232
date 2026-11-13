# Changelog

## v0.1.1

Protocol library aligned with the Remote 3 integration v0.1.12.

- A link that stays silent for more than 75 s (half-open TCP connection, bridge rebooted…)
  is detected and rebuilt: the unit always answers the 30 s `PW?` poll.
- Writes to the bridge time out after 5 s instead of waiting forever.
- Short names for what the unit reports it decodes, in the surround mode sensor and the
  media player sound mode: "Dolby TrueHD" instead of "DOLBY HD", "DTS-HD MA" instead of
  "DTS HD MSTR", "Pro Logic II" instead of "DOLBY PL2 C"…

## v0.1.0

- First version, tested on a Denon AVP-A1HD (3D upgrade) through an Unfolded Circle Dock 3.
- Media player, master volume and channel level trims (numbers), selects (source, surround,
  Room EQ, Dynamic EQ / Volume, Reference Level…), switches, Volume / Quick buttons,
  sensors including the incoming audio format.
- Local push with automatic reconnection; shares the bridge with the Unfolded Circle Remote.
