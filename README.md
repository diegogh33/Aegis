# AEGIS

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

-   Estructura de paquetes Python correcta (todos los subpaquetes de
    `app/` tienen su `__init__.py`).
-   Suite de tests ejecutable: `uv run pytest` pasa en limpio (20
    tests).
-   Linting limpio: `uv run ruff check .` sin avisos.
-   `config/constitution.yaml` ya contiene toda la configuración de
    reglas (delta, earnings, liquidez, spread, premium, pesos de
    scoring) — la configuración va por delante del código que la
    consume.
-   **Sistema de reglas unificado.** Existía un segundo sistema de
    reglas en paralelo (`BaseRule`/`HardFilterEngine`), incompatible
    con el usado por `RuleEngine`/`Strategy`. Se ha eliminado y todo
    vive ahora sobre una única interfaz: `Rule` (`app/rules/base.py`)
    + `RuleResult`/`RuleStatus` (`app/core/`).
-   **`CashSecuredPutStrategy` conectada a `AnalysisService`.** Cada
    contrato recuperado de IBKR se evalúa contra la Constitution antes
    de puntuarse; los que no pasan (bloqueantes en `FAIL`) se
    descartan y no llegan al ranking final. Dos reglas bloqueantes
    activas por ahora:
    -   `CompanyApprovedRule` — lee `InvestmentThesis.approved`. **Hoy
        está hardcodeado a `True` en `AnalysisService`** porque no
        existe todavía una fuente de datos real de tesis de inversión
        conectada a este repo (ver limitaciones más abajo).
    -   `NoUpcomingEarningsRule` — descarta si hay earnings dentro del
        `minimum_days` configurado. `Company.next_earnings` tampoco
        se puebla desde ningún provider todavía, así que hoy siempre
        es `None` y la regla pasa por defecto.
-   **`MetricsEngine` y `OptionScoreEngine` reparados.** Antes de este
    commit, ambos estaban rotos de forma silenciosa: `MetricsEngine`
    construía un `OptionMetrics` con campos que no existían en el
    dataclass real (`TypeError` garantizado en cuanto se ejecutara), y
    `OptionScoreEngine.evaluate()` leía Greeks/volumen desde
    `OptionMetrics` en vez de desde `OptionContract` (donde realmente
    viven). Como nada tenía test, el bug llevaba tiempo sin
    detectarse — el flujo de scoring **nunca había podido ejecutarse
    con éxito** hasta ahora, a pesar de que el README anterior lo
    describía como "operativo".
-   `tests/conftest.py` centraliza los builders de `Company`,
    `OptionContract` e `InvestmentCandidate` para tests — evita
    duplicar fixtures en cada fichero de test.
-   `AnalysisService.analyze()` tiene test de integración con mocks
    (`tests/services/test_analysis_service.py`), cubriendo: scoring y
    ranking de contratos elegibles, rechazo por earnings próximos, y
    descarte de contratos sin `underlying_price`.
-   **CLI probado contra IBKR real por primera vez** (ticker AAPL).
    Destapó un segundo bug de ejecución: `MarketDataProvider` no
    trataba `NaN` como dato ausente (solo `None`/`-1`), así que un
    `NaN` de IBKR llegaba intacto hasta `LiquidityFilter` y explotaba
    con `decimal.InvalidOperation` al compararlo. Corregido con
    `_decimal_or_none()` en `app/providers/ibkr/market_data.py`, que
    normaliza `None`/`-1`/`NaN` a `None` de forma consistente. También
    se ha eliminado un bloque de `print()` de debug que ensuciaba la
    salida del CLI con el detalle de cada contrato.
