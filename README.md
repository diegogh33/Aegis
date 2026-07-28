# AEGIS

<p align="center">
  <img src="assets/aegis.svg" width="160" alt="La Égida — escudo de Zeus y Atenea"/>
</p>

## ¿Por qué Aegis?

En la mitología griega, la **Égida** era el escudo que protegía a Zeus
y Atenea. Forjado por Hefesto, era indestructible — no un arma de
ataque, sino un escudo que alejaba el peligro.

Nuestro sistema no busca encontrar la operación con mayor rentabilidad.
**Busca protegerme de cometer errores.**

Cada regla de la Constitution, cada filtro de delta, cada validación de
spread o de earnings, existe por la misma razón que la Égida: no para
ganar más, sino para no perder por descuido.

---

## Visión del proyecto

Aegis no pretende ser un simple escáner de opciones.

El objetivo es construir una **plataforma profesional de análisis de
inversiones**, orientada principalmente a la inversión a largo plazo y a
la venta de opciones **Cash Secured Puts (CSP)**, que permita tomar
decisiones objetivas mediante un sistema de puntuación basado en datos
fundamentales, datos de mercado y reglas de inversión definidas por el
usuario.

La filosofía es crear una herramienta similar a un **Bloomberg Terminal
para el inversor particular**, capaz de responder preguntas como:

-   ¿Qué empresa merece ser comprada hoy?
-   ¿Qué PUT debería vender?
-   ¿Qué strike ofrece la mejor relación rentabilidad/riesgo?
-   ¿Estoy asumiendo demasiado riesgo?
-   ¿Esta operación cumple mis reglas de inversión?

------------------------------------------------------------------------

# Filosofía

## 1. Calidad de la empresa

Antes de analizar una opción, debe analizarse la empresa. Una buena
opción sobre una mala empresa sigue siendo una mala inversión.

## 2. Venta de Cash Secured Puts

El foco actual del proyecto es encontrar las mejores oportunidades para
vender CSP considerando:

-   Rentabilidad
-   Riesgo
-   Liquidez
-   Margen de seguridad
-   Calidad de la empresa

## 3. Arquitectura limpia

``` text
Proveedor de datos
        │
        ▼
Modelos
        │
        ▼
Motores de cálculo
        │
        ▼
Motores de puntuación
        │
        ▼
Servicios
        │
        ▼
CLI / API / UI
```

Los motores únicamente realizan cálculos. Nunca contienen reglas de
negocio.

## 4. Configuración

Todo parámetro modificable debe vivir en configuración (pesos, filtros,
umbrales, objetivos, etc.).

------------------------------------------------------------------------

# Cómo se aplican las reglas de inversión (Constitution)

Aegis separa completamente dos conceptos:

1.  **Reglas de inversión (Investment Constitution)** → eliminan
    opciones.
2.  **Scoring** → ordena únicamente las opciones que sobreviven.

La filosofía del proyecto es que **ninguna operación puede ser
recomendada si antes no cumple la Constitución**.

> **Primero filtrar. Después puntuar. Nunca al revés.**

## Fase 1 — Constitution (filtro duro)

Las reglas definidas en `config/constitution.yaml` son obligatorias.

  Regla                             Acción
  --------------------------------- -----------
  Empresa no aprobada               DESCARTAR
  Earnings antes del vencimiento    DESCARTAR
  Delta fuera del rango permitido   DESCARTAR
  DTE fuera del rango               DESCARTAR
  IV Rank inferior al mínimo        DESCARTAR
  Liquidez insuficiente             DESCARTAR
  Spread demasiado alto             DESCARTAR

Ejemplo para la estrategia Cash Secured Put:

``` yaml
delta:
  min: 0.15
  max: 0.25

dte:
  min: 30
  max: 45

ivr:
  min: 30

earnings:
  allow: false
```

Si cualquiera de estas reglas falla, la opción queda descartada.

## Fase 2 — Score

Una vez filtradas las opciones válidas, Aegis calcula un `ScoreResult`.

El score **no decide si una operación es válida**. Únicamente responde:

> "De todas las operaciones válidas, ¿cuál es la mejor?"

Actualmente el score utiliza:

