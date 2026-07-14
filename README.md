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

# Estado actual

La arquitectura ya está dividida entre:

-   CLI
-   Configuración
-   Modelos
-   Engines
-   Providers
-   Services

El proyecto utiliza `dataclasses`, tipado moderno y separación de
responsabilidades.

------------------------------------------------------------------------

# Arquitectura

``` text
app/

    cli/
    config/

    engines/
        metrics_engine.py
        option_score_engine.py

    models/
        company.py
        option_contract.py
        option_metrics.py
        scored_option.py
        score_result.py
        analysis_result.py

    providers/
        alphavantage/
        ibkr/

    services/
        option_scanner.py
        liquidity_filter.py
        analysis_service.py
```

------------------------------------------------------------------------

# Flujo actual

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

Información fundamental de la empresa.

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

Obtiene opciones, las enriquece con datos de mercado y aplica filtros.

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

------------------------------------------------------------------------

# Roadmap

## Fase 1 (Prioridad absoluta)

-   Finalizar la refactorización del dominio.
-   Unificar `OptionMetrics`, `MetricsEngine`, `OptionScoreEngine` y
    `AnalysisService`.
-   Estabilizar IBKR.
-   Conseguir que todos los tests pasen.

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

# Problemas detectados

1.  Refactorización incompleta del dominio.
2.  Integración con IBKR y datos delayed (`reqMarketDataType(3)`).
3.  Ausencia de una batería de tests.

------------------------------------------------------------------------

# Reglas de desarrollo

1.  Nunca romper la compilación.
2.  Todo cambio debe dejar el proyecto funcionando.
3.  Todo cambio debe incluir tests.
4.  Separar cálculos de reglas de negocio.
5.  Un modelo = una responsabilidad.
6.  Toda funcionalidad nueva debe incluir pruebas automáticas.

Antes de considerar un cambio terminado:

``` bash
uv run pytest
uv run python -m app.main AAPL
```

------------------------------------------------------------------------

# Visión a largo plazo

Aegis debe convertirse en un asistente integral para el inversor. No
solo debe indicar qué opción vender, sino explicar por qué, cuantificar
el riesgo, comparar alternativas y validar que cada decisión cumple las
reglas definidas por el usuario. La prioridad es construir una base
sólida, mantenible y respaldada por pruebas automáticas.
