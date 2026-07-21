import typer

from app.cli.commands.analyze import analyze
from app.cli.commands.watchlist import watchlist

app = typer.Typer(
    no_args_is_help=True,
)

app.command()(analyze)
app.command()(watchlist)


if __name__ == "__main__":
    app()