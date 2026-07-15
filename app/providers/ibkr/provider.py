from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ib_async import Contract, IB, Option, Stock
from loguru import logger

from app.config.settings import Settings
from app.models.market_data import MarketData
from app.models.option_contract import OptionContract
from app.providers.ibkr.greeks_estimate import estimate_put_delta
from app.providers.ibkr.mapper import IBKRMapper
from app.providers.ibkr.market_data import MarketDataProvider


def _as_single_contract(
    qualified: Contract | list[Contract | None] | None,
) -> Contract | None:
    """
    Normalizes one element of qualifyContractsAsync()'s result list
    into a single Contract or None.

    qualifyContractsAsync(*contracts) returns one entry per input
    contract, but each entry's static type is
    `Contract | list[Contract | None] | None` - the list case exists
    in the library for ambiguous contracts that could expand into
    several matches. For a well-formed Stock/Option request, that
    never actually happens in practice, but this makes the assumption
    explicit and mypy-verifiable instead of silently trusting it.
    """

    if isinstance(qualified, Contract):
        return qualified

    if isinstance(qualified, list):
        return qualified[0] if qualified else None

    return None


def _within_dte_window(
    expiration: str,
    min_dte: int,
    max_dte: int,
    today: date | None = None,
) -> bool:
    """
    Checks whether an expiration string (IBKR's "YYYYMMDD" format)
    falls within [min_dte, max_dte] days from today.
    """

    if today is None:
        today = date.today()

    expiration_date = datetime.strptime(expiration, "%Y%m%d").date()

    dte = (expiration_date - today).days

    return min_dte <= dte <= max_dte


def _closest_strikes(
    contracts: list[OptionContract],
    underlying_price: Decimal,
    limit: int,
) -> list[OptionContract]:
    """
    Returns up to `limit` contracts from `contracts`, ordered by how
    close their strike is to underlying_price (closest first).

    Used only to find the ATM strike (limit=1) to fetch a reference
    IV from - actual strike selection for scanning is by estimated
    delta (_closest_to_target_delta), not by raw price proximity.
    Price-proximity selection alone under-covers strikes far from the
    underlying price when a stock has high IV (confirmed with DRAM,
    IV ~95%: the delta range a CSP strategy targets falls much
    further from the price than for a low-IV stock like ACN, IV
    ~47%, at the same DTE).
    """

    return sorted(
        contracts,
        key=lambda c: abs(c.strike - underlying_price),
    )[:limit]


def _closest_to_target_delta(
    contracts: list[OptionContract],
    underlying_price: Decimal,
    days_to_expiration: int,
    reference_iv: Decimal,
    target_delta: float,
    limit: int,
) -> list[OptionContract]:
    """
    Returns up to `limit` contracts, ordered by how close their
    Black-Scholes-estimated delta (using a single reference IV, not
    each strike's own smile-adjusted IV) is to target_delta.
    """

    return sorted(
        contracts,
        key=lambda c: abs(
            estimate_put_delta(
                underlying_price,
                c.strike,
                days_to_expiration,
                reference_iv,
            )
            - target_delta
        ),
    )[:limit]


