"""WebSocket connection manager for real-time progress updates."""

import asyncio
import json
import logging
from typing import Dict, List

from fastapi import WebSocket

logger = logging.getLogger("prezi.ws")

_connections: Dict[str, List[WebSocket]] = {}
_main_loop: asyncio.AbstractEventLoop = None


def set_main_loop(loop: asyncio.AbstractEventLoop):
    """Store the main event loop (called at app startup)."""
    global _main_loop
    _main_loop = loop


def connect(job_id: str, ws: WebSocket):
    """Register a WebSocket connection for a job."""
    if job_id not in _connections:
        _connections[job_id] = []
    _connections[job_id].append(ws)
    logger.info(f"WS connected for job {job_id} (total: {len(_connections[job_id])})")


def disconnect(job_id: str, ws: WebSocket):
    """Remove a WebSocket connection for a job."""
    if job_id in _connections:
        try:
            _connections[job_id].remove(ws)
        except ValueError:
            pass
        if not _connections[job_id]:
            del _connections[job_id]
    logger.info(f"WS disconnected for job {job_id}")


def notify_progress(job_id: str, data: dict):
    """Thread-safe: send progress update to all connected WebSocket clients.

    Called from the worker thread — uses asyncio.run_coroutine_threadsafe()
    to dispatch into the main event loop.
    """
    if _main_loop is None:
        return

    if job_id not in _connections or not _connections[job_id]:
        return

    async def _broadcast():
        message = json.dumps(data)
        stale = []
        for ws in _connections.get(job_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            disconnect(job_id, ws)

    asyncio.run_coroutine_threadsafe(_broadcast(), _main_loop)
