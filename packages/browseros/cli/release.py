"""Release automation CLI."""

import typer


app = typer.Typer(
    help="Release automation commands",
    no_args_is_help=True
)


@app.command("prepare")
def prepare():
    """Prepare a release."""
    typer.echo("Release preparation not yet implemented")


@app.command("publish")
def publish():
    """Publish a release."""
    typer.echo("Release publishing not yet implemented")


@app.command("rollback")
def rollback():
    """Rollback a release."""
    typer.echo("Release rollback not yet implemented")