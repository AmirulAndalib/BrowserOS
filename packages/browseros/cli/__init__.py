"""BrowserOS Build System CLI."""

import typer
from cli.build import app as build_app
from cli.dev import app as dev_app
from cli.release import app as release_app


app = typer.Typer(
    name="browseros",
    help="BrowserOS Build System",
    no_args_is_help=True
)

app.add_typer(build_app, name="build", help="Production build orchestration")
app.add_typer(dev_app, name="dev", help="Development tools and patch management")
app.add_typer(release_app, name="release", help="Release automation")


if __name__ == "__main__":
    app()