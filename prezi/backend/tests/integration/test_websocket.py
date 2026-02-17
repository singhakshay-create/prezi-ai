"""Integration tests for WebSocket endpoint."""

import pytest
import httpx
from app.main import app


class TestWebSocketEndpoint:
    async def test_ws_endpoint_exists(self, test_client):
        """The /ws/progress/{job_id} route is registered on the app."""
        # Verify the websocket route is registered
        routes = [r.path for r in app.routes]
        assert "/ws/progress/{job_id}" in routes

    async def test_ws_not_accessible_via_http(self, test_client):
        """A plain HTTP GET to /ws/progress/{job_id} is not a valid HTTP route."""
        resp = await test_client.get("/ws/progress/test-job")
        # WebSocket routes are not accessible via plain HTTP
        assert resp.status_code in (403, 404)
