"""CLI for actcli-facilitator command."""

import typer


app = typer.Typer(
    help="Start the AI facilitator service",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    port: int = typer.Option(8765, "--port", "-p", help="Port to run facilitator on"),
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
):
    """
    Start the facilitator service for AI terminal communication.

    The facilitator routes messages between multiple AI terminals in real-time,
    enabling collaborative AI conversations.

    Examples:
        # Start on default port 8765
        actcli-facilitator

        # Start on custom port
        actcli-facilitator --port 9000

        # Bind to localhost only
        actcli-facilitator --host 127.0.0.1
    """
    import uvicorn
    from ..facilitator.service import create_app

    typer.echo(f"🚀 Starting AI Facilitator Service")
    typer.echo(f"   Host: {host}")
    typer.echo(f"   Port: {port}")
    typer.echo(f"   Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    typer.echo(f"\n✨ Ready to facilitate AI conversations!\n")

    app = create_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    app()
