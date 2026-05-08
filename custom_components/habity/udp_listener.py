"""Async UDP listener for Habity broadcasts."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Callable

from homeassistant.core import HomeAssistant

from .const import DOMAIN, UDP_DEDUP_WINDOW_MS, UDP_PORT

_LOGGER = logging.getLogger(__name__)

# HA event fired for automation triggers
HA_EVENT_UDP = f"{DOMAIN}_udp_event"


class HabityUDPListener(asyncio.DatagramProtocol):
    """Listens on UDP port 12345, deduplicates, and fires HA events.

    The callback receives (packet, addr) so callers can route by source IP.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        callback: Callable[[dict, tuple], None],
    ) -> None:
        self.hass = hass
        self._callback = callback
        self._transport: asyncio.BaseTransport | None = None
        self._seen: dict[tuple[str, str, str], float] = {}

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._transport = transport
        _LOGGER.debug("Habity UDP listener bound to port %s", UDP_PORT)

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        try:
            packet = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            _LOGGER.warning("Received invalid UDP packet from %s: %s", addr, data)
            return

        event_type = packet.get("type")
        state = packet.get("state")

        if not event_type or not state:
            _LOGGER.warning("Malformed UDP packet: %s", packet)
            return

        now_ms = time.monotonic() * 1000
        # Include source IP in dedup key so two devices sending the same
        # event type+state are not incorrectly collapsed into one.
        source_ip = addr[0]
        key = (source_ip, event_type, state)
        last_seen = self._seen.get(key, 0)

        if now_ms - last_seen < UDP_DEDUP_WINDOW_MS:
            _LOGGER.debug("Deduplicated UDP packet: %s", packet)
            return

        self._seen[key] = now_ms
        _LOGGER.debug("UDP event from %s: %s", addr, packet)
        self._callback(packet, addr)

    def error_received(self, exc: Exception) -> None:
        _LOGGER.error("Habity UDP listener error: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        _LOGGER.debug("Habity UDP listener connection lost: %s", exc)


async def async_start_udp_listener(
    hass: HomeAssistant,
    callback: Callable[[dict, tuple], None],
) -> Callable:
    """Start the shared UDP listener and return a stop function.

    Should be called only once per HA instance (guarded in __init__.py).
    """
    loop = asyncio.get_event_loop()

    transport, _ = await loop.create_datagram_endpoint(
        lambda: HabityUDPListener(hass, callback),
        local_addr=("0.0.0.0", UDP_PORT),
    )

    def stop() -> None:
        transport.close()
        _LOGGER.debug("Habity UDP listener stopped")

    return stop