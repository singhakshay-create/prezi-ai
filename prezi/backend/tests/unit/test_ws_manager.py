"""Unit tests for WebSocket connection manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.ws.manager import (
    connect,
    disconnect,
    notify_progress,
    set_main_loop,
    _connections,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Reset module-level state before each test."""
    _connections.clear()
    set_main_loop(None)
    yield
    _connections.clear()
    set_main_loop(None)


class TestConnectDisconnect:
    def test_connect_adds_ws(self):
        ws = MagicMock()
        connect("job-1", ws)
        assert "job-1" in _connections
        assert ws in _connections["job-1"]

    def test_disconnect_removes_ws(self):
        ws = MagicMock()
        connect("job-1", ws)
        disconnect("job-1", ws)
        assert "job-1" not in _connections

    def test_disconnect_nonexistent_no_error(self):
        ws = MagicMock()
        disconnect("nonexistent", ws)  # Should not raise

    def test_multiple_connections(self):
        ws1 = MagicMock()
        ws2 = MagicMock()
        connect("job-1", ws1)
        connect("job-1", ws2)
        assert len(_connections["job-1"]) == 2
        disconnect("job-1", ws1)
        assert len(_connections["job-1"]) == 1
        assert ws2 in _connections["job-1"]


class TestNotifyProgress:
    def test_notify_no_loop_is_noop(self):
        """notify_progress with no event loop should not raise."""
        ws = MagicMock()
        connect("job-1", ws)
        notify_progress("job-1", {"status": "slides"})
        # No error → pass

    def test_notify_no_connections_is_noop(self):
        """notify_progress with no connections for job should not raise."""
        loop = MagicMock()
        set_main_loop(loop)
        notify_progress("nonexistent-job", {"status": "slides"})
        loop.assert_not_called()

    def test_notify_with_connections_and_loop(self):
        """notify_progress with loop and connections does not raise."""
        import asyncio
        from unittest.mock import patch

        ws = MagicMock()
        connect("job-1", ws)

        loop = MagicMock()
        set_main_loop(loop)

        with patch("app.ws.manager.asyncio.run_coroutine_threadsafe") as mock_rcts:
            notify_progress("job-1", {"status": "slides", "progress": 65})
            mock_rcts.assert_called_once()
            # Verify the coroutine was scheduled on our loop
            assert mock_rcts.call_args[0][1] is loop