class IBKRProvider:
    """
    Wrapper around the Interactive Brokers API.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7496,
        client_id: int = 1,
        settings: Settings | None = None,
    ) -> None:

        self._host = host
        self._port = port
        self._client_id = client_id

        self.ib = IB()

        self.market_data = MarketDataProvider(self.ib)

        self._contracts: dict[int, Contract] = {}
        self._stock_contracts: dict[str, Contract] = {}

        self._settings = settings or Settings()

    async def connect(self) -> None:

        await self.ib.connectAsync(
            host=self._host,
            port=self._port,
            clientId=self._client_id,
        )

        #
        # La cuenta tiene suscripción de datos en tiempo real
        # (US Securities Snapshot and Futures Value Bundle +
        # US Equity and Options Add-On Streaming Bundle), así que
        # pedimos datos en vivo en vez de forzar delayed.
        #
        self.ib.reqMarketDataType(1)

    async def disconnect(self) -> None:

        if self.ib.isConnected():
            self.ib.disconnect()

    async def get_option_chain(
        self,
        symbol: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> dict:

        stock = Stock(symbol, exchange, currency)

        qualified = await self.ib.qualifyContractsAsync(stock)

        stock_contract = (
            _as_single_contract(qualified[0]) if qualified else None
        )

        if stock_contract is None:
            raise ValueError(f"Unable to qualify contract for {symbol}")

        self._stock_contracts[symbol] = stock_contract

        chains = await self.ib.reqSecDefOptParamsAsync(
            stock_contract.symbol,
            "",
            stock_contract.secType,
            stock_contract.conId,
        )

        if not chains:
            raise ValueError(f"No option chain found for {symbol}")

        chain = next(
            (c for c in chains if c.exchange == "SMART"),
            chains[0],
        )

        expirations = sorted(chain.expirations)

        logger.debug(
            "{symbol}: {count} expirations available on {exchange}: "
            "{expirations}",
            symbol=symbol,
            count=len(expirations),
            exchange=chain.exchange,
            expirations=", ".join(expirations),
        )

        return {
            "contract": stock_contract,
            "exchange": chain.exchange,
            "expirations": sorted(chain.expirations),
            "strikes": sorted(chain.strikes),
        }

    async def get_underlying_price(
        self,
        symbol: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> Decimal | None:
        """
        Returns the current market price of the underlying stock,
        independent of any option contract's own market data.

        Requires get_option_chain(symbol) to have been called first
        for this symbol (it qualifies and caches the stock contract).
        Falls back to a fresh qualification if that hasn't happened.
        """

        stock_contract = self._stock_contracts.get(symbol)

        if stock_contract is None:

            stock = Stock(symbol, exchange, currency)

            qualified = await self.ib.qualifyContractsAsync(stock)

            stock_contract = (
                _as_single_contract(qualified[0]) if qualified else None
            )

            if stock_contract is None:
                return None

            self._stock_contracts[symbol] = stock_contract

        return await self.market_data.get_stock_price(stock_contract)

    async def get_put_contracts(
        self,
        symbol: str,
        exchange: str = "SMART",
        currency: str = "USD",
    ) -> list[OptionContract]:

        chain = await self.get_option_chain(
            symbol, exchange=exchange, currency=currency
        )

        dte_window = self._settings.get("scan", "dte_window")

        candidate_expirations = [
            expiration
            for expiration in chain["expirations"]
            if _within_dte_window(
                expiration,
                min_dte=dte_window["min"],
                max_dte=dte_window["max"],
            )
        ]

        if not candidate_expirations:

            logger.debug(
                "{symbol}: no expirations within the {min}-{max} DTE "
                "scan window; falling back to the two nearest "
                "expirations instead.",
                symbol=symbol,
                min=dte_window["min"],
                max=dte_window["max"],
            )

            candidate_expirations = chain["expirations"][:2]

        strikes_per_expiration = self._settings.get(
            "scan", "strikes_per_expiration"
        )

        # Delta objetivo de la Constitution (punto medio del rango
        # preferido), usado para elegir qué strikes merece la pena
        # pedir a IBKR - no el rango de aceptación final, que sigue
        # aplicándose después con el delta real (DeltaRule).
        delta_config = self._settings.get("cash_secured_put", "delta")

        target_delta = (
            delta_config["preferred"]["min"]
            + delta_config["preferred"]["max"]
        ) / 2

        # El precio del subyacente se pide una vez, antes de elegir
        # qué strikes traer por vencimiento - sin él no hay forma de
        # saber cuáles son los "cercanos".
        underlying_price = await self.get_underlying_price(
            symbol, exchange=exchange, currency=currency
        )

        contracts: list[OptionContract] = []

        for expiration in candidate_expirations:

            option = Option(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiration,
                strike=0,
                right="P",
                exchange=chain["exchange"],
                currency=currency,
            )

            details = await self.ib.reqContractDetailsAsync(option)

            expiration_contracts: list[OptionContract] = []

            for detail in details:

                contract = detail.contract

                if contract is None:
                    continue

                option_contract = IBKRMapper.option_contract(contract)

                self._contracts[
                    option_contract.con_id
                ] = contract

                expiration_contracts.append(option_contract)

            if underlying_price is None:

                expiration_contracts = expiration_contracts[
                    :strikes_per_expiration
                ]

                contracts.extend(expiration_contracts)
                continue

            days_to_expiration = (
                datetime.strptime(expiration, "%Y%m%d").date()
                - date.today()
            ).days

            # Se pide el strike ATM real para sacar su IV como
            # referencia, y con ella se estima el delta de cada
            # strike disponible antes de pedir datos de mercado para
            # todos - solo tiene sentido gastar peticiones en los
            # strikes que probablemente caigan cerca del delta
            # objetivo, no en los N más cercanos al precio (que en
            # subyacentes con IV alta, como DRAM ~95%, dejan fuera los
            # strikes realmente relevantes).
            atm_strike = _closest_strikes(
                expiration_contracts, underlying_price, limit=1
            )

            reference_iv = None

            if atm_strike:
                atm_market = await self.get_market_data(atm_strike[0])
                reference_iv = atm_market.implied_volatility

            if reference_iv is None:

                logger.debug(
                    "{symbol} {expiration}: no reference IV available "
                    "from the ATM strike; falling back to strikes "
                    "closest to the underlying price instead of "
                    "target delta.",
                    symbol=symbol,
                    expiration=expiration,
                )

                expiration_contracts = _closest_strikes(
                    expiration_contracts,
                    underlying_price,
                    strikes_per_expiration,
                )

            else:

                logger.debug(
                    "{symbol} {expiration}: {total} strikes available, "
                    "keeping the {kept} closest to target delta "
                    "{target} (reference IV {iv}).",
                    symbol=symbol,
                    expiration=expiration,
                    total=len(expiration_contracts),
                    kept=min(
                        strikes_per_expiration, len(expiration_contracts)
                    ),
                    target=target_delta,
                    iv=reference_iv,
                )

                expiration_contracts = _closest_to_target_delta(
                    expiration_contracts,
                    underlying_price,
                    days_to_expiration,
                    reference_iv,
                    target_delta,
                    strikes_per_expiration,
                )

            contracts.extend(expiration_contracts)

        contracts.sort(
            key=lambda c: (
                c.expiration,
                c.strike,
            )
        )

        return contracts

    async def get_market_data(
        self,
        option: OptionContract,
    ) -> MarketData:

        contract = self._contracts.get(option.con_id)

        if contract is None:
            raise ValueError(
                f"Contract {option.con_id} not found."
            )

        return await self.market_data.get(contract)