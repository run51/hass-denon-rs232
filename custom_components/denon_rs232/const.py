"""Constants for the Denon RS-232 integration."""

from __future__ import annotations

DOMAIN = "denon_rs232"

CONF_HOST = "host"
CONF_PORT = "port"
DEFAULT_PORT = 5000
DEFAULT_NAME = "Denon"

# Safety refresh while connected (the unit pushes every change on its own).
POLL_INTERVAL_S = 30.0
# Link considered dead after this long without any line from the unit.
STALE_LINK_S = 2 * POLL_INTERVAL_S + 15
# Coalesce bursts of events (MVUP reports old + new value, power-on bursts…).
UPDATE_DEBOUNCE_S = 0.08
# Reconnection backoff.
BACKOFF_MIN_S = 2.0
BACKOFF_MAX_S = 60.0
# Setup validation: time allowed for the unit to answer PW?.
VALIDATE_TIMEOUT_S = 4.0

# Channel trims exposed as number entities, in display order.
# Enabled by default: the channels of a typical 7.2 setup.
# SW3 only exists with the "3SP" subwoofer settings: the unit does not report it otherwise.
MAIN_CHANNELS = ("FL", "C", "FR", "SL", "SR", "SBL", "SBR", "SW1", "SW2")
EXTRA_CHANNELS = ("SW3", "SB", "FHL", "FHR", "FWL", "FWR", "TR")