-   **`underlying_price` con fallback al precio de la acción.**
    Con la suscripción de opciones bloqueada (error 10091), el
    `underlying_price` de cada opción individual llegaba siempre
    vacío, y `AnalysisService` descartaba silenciosamente el 100% de
    los contratos (`if underlying_price is None: continue`) — la
    tabla del CLI salía vacía sin ningún error visible. Ahora
    `IBKRProvider.get_underlying_price()` pide el precio de la propia
    acción (que normalmente sí tiene datos disponibles, a diferencia
    de sus opciones) una sola vez por análisis, y `OptionScanner` lo
    usa como valor de respaldo cuando el de la opción individual
    viene vacío.
-   **`DTERule` — tercera regla bloqueante de la Constitution.**
    Descarta contratos cuyo DTE (días hasta vencimiento) caiga fuera
    del rango `cash_secured_put.dte.min`/`max` de
    `config/constitution.yaml` (30–45 por defecto). A diferencia de
    `DeltaRule`/`NoUpcomingEarningsRule`, `DTERule` sí lee sus
    umbrales de `constitution.yaml` a través de `Settings` en vez de
    tenerlos hardcodeados — ver nota en limitaciones sobre esta
    inconsistencia.
-   **`DeltaRule` — cuarta regla, ahora también bloqueante.**
    Antes solo aportaba puntuación (`blocker = False`); ahora
    descarta candidatos cuyo delta caiga fuera del rango completo
    (`warning_min`/`pass_max`, -0.35/-0.15 por defecto) o venga
    ausente. Deliberadamente **no** bloquea el estado intermedio
    `WARNING` (delta algo más agresivo que el preferido, entre
    `warning_min` y `pass_min`): ese matiz de tolerancia con criterio
    ya existía en el diseño de la regla y se ha conservado — solo
    penaliza en score, no rechaza. Solo `FAIL` (fuera de rango del
    todo, o delta ausente) bloquea.
-   **`LiquidityRule` y `SpreadRule` — quinta y sexta regla
    bloqueante.** Sustituyen por completo al antiguo
    `LiquidityFilter` (servicio eliminado, ver más abajo). Ambas leen
    `constitution.yaml` (`cash_secured_put.liquidity` y
    `cash_secured_put.spread`) vía `Settings`, igual que `DTERule`.
    `LiquidityRule` comprueba volumen y open interest por separado
    (el `LiquidityFilter` antiguo nunca comprobaba open interest,
    pese a que `constitution.yaml` ya lo definía). Igual que
    `LiquidityFilter`, ambas tratan los datos ausentes como `PASS`,
    no como rechazo — necesario mientras IBKR no siempre devuelva
    bid/ask/volumen/open interest (ver limitaciones de datos).
-   **`LiquidityFilter` (servicio) eliminado.** Vivía en
    `OptionScanner`, fuera del `RuleEngine`, con umbrales
    hardcodeados que **no coincidían** con `constitution.yaml`
    (`minimum_volume=1` en el servicio vs. `50` en el YAML,
    `maximum_spread_pct=0.20` vs. `maximum_percent: 5` = 0.05, y
    nunca comprobaba `minimum_open_interest`). El filtrado de
    liquidez y spread ahora ocurre una sola vez, en un solo sitio, con
    los valores reales de la Constitution.
-   **Las 6 reglas de Constitution existentes ya leen
    `constitution.yaml` de forma consistente.** `DeltaRule` y
    `NoUpcomingEarningsRule` tenían sus umbrales hardcodeados en el
    constructor pese a que los mismos valores ya existían en el YAML
    (`delta.preferred`/`delta.warning`, `earnings.minimum_days`).
    Ahora ambas siguen el mismo patrón que `DTERule`/`LiquidityRule`/
    `SpreadRule`: leen `Settings` por defecto, con override explícito
    disponible en el constructor (usado en tests). Los valores por
    defecto no cambiaron — solo se volvieron editables desde el YAML
    sin tocar código.
