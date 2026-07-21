import sys

import typer

from app.cli.commands.analyze import analyze
from app.cli.commands.watchlist import watchlist

app = typer.Typer(
    no_args_is_help=True,
)

app.command()(analyze)
app.command()(watchlist)

_KNOWN_COMMANDS = {"analyze", "watchlist", "--help", "-h", "--version"}


def main() -> None:
    # If the first real argument isn't a known subcommand, prepend
    # "analyze" so that `app.main NFLX --long-term` keeps working
    # exactly as before, without requiring the user to type "analyze".
    args = sys.argv[1:]
    if args and args[0] not in _KNOWN_COMMANDS:
        sys.argv.insert(1, "analyze")

    app()


if __name__ == "__main__":
    main()