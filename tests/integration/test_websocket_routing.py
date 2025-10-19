"""Integration test for WebSocket message routing."""

import pytest
import asyncio
import websockets
import json
from contextlib import asynccontextmanager

from actcli.facilitator.service import create_app
from actcli.wrapper.client import FacilitatorClient


@pytest.fixture
async def running_server():
    """Start the facilitator server in the background."""
    import uvicorn
    from threading import Thread

    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=8766, log_level="error")
    server = uvicorn.Server(config)

    # Run server in background thread
    thread = Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to start
    await asyncio.sleep(0.5)

    yield "http://127.0.0.1:8766"

    # Cleanup
    server.should_exit = True


@pytest.mark.anyio
async def test_websocket_message_routing_full_flow(running_server):
    """Test complete message routing between two participants via WebSocket."""
    base_url = running_server

    # Create two clients
    client1 = FacilitatorClient(base_url)
    client2 = FacilitatorClient(base_url)

    # Client 1 creates session
    session_id = await client1.create_session("Test Session", "Integration test")
    assert session_id is not None
    print(f"Created session: {session_id}")

    # Both join the session
    p1_id = await client1.join_session(session_id, "Alice", provider="test")
    p2_id = await client2.join_session(session_id, "Bob", provider="test")
    print(f"Alice joined: {p1_id}")
    print(f"Bob joined: {p2_id}")

    # Connect WebSockets
    await client1.connect_websocket()
    await client2.connect_websocket()
    print("WebSockets connected")

    # Track received messages
    alice_received = []
    bob_received = []

    async def alice_listener(data):
        print(f"Alice received: {data}")
        alice_received.append(data)

    async def bob_listener(data):
        print(f"Bob received: {data}")
        bob_received.append(data)

    # Start listening (in background tasks)
    alice_task = asyncio.create_task(client1.listen(alice_listener))
    bob_task = asyncio.create_task(client2.listen(bob_listener))

    # Give listeners time to start
    await asyncio.sleep(0.1)

    # Alice sends a message
    print("Alice sending message...")
    await client1.send_message("Hello Bob!", to="all", msg_type="chat")

    # Wait for message delivery
    await asyncio.sleep(0.5)

    # Bob should have received it
    print(f"Bob received messages: {bob_received}")
    assert len(bob_received) >= 1, f"Bob should receive message, got: {bob_received}"
    assert bob_received[0]["content"] == "Hello Bob!"
    assert bob_received[0]["from_name"] == "Alice"

    # Bob sends a reply
    print("Bob sending reply...")
    await client2.send_message("Hi Alice!", to="all", msg_type="chat")

    # Wait for message delivery
    await asyncio.sleep(0.5)

    # Alice should have received it
    print(f"Alice received messages: {alice_received}")
    assert len(alice_received) >= 1, f"Alice should receive message, got: {alice_received}"
    assert alice_received[0]["content"] == "Hi Alice!"
    assert alice_received[0]["from_name"] == "Bob"

    # Cleanup
    alice_task.cancel()
    bob_task.cancel()
    await client1.close()
    await client2.close()

    print("Test completed successfully!")


@pytest.mark.anyio
async def test_message_not_echoed_to_sender(running_server):
    """Test that sender doesn't receive their own messages."""
    base_url = running_server

    client = FacilitatorClient(base_url)

    # Create and join session
    session_id = await client.create_session("Echo Test", "Test")
    await client.join_session(session_id, "TestUser", provider="test")
    await client.connect_websocket()

    received = []

    async def listener(data):
        received.append(data)

    # Start listening
    listen_task = asyncio.create_task(client.listen(listener))
    await asyncio.sleep(0.1)

    # Send a message
    await client.send_message("My own message", to="all", msg_type="chat")

    # Wait a bit
    await asyncio.sleep(0.5)

    # Should NOT receive own message
    assert len(received) == 0, f"Should not echo own message, got: {received}"

    # Cleanup
    listen_task.cancel()
    await client.close()


@pytest.mark.anyio
async def test_three_participants_broadcast(running_server):
    """Test message broadcast to multiple participants."""
    base_url = running_server

    # Create three clients
    clients = [
        FacilitatorClient(base_url),
        FacilitatorClient(base_url),
        FacilitatorClient(base_url),
    ]
    names = ["Alice", "Bob", "Charlie"]

    # Create session
    session_id = await clients[0].create_session("Multi Test", "Test")

    # All join
    for i, (client, name) in enumerate(zip(clients, names)):
        await client.join_session(session_id, name, provider="test")
        await client.connect_websocket()
        print(f"{name} connected")

    # Track received messages
    received = [[], [], []]

    async def make_listener(idx):
        async def listener(data):
            print(f"{names[idx]} received: {data['content']}")
            received[idx].append(data)
        return listener

    # Start all listeners
    tasks = []
    for i, client in enumerate(clients):
        task = asyncio.create_task(client.listen(await make_listener(i)))
        tasks.append(task)

    await asyncio.sleep(0.1)

    # Alice sends to all
    print("Alice broadcasting...")
    await clients[0].send_message("Hello everyone!", to="all", msg_type="chat")

    await asyncio.sleep(0.5)

    # Bob and Charlie should receive (not Alice)
    print(f"Alice received: {len(received[0])}")
    print(f"Bob received: {len(received[1])}")
    print(f"Charlie received: {len(received[2])}")

    assert len(received[0]) == 0, "Alice should not receive own message"
    assert len(received[1]) == 1, "Bob should receive message"
    assert len(received[2]) == 1, "Charlie should receive message"

    assert received[1][0]["content"] == "Hello everyone!"
    assert received[2][0]["content"] == "Hello everyone!"

    # Cleanup
    for task in tasks:
        task.cancel()
    for client in clients:
        await client.close()

    print("Three-way test completed!")


if __name__ == "__main__":
    # Run the test directly
    import sys
    asyncio.run(test_websocket_message_routing_full_flow(None))