-   **`mypy app` en limpio: 0 errores (bajó de 20).** Se encontraron
    5 ficheros de código muerto, nunca importados por nada del
    proyecto, que generaban la mitad de los errores:
    `app/providers/alphavantage/option_mapper.py` (mapper de opciones
    de AlphaVantage que ni siquiera coincidía con el modelo real de
    `OptionContract`), `app/selectors/option_selector.py` y
    `app/selectors/base.py` (un selector de opciones "temporal" ya
    reemplazado por `OptionScoreEngine`/`CashSecuredPutStrategy`),
    `app/criteria/base.py` y `app/core/criterion_report.py` (otro
    sistema de agregación de reglas en paralelo, nunca conectado a
    nada). Los paquetes `app/selectors/` y `app/criteria/`, ya
    vacíos, se eliminaron también. El resto de errores reales se
    corrigieron: `EvaluationReport.score` podía devolver `int(0)` en
    vez de `Decimal` cuando no había resultados (`sum()` sin `start`
    explícito); faltaban stubs de tipos para `yaml`
    (`types-PyYAML`, añadido a las dependencias de desarrollo); y
    `IBKRProvider` asumía sin comprobar que
    `qualifyContractsAsync()`/`ContractDetails.contract` siempre
    devolvían un `Contract` válido — ahora se valida explícitamente
    en runtime (`_as_single_contract()`), coincidiendo con lo que
    los stubs de `ib_async` ya declaraban como posible.
-   **Score de "Premium" eliminado — estaba sin implementar
    (`0.0` fijo) y duplicaba `annualized_return`.** Análisis previo
    (documento externo, revisado y confirmado) mostró que
    `Annualized Return = ROC × (365 / DTE)` — ambas métricas miden
    esencialmente la misma señal de rentabilidad, solo que una está
    anualizada y la otra no. Mantener las dos como componentes de
    score independientes habría duplicado el peso de la misma
    información. `ScoreResult` ya no tiene campo `premium`;
    `scoring.premium` se eliminó de `constitution.yaml` y sus 10
    puntos de peso se sumaron a `annualized_return` (35 → 45), para
    que el techo teórico del score total siga siendo 100
    (delta 30 + spread 15 + volume 10 + annualized_return 45). Nota:
    `cash_secured_put.premium.minimum_annualized_return` sigue
    existiendo en el YAML — es un umbral de filtro distinto, no
    relacionado con este score, y no se ha tocado.
-   **El CLI ya explica por qué la tabla de resultados sale vacía o
    incompleta, en vez de silencio total.** Antes, un contrato
    descartado (por falta de `underlying_price` o por fallar la
    Constitution) simplemente desaparecía sin dejar rastro — así fue
    como una tabla vacía por mercado cerrado se confundió al
    principio con un bug real. `AnalysisService.analyze()` ahora
    devuelve también `rejected: list[RejectedContract]` (contrato +
    motivo: `NO_UNDERLYING_PRICE`, o el `rule_id` de la regla de
    Constitution que bloqueó, ej. `DELTA`, `DTE`, `NO_EARNINGS`). El
    CLI muestra una tabla "Rejected Contracts" agrupada por motivo con
    conteo y un mensaje de ejemplo, y un aviso explícito si la tabla
    de candidatos queda vacía del todo.
-   **Soporte para tickers no estadounidenses** (`--currency`,
    `--exchange` en el CLI). Antes, `IBKRProvider` tenía
    `Stock(symbol, "SMART", "USD")` hardcodeado en dos sitios —
    cualquier ticker fuera de US habría fallado al cualificar el
    contrato. Ahora `exchange`/`currency` son parámetros configurables
    de extremo a extremo (`IBKRProvider` → `OptionScanner` →
    `AnalysisService.analyze()` → CLI), con `SMART`/`USD` como
    defaults para no romper el uso habitual. Probado en real con SAN
    (Banco Santander) vía `--currency EUR`: IBKR devolvió el exchange
    de opciones como **EUREX**, no MEFF como se había asumido en la
    documentación original — corregido aquí.
