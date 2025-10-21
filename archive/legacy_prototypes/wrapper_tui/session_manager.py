"""Session manager - handles facilitator and session lifecycle."""

import asyncio
import httpx
import subprocess
import time
from typing import Optional
from dataclasses import dataclass


@dataclass
class SessionInfo:
    """Information about current session."""
    session_id: str
    facilitator_url: str
    participant_name: str
    participant_id: Optional[str] = None


class SessionManager:
    """Manages facilitator and session lifecycle."""

    def __init__(self):
        self.facilitator_process: Optional[subprocess.Popen] = None
        self.facilitator_url: str = "http://localhost:8765"
        self.session: Optional[SessionInfo] = None

    async def start_local_facilitator(self) -> bool:
        """Start local facilitator service if not already running."""
        # Check if already running
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.facilitator_url}/sessions", timeout=1.0)
                if response.status_code == 200:
                    return True  # Already running
        except:
            pass

        # Start facilitator
        try:
            import sys
            import os

            # Get path to actcli-facilitator
            venv_bin = os.path.join(sys.prefix, "bin", "actcli-facilitator")

            self.facilitator_process = subprocess.Popen(
                [venv_bin],  # No 'serve' subcommand needed anymore
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait for it to start
            for _ in range(10):
                await asyncio.sleep(0.5)
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.facilitator_url}/sessions", timeout=1.0)
                        if response.status_code == 200:
                            return True
                except:
                    continue

            return False
        except Exception as e:
            print(f"Failed to start facilitator: {e}")
            return False

    async def create_default_session(self, name: str = "default") -> bool:
        """Create default session."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.facilitator_url}/sessions",
                    json={"name": name, "description": "Local actcli-shell session"}
                )
                response.raise_for_status()
                data = response.json()

                self.session = SessionInfo(
                    session_id=data["session_id"],
                    facilitator_url=self.facilitator_url,
                    participant_name="shell"
                )
                return True
        except Exception as e:
            print(f"Failed to create session: {e}")
            return False

    async def join_session(self, session_id: str, participant_name: str) -> bool:
        """Join existing session."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.facilitator_url}/sessions/{session_id}/join",
                    json={
                        "session_id": session_id,
                        "name": participant_name,
                        "type": "human"
                    }
                )
                response.raise_for_status()
                data = response.json()

                self.session = SessionInfo(
                    session_id=session_id,
                    facilitator_url=self.facilitator_url,
                    participant_name=participant_name,
                    participant_id=data["participant_id"]
                )
                return True
        except Exception as e:
            print(f"Failed to join session: {e}")
            return False

    async def list_sessions(self) -> list:
        """List available sessions."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.facilitator_url}/sessions")
                response.raise_for_status()
                return response.json().get("sessions", [])
        except Exception as e:
            print(f"Failed to list sessions: {e}")
            return []

    def cleanup(self):
        """Cleanup facilitator process."""
        if self.facilitator_process:
            self.facilitator_process.terminate()
            self.facilitator_process.wait(timeout=5)