-   Delta
-   Spread Bid/Ask
-   Volumen
-   Rentabilidad anualizada

Configuración típica:

``` yaml
scoring:
  delta:
    target: 0.20
    weight: 30

  spread:
    weight: 15
    max_percentage: 0.20

  volume:
    weight: 10
    normalization: 100

  annualized_return:
    target: 15
    weight: 45
```

> Nota: este es el `scoring` real tal como vive hoy en
> `config/constitution.yaml`. `target`/`normalization` son necesarios
> porque `OptionScoreEngine` los usa para calcular la distancia al
> valor ideal, no solo el peso.

## Ejemplo

  Contrato     Delta   DTE   IVR Earnings   Resultado
  ---------- ------- ----- ----- ---------- ------------------------
  A             0.19    38    42 No         ✅ Pasa al Score
  B             0.33    38    45 No         ❌ Eliminada (Delta)
  C             0.18    41    18 No         ❌ Eliminada (IV Rank)

Solo la opción **A** llega al `OptionScoreEngine`.

## Flujo objetivo (con Constitution integrada)

``` text
IBKR
 │
 ▼
OptionScanner
 │
 ▼
Market Data
 │
 ▼
MetricsEngine
 │
 ▼
ConstitutionEngine
 │
 ├── descarta opciones que incumplen reglas
 ▼
OptionScoreEngine
 │
 ▼
Ranking final
 │
 ▼
CLI / Dashboard
```

> ⚠️ El `ConstitutionEngine` que aplica estas reglas de forma unificada
> **todavía no está implementado**. Ver sección "Estado actual" para el
> detalle de qué existe hoy y qué queda pendiente.

------------------------------------------------------------------------

# Estado actual

## Lo que funciona hoy

**Estado a 21-jul-2026: 143 tests, `mypy`/`ruff` limpios, 42 commits en rama `fuckyouchatgpt`.**

### Pipeline completo de análisis (validado con datos reales)

- **Motor de reglas completo**: las 7 reglas originales de la
  Constitution implementadas y conectadas (`CompanyApproved`,
  `NoUpcomingEarnings`, `DTE`, `Delta`, `Liquidity`, `Spread`,
  `IVRankRule`). Todas leen `config/constitution.yaml`.
- **Dos estrategias**: `CashSecuredPutStrategy` (recurrente, 30-45
  DTE, delta -0.15/-0.25) y `LongTermPutStrategy` (oportunista,
  90-365 DTE, delta -0.10/-0.30, activada con `--long-term`). Cada
  una tiene sus propios umbrales de spread/liquidez configurables.
- **ATLAS** (`diegogh33/atlas-research`) conectado como fuente real
  de `InvestmentThesis`: aprueba/watchlist/no analizado según
  `valoracion`. `BelowBuyZoneRule` (solo en `--long-term`) valida el
  strike contra `entrada_max` de ATLAS.
- **IVRank** con histórico SQLite local (`data/iv_history.db`):
  snapshot diario automático en cada análisis, `IVRankRule` activa
  tras 90 días de histórico por ticker.
- **Scoring y ranking** con `OptionScoreEngine` (retorno anualizado
  45%, delta 30%, spread 15%, volumen 10%).
- **Validado en producción** contra IBKR real en US (AAPL, ACN,
  DRAM) y Europa (ASML, SAP, SAN, ITX) con múltiples tipos de
  suscripción y condiciones de mercado.

### Robustez de datos IBKR

- Fallback automático a datos delayed cuando no hay suscripción en
  tiempo real para un mercado (confirmado MEFFRV, EUREX).
- Poll específico para `modelGreeks` (tardan más que bid/ask),
  fallback a `bidGreeks`/`askGreeks` si no convergen.
- Peticiones de market data en lotes de 6 (evita saturar el límite
  de 50 mensajes/segundo de IBKR).
- Selección de strikes por **delta estimado** (Black-Scholes con IV
  ATM de referencia), no por cercanía de precio — correcto para
  subyacentes con IV alta como DRAM (~95%).
- `tradingClass` fijado explícitamente para evitar mezclar clases
  secundarias (bug confirmado con MSFT: `2MSFT`).
