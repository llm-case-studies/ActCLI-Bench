"""Tests for facilitator client."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from actcli.wrapper.client import FacilitatorClient


@pytest.mark.anyio
async def test_create_session():
    """Test creating a session."""
    client = FacilitatorClient("http://localhost:8765")

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "session_id": "session_123",
            "name": "Test Session",
            "created_at": "2025-10-11T00:00:00Z"
        }
        mock_client.post.return_value = mock_response

        session_id = await client.create_session("Test Session", "Description")

        assert session_id == "session_123"
        assert client.session_id == "session_123"
        mock_client.post.assert_called_once()


@pytest.mark.anyio
async def test_join_session():
    """Test joining a session."""
    client = FacilitatorClient("http://localhost:8765")

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "participant_id": "participant_456",
            "session_id": "session_123"
        }
        mock_client.post.return_value = mock_response

        participant_id = await client.join_session(
            session_id="session_123",
            name="TestBot",
            provider="test"
        )

        assert participant_id == "participant_456"
        assert client.participant_id == "participant_456"
        assert client.session_id == "session_123"
        mock_client.post.assert_called_once()


@pytest.mark.anyio
async def test_websocket_url_conversion():
    """Test that HTTP URLs are converted to WebSocket URLs."""
    client = FacilitatorClient("http://localhost:8765")
    assert client.ws_url == "ws://localhost:8765"

    https_client = FacilitatorClient("https://example.com")
    assert https_client.ws_url == "wss://example.com"


@pytest.mark.anyio
async def test_send_message_requires_connection():
    """Test that sending a message requires a WebSocket connection."""
    client = FacilitatorClient("http://localhost:8765")

    with pytest.raises(ValueError, match="WebSocket not connected"):
        await client.send_message("Hello")


@pytest.mark.anyio
async def test_listen_requires_connection():
    """Test that listening requires a WebSocket connection."""
    client = FacilitatorClient("http://localhost:8765")

    async def callback(data):
        pass

    with pytest.raises(ValueError, match="WebSocket not connected"):
        await client.listen(callback)


@pytest.mark.anyio
async def test_connect_websocket_requires_session():
    """Test that connecting WebSocket requires joining a session."""
    client = FacilitatorClient("http://localhost:8765")

    with pytest.raises(ValueError, match="Must join session"):
        await client.connect_websocket()
