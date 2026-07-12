from rich.console import Console

console = Console()


def analyze(
    ticker: str,
):

    console.rule("[bold blue]Aegis[/]")

    console.print(f"Analyzing [green]{ticker}[/]")

    console.print()

    console.print("Loading market data...")

    console.print("Selecting best option...")

    console.print("Running strategy...")

    console.print()

    console.print("[bold green]Done[/]")