- `underlying_price` del stock preferido sobre el del contrato de
  opción (bug confirmado con ASML/EUREX: escala incorrecta).

### CLI

- `analyze TICKER [--long-term] [--currency EUR]`: análisis de un
  ticker con tabla de candidatos (Score, Strike, OTM%, vs Buy Zone,
  Expiration, Bid, Ask, Delta, IV, Open Int, Recommendation).
- `watchlist [TICKERS...] [--long-term] [--currency EUR]`: análisis
  de múltiples tickers con tabla resumen (candidatos encontrados,
  mejor score/strike/OTM%, motivo de rechazo si no hay candidatos).
  Sin argumentos, recorre todo el ATLAS ordenado por convicción
  (alcista/posicion primero).
- Tabla "Company" muestra Max Entry y Buy Zone de ATLAS cuando
  existen.
- Avisos claros cuando AlphaVantage falla (rate-limit o ticker no
  reconocido), cuando el ticker no está aprobado en ATLAS, o cuando
  el mercado devuelve datos incompletos.

### Calidad

- 143 tests (unitarios + integración), `mypy` 0 errores, `ruff`
  limpio.
- `data/iv_history.db` excluido de git (histórico local, personal).
- `GITHUB_TOKEN`, `ATLAS_REPO`, `IV_HISTORY_DB_PATH`,
  `ALPHA_VANTAGE_API_KEY` configurables vía `.env`.

## Lo que NO funciona todavía / limitaciones conocidas

-   **`AlphaVantageProvider` sigue sin adaptarse de verdad a tickers
    no estadounidenses** — ya no revienta (ver arriba), pero el
    símbolo se sigue enviando tal cual (ej. `ITX`), sin el sufijo de
    mercado que Alpha Vantage probablemente necesita (ej. `ITX.MC`
    para Madrid, sin confirmar el sufijo exacto). Con un ticker
    europeo sin ese sufijo, la tabla "Company" no aparecerá — la
    tabla de opciones (que solo depende de IBKR) sigue funcionando
    igual, son proveedores independientes.
-   **`Company.next_earnings` no se puebla desde ningún provider
    todavía.** El endpoint que lo daría, `EARNINGS_CALENDAR` de
    Alpha Vantage, devuelve **CSV en vez de JSON**, a diferencia de
    todo lo que usa el cliente HTTP actual (`AlphaVantageClient`) —
    necesita ampliarse para soportar ambos formatos. Además, según
    la IA que diseñó la arquitectura original, `next_earnings` no
    debería vivir en `Company` (dato estable) sino en un modelo
    separado tipo `MarketEvents`/`UpcomingEvents` (datos dinámicos:
    earnings, dividendos, splits...). Pendiente de implementar; no
    se ha tocado a ciegas sin poder validar el formato CSV real
    contra la API.
-   **`IVRankRule` implementada, pero necesita 90 días de histórico
    acumulado antes de bloquear de verdad.** Hasta entonces, pasa sin
    bloquear (`WARNING`) para cualquier ticker — el rank real
    empezará a activarse por ticker a medida que se analicen con
    regularidad y se acumulen snapshots diarios. No hay forma de
    "rellenar" histórico retroactivo — solo se acumula con el uso.
-   **Suscripción de opciones de IBKR contratada — error 10091
    resuelto, pero datos aún vacíos, causa pendiente de confirmar.**
    Se contrató el `US Equity and Options Add-On Streaming Bundle`
    ($4.50/mes) en Client Portal, y el error 10091 dejó de aparecer.
    Sin embargo, en la prueba posterior (fuera de horario de mercado
    US) `bid`/`ask`/Greeks/volumen siguieron llegando vacíos para las
    10 opciones, sin ningún error. Dos cambios se han hecho para
    investigar y facilitar el diagnóstico, pero **falta confirmar el
    resultado con el mercado US abierto** (15:30–22:00 hora de
    Madrid, aprox.) antes de dar esto por resuelto o seguir tocando
    código:
    -   `IBKRProvider.connect()` ahora pide datos en tiempo real
        (`reqMarketDataType(1)`) en vez de forzar delayed (tipo 3),
        ya que la cuenta tiene suscripción real-time de pago.
    -   `MarketDataProvider` registra un log (`loguru`, nivel DEBUG,
        visible por `stderr` sin configuración adicional) con el
        `ticker.marketDataType` cuando no llega ningún dato, para
        saber en la próxima prueba si IBKR está sirviendo tipo
        delayed/frozen en vez de live, sin tener que adivinar.
