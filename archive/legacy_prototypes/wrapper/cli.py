"""CLI for terminal wrapper."""

import asyncio
import sys
from typing import Optional
import typer

from .client import FacilitatorClient
from .pty_wrapper import wrap_ai_cli_async


app = typer.Typer(help="Terminal wrapper for AI CLI communication")


@app.command()
def wrap(
    command: str = typer.Argument(..., help="Command to wrap (e.g., 'claude chat')"),
    session: Optional[str] = typer.Option(None, "--session", "-s", help="Session ID to join"),
    name: str = typer.Option("AI", "--name", "-n", help="Participant name"),
    create: bool = typer.Option(False, "--create", "-c", help="Create new session"),
    facilitator: str = typer.Option("http://localhost:8765", "--facilitator", "-f", help="Facilitator URL"),
    provider: Optional[str] = typer.Option(None, "--provider", help="AI provider (anthropic, openai, google)"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name"),
):
    """
    Wrap an AI CLI and connect to facilitator.

    Examples:
        # Create new session
        actcli-wrap --create --name "Claude-1" "claude chat"

        # Join existing session
        actcli-wrap --session session_abc123 --name "Codex-1" "codex chat"
    """
    asyncio.run(_wrap_async(
        command=command,
        session_id=session,
        name=name,
        create_session=create,
        facilitator_url=facilitator,
        provider=provider,
        model=model,
    ))


async def _wrap_async(
    command: str,
    session_id: Optional[str],
    name: str,
    create_session: bool,
    facilitator_url: str,
    provider: Optional[str],
    model: Optional[str],
):
    """Async implementation of wrap command."""
    # Parse command
    cmd_parts = command.split()
    if not cmd_parts:
        typer.echo("Error: Empty command", err=True)
        sys.exit(1)

    # Connect to facilitator
    client = FacilitatorClient(facilitator_url)

    try:
        # Create or join session
        if create_session:
            session_id = await client.create_session(
                name=f"Session with {name}",
                description="AI roundtable discussion"
            )
            typer.echo(f"✅ Created session: {session_id}")
        elif not session_id:
            typer.echo("Error: Must provide --session or --create", err=True)
            sys.exit(1)

        # Join session
        participant_id = await client.join_session(
            session_id=session_id,
            name=name,
            provider=provider,
            model=model,
        )
        typer.echo(f"✅ Joined as: {name} ({participant_id})")

        # Connect WebSocket
        await client.connect_websocket()
        typer.echo(f"✅ Connected to facilitator")
        typer.echo(f"\n🎬 Starting wrapped session: {' '.join(cmd_parts)}\n")
        typer.echo("=" * 60)

        # Wrap and run the AI CLI
        await wrap_ai_cli_async(cmd_parts, client, name)

    except KeyboardInterrupt:
        typer.echo("\n\n👋 Disconnecting...")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    finally:
        await client.close()


@app.command()
def serve(
    port: int = typer.Option(8765, "--port", "-p", help="Port to run facilitator on"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
):
    """Start the facilitator service."""
    import uvicorn
    from ..facilitator.service import create_app

    typer.echo(f"🚀 Starting facilitator on {host}:{port}")
    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    app()
