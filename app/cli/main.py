import typer

from app.cli.commands.analyze import analyze

app = typer.Typer(
    no_args_is_help=True,
)

app.command()(analyze)


if __name__ == "__main__":
    app()