-   **IBKR con datos delayed** (`reqMarketDataType(3)`, usado hasta
    este commit) — ya no se fuerza por defecto (ver punto anterior),
    pero queda como referencia si en el futuro hace falta volver a
    delayed (por ejemplo, en cuentas sin suscripción real-time).

------------------------------------------------------------------------

# Arquitectura

``` text
app/
    cli/
        commands/
            analyze.py
    config/
    core/
        result.py
        rule_status.py
        rule_engine.py
        evaluation_report.py
    engines/
        metrics_engine.py
        option_score_engine.py
    iv_history/
        repository.py
        rank.py
    mcp/
    models/
        company.py
        option_contract.py
        option_metrics.py
        scored_option.py
        score_result.py
        analysis_result.py
        investment_candidate.py
        investment_thesis.py
        rejected_contract.py
    providers/
        alphavantage/
        atlas/
        ibkr/
    rules/
        base.py
        below_buy_zone.py
        delta.py
        dte.py
        ivr.py
        liquidity.py
        no_earnings.py
        spread.py
        company/
            company_approved_rule.py
    services/
        option_scanner.py
        analysis_service.py
    strategies/
        base.py
        cash_secured_put.py
        long_term_put.py
    utils/

tests/
    conftest.py
    core/
        test_evaluation_report.py
    engines/
        test_metrics_engine.py
        test_option_score_engine.py
    iv_history/
        test_repository.py
        test_rank.py
    providers/
        test_market_data.py
        test_dte_window.py
        test_closest_strikes.py
        test_greeks_estimate.py
        test_option_chain_selection.py
        test_alphavantage_mapper.py
        atlas/
            test_mapper.py
            test_provider.py
            test_thesis_mapper.py
    rules/
        test_delta_rule.py
        test_company_approved_rule.py
        test_no_earnings_rule.py
        test_dte_rule.py
        test_liquidity_rule.py
        test_spread_rule.py
        test_ivr_rule.py
        test_below_buy_zone_rule.py
    services/
        test_analysis_service.py
        test_option_scanner.py
    strategies/
        test_cash_secured_put.py
        test_long_term_put.py
```

------------------------------------------------------------------------

# Flujo actual (sin Constitution todavía)

``` text
Usuario
    ↓
CLI
    ↓
AnalysisService
    ↓
AlphaVantage ──► Company
    ↓
IBKR
    ↓
OptionScanner
    ↓
OptionContract
    ↓
MarketDataProvider
    ↓
MarketData
    ↓
MetricsEngine
    ↓
OptionMetrics
    ↓
OptionScoreEngine
    ↓
ScoreResult
    ↓
ScoredOption
    ↓
Ranking final
```

------------------------------------------------------------------------

# Proveedores

## AlphaVantage

Información fundamental:

-   PER
-   PEG
-   EPS
-   ROE
-   ROA
-   EBITDA
-   Cash Flow
-   Revenue
-   Sector
-   Industria
-   etc.

> **Nota importante:** hoy, de todos estos datos fundamentales,
> **ninguno afecta a la Constitution ni al scoring**. La única
> excepción prevista es `Company.next_earnings` (usado por
> `NoUpcomingEarningsRule`), pero ese campo tampoco se puebla desde
> AlphaVantage todavía — el endpoint que lo daría
> (`EARNINGS_CALENDAR`) devuelve CSV en vez de JSON y no está
> integrado (ver limitaciones). AlphaVantage es, por ahora,
> **puramente informativo**: solo alimenta la tabla "Company" del
> CLI. Con el límite del plan gratuito (25 peticiones/día,
> confirmado en real durante esta sesión de trabajo) fácil de agotar,
> es una dependencia de bajo coste técnico (falla con gracia, no
> bloquea el análisis de opciones) pero de valor limitado hasta que
> se conecte algo que sí influya en las decisiones — `next_earnings`
> real, o una futura regla de "calidad de empresa" basada en estos
> fundamentales.