-   **Filtro de ventana de vencimientos al escanear la cadena de
    opciones (`scan.dte_window` en `constitution.yaml`, 20-60 días
    por defecto), en vez del límite arbitrario `[:2]` anterior.**
    Confirmado con datos reales: la cadena de SAN en EUREX tiene 19
    vencimientos disponibles, pero `get_put_contracts()` solo miraba
    los 2 más próximos cronológicamente (2 y 9 días) — muy por debajo
    del rango operativo real (`cash_secured_put.dte`, 30-45 días), así
    que todo se rechazaba siempre por DTE antes de llegar a ver algo
    útil. `scan.dte_window` es deliberadamente más ancho que
    `cash_secured_put.dte`: permite ver candidatos algo más lejanos
    si la ventana estricta de la Constitution no trae nada
    interesante (más prima a cambio de más plazo), sin gastar
    peticiones de mercado en vencimientos demasiado cortos. Si ningún
    vencimiento cae dentro de la ventana, cae de vuelta a los 2 más
    próximos en vez de devolver una lista vacía.
-   **Strikes seleccionados por cercanía al precio del subyacente
    (`scan.strikes_per_expiration`, 8 por defecto), no arbitrariamente.**
    Detectado probando SAN con el nuevo filtro de ventana de
    vencimientos: `OptionScanner` tenía un corte global
    `contracts[:10]` aplicado *después* de juntar los contratos de
    varios vencimientos — con un vencimiento cercano aportando ya 10+
    strikes, el corte se comía entero ese vencimiento y descartaba
    los otros dos sin que el usuario llegara a verlos. Ahora el límite
    se aplica por vencimiento, dentro de `IBKRProvider.get_put_contracts()`,
    seleccionando los `strikes_per_expiration` más cercanos al precio
    actual del subyacente (los relevantes para vender PUT con delta
    objetivo) en vez de tomar los primeros N tal como llegan de IBKR.
    El corte global `contracts[:10]` en `OptionScanner` se ha
    eliminado por quedar redundante. Con subyacentes muy líquidos
    (ej. MSFT, con decenas de strikes por vencimiento) este límite es
    lo que evita disparar el número de peticiones de market data.
-   **El CLI ya no revienta si Alpha Vantage no reconoce el ticker
    (confirmado con ITX: `KeyError: 'Symbol'` sin control).**
    `AlphaVantageMapper.company()` accedía a `data["Symbol"]`
    directamente; para tickers no reconocidos (típicamente no-US sin
    el sufijo de mercado correcto), Alpha Vantage devuelve un JSON
    vacío `{}` en vez de un error explícito, y eso tumbaba todo el
    CLI — incluida la parte de opciones, que es completamente
    independiente (IBKR) y no tiene motivo para fallar por esto.
    Ahora el mapper lanza `UnknownCompanyError` de forma controlada;
    `AnalysisService.analyze()` la captura y continúa con un
    `Company.unknown()` (placeholder) y `company_known=False` en el
    resultado; el CLI se salta la tabla "Company" y muestra un aviso
    explícito en su lugar, mientras la tabla de opciones sigue
    funcionando con normalidad.

## Lo que NO funciona todavía / limitaciones conocidas

-   **`AlphaVantageProvider` sigue sin adaptarse de verdad a tickers
    no estadounidenses** — ya no revienta (ver arriba), pero el
    símbolo se sigue enviando tal cual (ej. `ITX`), sin el sufijo de
    mercado que Alpha Vantage probablemente necesita (ej. `ITX.MC`
    para Madrid, sin confirmar el sufijo exacto). Con un ticker
    europeo sin ese sufijo, la tabla "Company" no aparecerá — la
    tabla de opciones (que solo depende de IBKR) sigue funcionando
    igual, son proveedores independientes.
-   **No hay fuente de datos real para `InvestmentThesis.approved`.**
    Se decide "a mano" con `approved=True` fijo en
    `AnalysisService.analyze()`. Falta decidir de dónde vendrá este
    dato en el futuro (¿tu biblioteca ATLAS vía algún fichero de
    configuración? ¿input manual por CLI?).
