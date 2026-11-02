"""Connection manager: keeps the TCP link to the serial bridge alive."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

from .const import (
    BACKOFF_MAX_S,
    BACKOFF_MIN_S,
    POLL_INTERVAL_S,
    UPDATE_DEBOUNCE_S,
    VALIDATE_TIMEOUT_S,
)
from .denon_control import DenonDevice, DenonEvent, DenonState

_LOG = logging.getLogger(__name__)


class DenonHub:
    """Owns the DenonDevice, reconnects with backoff, notifies entities."""

    def __init__(self, hass: HomeAssistant, host: str, port: int) -> None:
        self.hass = hass
        self.client = DenonDevice(host, port)
        self._callbacks: set[Callable[[], None]] = set()
        self._task: asyncio.Task | None = None
        self._flush_handle: asyncio.TimerHandle | None = None
        self._stopping = False
        self.client.add_listener(self._on_event)

    # ---------------------------------------------------------------- state

    @property
    def state(self) -> DenonState:
        """Raw protocol state."""
        return self.client.state

    @property
    def connected(self) -> bool:
        """True while the TCP link to the bridge is up."""
        return self.client.is_connected

    # ------------------------------------------------------------ lifecycle

    def start(self) -> None:
        """Start the connection loop."""
        self._stopping = False
        self._task = self.hass.async_create_background_task(
            self._run(), name=f"denon_rs232 {self.client.host}:{self.client.port}"
        )

    async def stop(self) -> None:
        """Stop the loop and close the link."""
        self._stopping = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self.client.disconnect()

    async def _run(self) -> None:
        backoff = BACKOFF_MIN_S
        while not self._stopping:
            try:
                await self.client.connect()
                _LOG.info("Connected to %s:%s", self.client.host, self.client.port)
                backoff = BACKOFF_MIN_S
                self._schedule_update(immediate=True)
                await self.client.query_status(full=True)
                while self.client.is_connected:
                    try:
                        await asyncio.wait_for(self.client.wait_closed(), timeout=POLL_INTERVAL_S)
                    except TimeoutError:
                        await self.client.query_status()
            except asyncio.CancelledError:
                raise
            except Exception as err:  # noqa: BLE001 - keep the loop alive whatever happens
                _LOG.warning("Link to %s:%s lost: %s", self.client.host, self.client.port, err)
            finally:
                if not self._stopping:
                    await self.client.disconnect()
                    self._schedule_update(immediate=True)
            if self._stopping:
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, BACKOFF_MAX_S)

    # ------------------------------------------------------------ listeners

    @callback
    def add_listener(self, update: Callable[[], None]) -> CALLBACK_TYPE:
        """Register an entity refresh callback."""
        self._callbacks.add(update)

        @callback
        def remove() -> None:
            self._callbacks.discard(update)

        return remove

    def _on_event(self, _state: DenonState, _event: DenonEvent) -> None:
        self._schedule_update()

    @callback
    def _schedule_update(self, immediate: bool = False) -> None:
        if immediate:
            self._flush()
            return
        if self._flush_handle is None:
            self._flush_handle = self.hass.loop.call_later(UPDATE_DEBOUNCE_S, self._flush)

    @callback
    def _flush(self) -> None:
        if self._flush_handle is not None:
            self._flush_handle.cancel()
            self._flush_handle = None
        for update in list(self._callbacks):
            update()


async def async_validate(host: str, port: int) -> str | None:
    """Connect once and check that the unit answers PW?.

    Returns None on success, else an error key: "cannot_connect" (bridge not
    reachable) or "no_response" (bridge reachable, the Denon does not answer).
    """
    client = DenonDevice(host, port)
    answered = asyncio.Event()

    def on_event(state: DenonState, _event: DenonEvent) -> None:
        if state.power is not None:
            answered.set()

    client.add_listener(on_event)
    try:
        try:
            await asyncio.wait_for(client.connect(), timeout=VALIDATE_TIMEOUT_S)
        except (OSError, ConnectionError, TimeoutError):
            return "cannot_connect"
        await client.send_raw("PW?")
        try:
            await asyncio.wait_for(answered.wait(), timeout=VALIDATE_TIMEOUT_S)
        except TimeoutError:
            return "no_response"
        return None
    finally:
        await client.disconnect()