## Interactive Brokers

Actualmente:

-   Cadena de opciones
-   Bid / Ask / Last / Mark
-   Greeks
-   IV
-   Volumen

Pendiente:

-   Open Interest
-   Histórico
-   Volatilidad histórica

------------------------------------------------------------------------

# Modelos

## Company

Información fundamental de la empresa. Incluye `next_earnings`
(fecha del próximo earnings, usada por la regla de exclusión
pre-earnings de la Constitution). Puede ser `None` si el proveedor no
lo suministra todavía.

## OptionContract

Datos originales del broker.

## OptionMetrics

Métricas derivadas:

-   Premium
-   Capital Required
-   Return on Capital
-   Annualized Return
-   Break Even
-   Downside Protection

## ScoreResult

Puntuación de la operación.

------------------------------------------------------------------------

# Engines

## MetricsEngine

Calcula métricas.

## OptionScoreEngine

Calcula puntuaciones.

------------------------------------------------------------------------

# Services

## OptionScanner

Obtiene opciones y las enriquece con datos de mercado. El filtrado
de liquidez y spread ya no ocurre aquí — vive en la Constitution
(`LiquidityRule`, `SpreadRule`).

## AnalysisService

Orquesta todo el proceso.

------------------------------------------------------------------------

# Objetivo final

Ejecutar:

``` bash
uv run python -m app.main AAPL
```

Y obtener un informe similar a:

``` text
APPLE

Fundamental Score: 92/100

Best Cash Secured Put

Strike: 205
ROC: 17.3%
Annualized: 21%
Delta: -0.18
Margin of Safety: 8%
Overall Score: 96
★★★★★
```

Nota: el CLI actual (`app/cli/commands/analyze.py`) ya produce una
tabla de empresa, una tabla de mejores PUT candidatas con score y
recomendación (con el filtro de Constitution ya aplicado), y una
tabla de contratos rechazados agrupados por motivo. Sigue sin existir
el "Fundamental Score" como campo independiente.

------------------------------------------------------------------------

# Cómo probar el proyecto

## Requisitos