-   **`Company.next_earnings` no se puebla desde ningún provider.**
    `AlphaVantageMapper.company()` no lo asigna (el endpoint
    `OVERVIEW` no lo trae; probablemente haga falta
    `EARNINGS_CALENDAR`). Mientras tanto, `NoUpcomingEarningsRule`
    siempre pasa porque el dato es `None`.
-   Queda 1 regla bloqueante por implementar de las 7 que define
    `constitution.yaml`: `IVRankFilter` — bloqueado por falta de
    histórico de IV fiable (ninguno de los 3 proveedores de datos da
    IV Rank de forma consistente hoy, ver limitación más abajo).
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
    builders/
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
        ibkr/
    rules/
        base.py
        delta.py
        dte.py
        liquidity.py
        no_earnings.py
        spread.py
        company/
            company_approved_rule.py
    services/
        option_scanner.py
        analysis_service.py
    strategies/
    utils/

tests/
    conftest.py
    engines/
        test_metrics_engine.py
        test_option_score_engine.py
    providers/
        test_market_data.py
        test_dte_window.py
        test_closest_strikes.py
        test_alphavantage_mapper.py
    rules/
        test_delta_rule.py
        test_company_approved_rule.py
        test_no_earnings_rule.py
        test_dte_rule.py
        test_liquidity_rule.py
        test_spread_rule.py
    services/
        test_analysis_service.py
        test_option_scanner.py
    strategies/
        test_cash_secured_put.py
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

## Ejecutar el CLI contra datos reales

Requiere IBKR (TWS/Gateway) corriendo en `127.0.0.1:7496` y una API key
de Alpha Vantage configurada como variable de entorno.

``` bash
uv run python -m app.main AAPL
```

Para tickers no estadounidenses (ej. acciones españolas cotizando
opciones en MEFF), pasa `--currency`:

``` bash
uv run python -m app.main SAN --currency EUR
```

`--exchange` normalmente se deja en `SMART` (SmartRouting de IBKR
encuentra el mercado correcto solo); solo hace falta especificarlo si
necesitas forzar un enrutamiento concreto. Nota: `AlphaVantageProvider`
sigue usando el ticker tal cual para los datos fundamentales de la
empresa — si el símbolo necesita un sufijo distinto en AlphaVantage
para mercados no estadounidenses (ej. `SAN.MC`), eso no está resuelto
todavía; solo afecta a la tabla "Company", no a la de opciones.

Esto **no se puede validar en un entorno aislado sin conexión a IBKR**;
es la parte que cada colaborador debe probar en su propia máquina antes
de dar un cambio por terminado.

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
-   [ ] Conectar una fuente de datos real para
        `InvestmentThesis.approved` (hoy hardcodeado a `True`).
-   [ ] Poblar `Company.next_earnings` desde un provider real (hoy
        siempre `None`).
-   [x] `DTERule` implementada y conectada (lee de
        `constitution.yaml`).
-   [x] `DeltaRule` convertida en regla bloqueante (solo `FAIL`
        bloquea; `WARNING` sigue pasando con score reducido).
-   [x] `LiquidityRule` y `SpreadRule` implementadas y conectadas
        (leen de `constitution.yaml`); `LiquidityFilter` (servicio,
        con umbrales que no coincidían con el YAML) eliminado.
-   [ ] Implementar la regla de Constitution que falta (IVR —
        bloqueado por falta de histórico de IV fiable).
-   [x] Unificar `DeltaRule`/`NoUpcomingEarningsRule` para que lean
        `constitution.yaml` igual que las demás reglas, en vez de
        tener umbrales hardcodeados.
-   [ ] Construir `ConstitutionEngine` real conectado al flujo.
-   [x] Resolver los errores de `mypy` (0 errores, bajó de 20; incluyó
        eliminar 5 ficheros de código muerto).
-   [ ] Confirmar el comportamiento de datos de IBKR con el mercado
        US abierto (pendiente al cierre de esta sesión de trabajo).

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
