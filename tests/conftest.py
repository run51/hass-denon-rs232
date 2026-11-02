"""Shared fixtures: a simulated Denon on a local TCP port."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from denon_simulator import DenonSim

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    return


@pytest.fixture
async def denon_sim(socket_enabled) -> AsyncGenerator[tuple[DenonSim, int]]:
    """Start the simulator on a free port, powered on."""
    sim = DenonSim()
    sim.power = True
    server = await asyncio.start_server(sim.client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    yield sim, port
    for writer in list(sim.clients):
        writer.close()
    server.close()
    await server.wait_closed()