-   Python ≥ 3.13
-   [`uv`](https://docs.astral.sh/uv/) instalado
-   (Opcional, solo para el flujo end-to-end real) TWS o IB Gateway
    corriendo en local, y una API key de Alpha Vantage

## Instalación

``` bash
uv sync
```

Esto instala dependencias de producción y de desarrollo
(`pytest`, `pytest-asyncio`, `ruff`, `mypy`, `pre-commit`).

## Ejecutar la suite de tests

``` bash
uv run pytest
```

Debe terminar en verde. Si algún test falla, **no se considera
terminado ningún cambio** hasta que vuelva a pasar (ver "Reglas de
desarrollo" más abajo).

Para ver detalle de cada test:

``` bash
uv run pytest -v
```

## Linting

``` bash
uv run ruff check .
```

Debe devolver `All checks passed!`. Aegis no aplica todavía
`ruff format` en CI/commits — el formato existente no es 100%
consistente y se abordará en un commit dedicado más adelante.

## Comprobación de tipos

``` bash
uv run mypy app
```

Debe devolver `Success: no issues found in N source files`. Desde
esta sesión de trabajo `mypy` está en limpio (0 errores) y puede
tratarse como un check real, no solo informativo — si un cambio
introduce un error de tipos nuevo, es una señal a atender antes de
dar el cambio por terminado.

## Comandos disponibles

Requiere IBKR (TWS/Gateway) corriendo en `127.0.0.1:7496`. Todos los
comandos se ejecutan desde la carpeta del proyecto en PowerShell.

### Análisis de un solo ticker

``` powershell
# Estrategia recurrente (30-45 DTE, delta -0.15/-0.25) — tabla detallada
uv run python -m app.main AAPL

# Largo plazo (90-365 DTE, delta -0.10/-0.30) — tabla detallada
uv run python -m app.main ACN --long-term

# Con análisis de spreads PCS — contexto + top 3 + tabla completa
# (omite la tabla de candidatos individuales y rechazos)
uv run python -m app.main NOW --pcs
uv run python -m app.main MU --pcs
uv run python -m app.main AMD --long-term --pcs

# Cadena en crudo sin reglas — delta -0.50 a -0.10, ordenada por prima
# Columnas: Bid, Ask, Mid, Strike, DTE, Ret. Anual., Delta, IV, OTM%, OI, Exp
uv run python -m app.main NESN --currency CHF --no-rules
uv run python -m app.main NESN --currency CHF --no-rules --until 2026-11
uv run python -m app.main NESN --currency CHF --long-term --no-rules

# Mercado europeo
uv run python -m app.main ASML --currency EUR
uv run python -m app.main ASML --currency EUR --long-term
```

**`--no-rules`**: muestra la cadena completa sin aplicar ninguna regla de
Constitution. Útil para explorar un ticker nuevo o un mercado con poca
liquidez. Ordenada por prima (bid) descendente. `--until YYYY-MM` limita
los vencimientos a ese mes — si se especifica, `--long-term` no es
necesario para la ventana temporal.

### Análisis de varios tickers explícitos — tabla resumen

``` powershell
# Recurrente
uv run python -m app.main NFLX AAPL ACN

# Largo plazo
uv run python -m app.main NFLX UBER DHR --long-term

# Europeos
uv run python -m app.main ASML SAP --currency EUR --long-term
```

### Watchlist automático desde ATLAS

``` powershell
# Recorre todos los tickers de ATLAS (alcista + posicion + seguimiento),
# filtrando los que están >10% por encima de su zona de compra.
# Aprobados primero, luego seguimiento.
uv run python -m app.main watchlist

# Largo plazo
uv run python -m app.main watchlist --long-term

# Europeos en ATLAS
uv run python -m app.main watchlist --currency EUR --long-term
```

Tickers excluidos del watchlist automático: `watchlist.exclude` en
`constitution.yaml` (actualmente: KRKNF, MC.PA, WKL, LOG.MC, PG, DEO,
MAIN). Edita esa lista para añadir o quitar.

### Put Credit Spread (PCS)

``` powershell
# Ticker individual: panel de contexto + top 3 PCS + tabla completa
# Panel muestra: precio actual, IV con colores, IVR y enlace earnings
uv run python -m app.main NOW --pcs
uv run python -m app.main MU --pcs
uv run python -m app.main ORCL --long-term --pcs

# Scan automático del universo S2 (sistemático: AMD, MU, PYPL, COIN...)
uv run python -m app.main scan-pcs s2

# Scan automático del universo S3 (ETFs tácticos: SPY, QQQ, IWM...)
uv run python -m app.main scan-pcs s3

# Combinable con largo plazo
uv run python -m app.main scan-pcs s2 --long-term
```

Los universos S2 y S3 se configuran en `constitution.yaml`
(`s2_universe` / `s3_universe`).

**Filtros PCS** (Plan Operativo S2/S3):
- Crédito neto / ancho del spread **≥ 25%**
- Open Interest **≥ 500 contratos en ambas patas** (short y long)
- Short strike **≤ `entrada_max` de ATLAS** cuando existe

**Tablas PCS** incluyen: Short, Long, Exp, DTE, Ancho, Mid Short, Mid
Long, Crédito, Cr/Ancho, Break-even, Caída %, Δ Short, OI Short, OI Long.

**Panel de contexto** (aparece antes del top 3):
- Precio actual del subyacente
- IV actual con código de color: rojo < 30% / amarillo 30-40% / verde ≥ 40%
  (umbrales de `constitution.yaml`)
- IVR: días acumulados / 90 necesarios para que IVRankRule se active
- Enlace directo a Yahoo Finance para verificar próximos earnings

### Covered Calls S1 (cartera)

``` powershell
# Escanea el universo S1 (acciones en cartera con ≥100 acciones)
# y muestra rendimiento reciente para identificar candidatos a Covered Call.
uv run python -m app.main scan-cc
```

Muestra una tabla con: Precio actual, rendimiento 15d y 30d, mínimo y
máximo de 52 semanas, % hasta el máximo anual, máximo de los últimos 30
días, % por debajo del máximo de 30 días, e IV actual. Ordenada por
rendimiento a 30 días descendente — las acciones que más han subido
recientemente son las mejores candidatas (primas más altas, más margen
si se ejecuta la call).

El universo S1 se configura en `constitution.yaml` (`s1_universe`).

### IV History

``` powershell
# Ver progreso de acumulación de histórico IV por ticker.
# No hay que ejecutarlo regularmente — solo para consultar.
# El histórico se guarda automáticamente con cualquier análisis.
uv run python -m app.main iv-history
```

`IVRankRule` se activa por ticker cuando acumula ≥ 90 días de snapshots
diarios. Los snapshots se guardan solos con cada análisis — uno por día
por ticker, sin ningún comando aparte.

### Notas generales

- `--long-term` siempre se añade al final del comando.
- `--currency EUR` / `--currency CHF` para mercados europeos.
- `--pcs` es compatible con `--long-term` y `--currency`.
- `--no-rules` solo funciona con un ticker individual (no multi-ticker).
- `--until YYYY-MM` solo aplica con `--no-rules`.
- Para tickers explícitos, el watchlist **no** aplica el filtro de
  precio ni la lista de exclusión — los analiza siempre.
- El watchlist automático **sí** aplica ambos filtros (precio y exclusión).
- Open Interest solo llega con el mercado US abierto (15:30-22:00
  Madrid). Fuera de ese horario, algunos strikes mostrarán `-`.

------------------------------------------------------------------------

# Roadmap

## Fase 1 (Prioridad absoluta) — en curso

-   [x] Estructura de paquetes correcta (`__init__.py` en todos los
        subpaquetes).
-   [x] Suite de tests ejecutable y en verde.
-   [x] Eliminar scripts de prueba manual mezclados con tests
        automatizados.
-   [x] Unificar los dos sistemas de reglas en uno solo.
-   [x] Conectar `CashSecuredPutStrategy` a `AnalysisService`.
-   [x] Reparar `MetricsEngine` y `OptionScoreEngine` (estaban rotos
        de forma silenciosa, sin test que lo detectara).
-   [x] Conectar una fuente de datos real para
        `InvestmentThesis.approved` (biblioteca ATLAS,
        `diegogh33/atlas-research`).
-   [ ] Poblar `Company.next_earnings` desde un provider real (hoy
        siempre `None`).
-   [x] `DTERule` implementada y conectada (lee de
        `constitution.yaml`).
-   [x] `DeltaRule` convertida en regla bloqueante (solo `FAIL`
        bloquea; `WARNING` sigue pasando con score reducido).
-   [x] `LiquidityRule` y `SpreadRule` implementadas y conectadas
        (leen de `constitution.yaml`); `LiquidityFilter` (servicio,
        con umbrales que no coincidían con el YAML) eliminado.
-   [x] Implementar la regla de Constitution que faltaba (`IVRankRule`
        — las 7 reglas originales de la Constitution ya están
        implementadas y conectadas). Necesita 90 días de histórico
        por ticker antes de bloquear de verdad.
-   [x] Unificar `DeltaRule`/`NoUpcomingEarningsRule` para que lean
        `constitution.yaml` igual que las demás reglas, en vez de
        tener umbrales hardcodeados.
-   [ ] Construir `ConstitutionEngine` real conectado al flujo.
-   [x] Resolver los errores de `mypy` (0 errores, bajó de 20; incluyó
        eliminar 5 ficheros de código muerto).
-   [x] Confirmar el comportamiento de datos de IBKR con el mercado
        US abierto — validado en múltiples sesiones reales (AAPL,
        ACN, DRAM, SAN, ITX), en US y Europa.

## Fase 2

-   Sistema completo de scoring.
-   IV Rank.
-   Open Interest.
-   Probability of Assignment.
-   Filtros avanzados.

## Fase 3

-   Persistencia.
-   Watchlists.
-   Historial.

## Fase 4

-   Interfaz gráfica.
-   Dashboard.
-   Automatización.

------------------------------------------------------------------------

# Reglas de desarrollo

1.  Nunca romper la compilación.
2.  Todo cambio debe dejar el proyecto funcionando (`uv run pytest`
    en verde).
3.  Todo cambio debe incluir tests.
4.  Separar cálculos de reglas de negocio.
5.  Un modelo = una responsabilidad.
6.  Toda funcionalidad nueva debe incluir pruebas automáticas.
7.  Cada vez que se añada, modifique o elimine una funcionalidad
    importante, este README debe actualizarse en el mismo cambio.
8.  Ante cualquier duda de diseño, se pregunta antes de decidir.

Antes de considerar un cambio terminado:

``` bash
uv run pytest
uv run ruff check .
uv run mypy app
uv run python -m app.main AAPL   # validación manual en local, con IBKR corriendo
```

------------------------------------------------------------------------

# Visión a largo plazo

Aegis debe convertirse en un asistente integral para el inversor. No
solo debe indicar qué opción vender, sino explicar por qué, cuantificar
el riesgo, comparar alternativas y validar que cada decisión cumple las
reglas definidas por el usuario. La prioridad es construir una base
sólida, mantenible y respaldada por pruebas automáticas.

------------------------------------------------------------------------

# Cómo retomar el proyecto en una conversación nueva con Claude

Si esta conversación llega a su límite o simplemente abres una sesión
nueva, usa este mensaje inicial para que Claude se ponga al día
inmediatamente sin perder contexto:

---

> Estoy trabajando en Aegis, mi plataforma de análisis de opciones CSP
> en Python. El repo es `diegogh33/Aegis`, rama `fuckyouchatgpt`. Lee
> el README actualizado para ponerte al día del estado actual del
> proyecto — está en la sección 'Lo que funciona hoy'. También tengo
> mis notas en el fichero de memoria de esta cuenta. Quiero continuar
> desde donde lo dejamos.

---

Claude leerá el README (sección "Lo que funciona hoy"), consultará la
memoria de la cuenta donde está el contexto de Aegis, y estará listo
para continuar sin que tengas que re-explicar nada.

## Pendientes al cierre de la última sesión (22-jul-2026)

-   **Recordar siempre probar con mercado US abierto (15:30-22:00
    Madrid) antes de dar algo por resuelto** — Diego lo pidió
    explícitamente y sigue vigente.
-   IVRankRule acumulando histórico — 90 días por ticker para que
    empiece a filtrar de verdad. No hay nada que hacer, se acumula
    solo con el uso normal.

### Todo validado con mercado abierto el 22-jul

-   ✅ Timing por contrato: price 2.0s, greeks 0.0s, OI 0.0s en la
    mayoría. Solo strikes muy poco líquidos tardan hasta 4s en OI.
-   ✅ Open Interest llegando correctamente — `putOpenInterest` es el
    campo correcto para PUT individuales (no `openInterest`).
-   ✅ Multi-ticker tabla resumen con Bid/Ask/Delta/IV/Open Int reales.
-   ✅ `--pcs` funcionando: top 3 destacados, columnas Caída % y Δ
    Short. Confirmado con MU: $810/$800 y $820/$800 identificados
    correctamente como candidatos principales.
-   ✅ `scan-pcs s2` recorre el universo S2 y presenta candidatos PCS.
-   ✅ `watchlist --long-term` con filtro de precio y lista de exclusión.
-   ✅ `iv-history` mostrando 32 tickers acumulando desde 21-22 jul.

------------------------------------------------------------------------

# Último paso — Menú interactivo de terminal

Cuando la aplicación esté completa con toda la funcionalidad deseada,
el último paso será crear un **menú interactivo de terminal** que
centralice todos los comandos disponibles. En vez de recordar flags y
sintaxis, el usuario verá algo como:

```
═══════════════ AEGIS ═══════════════

  1. Análisis individual (PUT)
  2. Análisis PCS
  3. Raw chain (sin reglas)
  4. Watchlist ATLAS
  5. Scan PCS S2
  6. Scan PCS S3
  7. IV History

Selecciona opción: _
```

El menú pedirá el ticker y los parámetros necesarios para cada opción
y ejecutará el comando correspondiente. No requiere tecnología nueva —
es un script Python que envuelve los comandos existentes — y resuelve
el problema de tener que recordar la sintaxis exacta de cada comando.

**Este paso se implementa al final**, cuando ya no haya más
funcionalidad que añadir, para que el menú refleje el conjunto
completo y definitivo de opciones.
