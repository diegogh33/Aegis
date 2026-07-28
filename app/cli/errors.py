from __future__ import annotations

from rich.console import Console

console = Console()


class AegisError(Exception):
    """Base exception for user-facing errors in Aegis CLI."""

    def __init__(self, message: str, hint: str | None = None):
        super().__init__(message)
        self.hint = hint


class IBKRConnectionError(AegisError):
    """Raised when Aegis cannot connect to TWS/Gateway."""
    pass


class IBKRDataError(AegisError):
    """Raised when IBKR returns unexpected or missing data."""
    pass


class AtlasError(AegisError):
    """Raised when the ATLAS repository cannot be accessed."""
    pass


def print_error(exc: Exception) -> None:
    """
    Prints a user-friendly error message for known Aegis errors,
    or a generic fallback with the exception message for unknown ones.
    Does NOT print a Python traceback.
    """

    msg = str(exc)

    # ── IBKR connection errors ──────────────────────────────────────────
    if isinstance(exc, IBKRConnectionError) or _is_connection_error(exc):
        console.print()
        console.print("[bold red]✗ No se puede conectar a IBKR[/]")
        console.print(
            "  Comprueba que [bold]TWS o IB Gateway[/] está corriendo "
            "en [bold]127.0.0.1:7496[/]."
        )
        console.print(
            "  En TWS: Configuración → API → "
            "Habilitar ActiveX y Socket Clients → ✓"
        )
        console.print(
            "  Si usas IB Gateway, verifica que el puerto es 7497 "
            "y pasa [bold]--port 7497[/] si es necesario."
        )

    # ── No option chain ─────────────────────────────────────────────────
    elif "No option chain found" in msg:
        ticker = _extract_ticker(msg)
        console.print()
        console.print(
            f"[bold red]✗ No hay cadena de opciones para "
            f"{ticker or 'este ticker'}[/]"
        )
        console.print(
            "  Puede que el ticker no tenga opciones en IBKR, "
            "o que el mercado esté cerrado."
        )
        console.print(
            "  Para mercados europeos, prueba con [bold]--currency EUR[/] "
            "o [bold]--currency CHF[/]."
        )

    # ── Unable to qualify contract ──────────────────────────────────────
    elif "Unable to qualify contract" in msg:
        ticker = _extract_ticker(msg)
        console.print()
        console.print(
            f"[bold red]✗ No se puede resolver el contrato para "
            f"{ticker or 'este ticker'}[/]"
        )
        console.print(
            "  Verifica que el ticker es correcto y que cotiza en IBKR."
        )
        console.print(
            "  Para acciones europeas, puede ser necesario el sufijo "
            "de mercado (ej. [bold]ITX[/] en vez de [bold]ITX.MC[/])."
        )

    # ── Alpha Vantage rate limit ─────────────────────────────────────────
    elif "rate limit" in msg.lower() or "alphavantage" in msg.lower():
        console.print()
        console.print("[bold yellow]⚠ Límite de peticiones de Alpha Vantage[/]")
        console.print(
            "  El plan gratuito permite 25 peticiones/día. "
            "El análisis de opciones continuará sin datos fundamentales."
        )

    # ── GitHub / ATLAS access ───────────────────────────────────────────
    elif "github" in msg.lower() or "atlas" in msg.lower():
        console.print()
        console.print("[bold yellow]⚠ No se puede acceder a ATLAS[/]")
        console.print(
            "  Comprueba la variable de entorno [bold]GITHUB_TOKEN[/] "
            "y que el repositorio [bold]ATLAS_REPO[/] es accesible."
        )
        console.print(
            "  El análisis continuará sin datos de ATLAS "
            "(sin zona de compra ni valoración)."
        )

    # ── IBKR data error ─────────────────────────────────────────────────
    elif isinstance(exc, IBKRDataError):
        console.print()
        console.print(f"[bold red]✗ Error de datos IBKR:[/] {msg}")
        if isinstance(exc, AegisError) and exc.hint:
            console.print(f"  [dim]{exc.hint}[/]")

    # ── Generic fallback ────────────────────────────────────────────────
    else:
        console.print()
        console.print(f"[bold red]✗ Error inesperado:[/] {msg}")
        console.print(
            "  Si el problema persiste, revisa el log DEBUG o "
            "abre un issue en el repositorio."
        )


def _is_connection_error(exc: Exception) -> bool:
    """Detects IBKR connection failures from common exception types."""
    msg = str(exc).lower()
    return any(
        keyword in msg
        for keyword in [
            "connection refused",
            "timed out",
            "connectasync",
            "not connected",
            "socket",
            "10061",  # Windows connection refused
        ]
    )


def _extract_ticker(msg: str) -> str | None:
    """Extracts the ticker symbol from an IBKR error message if present."""
    import re
    match = re.search(r"for ([A-Z0-9.]+)$", msg)
    return match.group(1) if match else None
