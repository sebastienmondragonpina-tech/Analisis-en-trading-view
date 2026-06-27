# Posicionamiento institucional ("smart money") nativo y gratis en TradingView / Pine Script v6

> Investigación para añadir datos de posicionamiento institucional a un indicador, **sin pagar datos externos** y **sin salir de Pine Script**.
> Fecha: 2026-06-27.

---

## 0. Resumen ejecutivo (TL;DR)

- **Sí existe** una vía nativa y gratuita: la librería oficial **`LibraryCOT`** de TradingView, que expone los datos **COT (Commitment of Traders)** publicados semanalmente por la **CFTC** (regulador de futuros de EE. UU.).
- **Import actual:** `import TradingView/LibraryCOT/3 as cot` (la **versión 3** es la que migró a Pine v6 y añadió las "dynamic requests").
- **Cubre:** futuros, materias primas, índices bursátiles (vía sus futuros), divisas (vía futuros de divisa) y algún cripto con futuros CFTC.
- **NO cubre:** acciones individuales (NVDA, AAPL, TSLA...). No hay COT para una acción — la CFTC solo reporta **futuros**, no acciones.
- **Lo que Pine NO puede hacer NUNCA:** options flow, dark pool, trades del Congreso tipo Unusual Whales, o cualquier API externa. Pine corre en un **sandbox sin acceso a internet**: no hace peticiones HTTP de entrada.

---

## 1. ¿Qué es el COT y por qué es el "smart money" nativo de TradingView?

El **Commitment of Traders (COT)** es un informe **semanal** que publica la **Commodity Futures Trading Commission (CFTC)**, la agencia federal de EE. UU. que supervisa los mercados de derivados (futuros). El informe desglosa el **open interest** (posiciones abiertas) por **tipo de participante**:

- **Commercial (Comerciales / "hedgers"):** empresas que usan el futuro para **cubrir** su negocio real (ej. una aerolínea cubriendo combustible, una minera cubriendo oro). Es el dinero "informado" que opera por cobertura, no por especulación.
- **Non-commercial (No comerciales):** grandes especuladores, típicamente **fondos / hedge funds** ("large speculators"). Son los que suelen seguir tendencia.
- **Non-reportable:** pequeños traders por debajo del umbral de reporte.

> "Commitment of Traders (COT) data is tallied by the Commodity Futures Trading Commission (CFTC)... It is weekly data that provides traders with information about open interest for an asset."
> — [LibraryCOT by TradingView](https://www.tradingview.com/script/ysFf2OTq-LibraryCOT/)

TradingView ofrece **tres tipos de informe**, todos cubiertos por la librería:

| Tipo (`COTType`) | Categorías de participantes principales |
|------------------|------------------------------------------|
| **`"Legacy"`**        | Commercial, Noncommercial, Open Interest (el clásico para comerciales vs especuladores) |
| **`"Disaggregated"`** | Producer/Merchant, Swap Dealers, Managed Money, Other Reportables (commodities, más granular) |
| **`"Financial"`** (TFF) | Dealer, Asset Manager, Leveraged Funds, Other Reportables (índices, divisas, bonos) |

> Fuente de los tres tipos: [Commitments of Traders reports on TradingView](https://www.tradingview.com/blog/en/commitments-of-traders-reports-on-tradingview-29284/)

Para **comerciales (cobertura institucional) vs no-comerciales (grandes especuladores)** se usa el informe **`"Legacy"`**.

---

## 2. La librería oficial `LibraryCOT` — import y versión

### Import exacto (versión actual)

```pinescript
//@version=6
import TradingView/LibraryCOT/3 as cot
```

**Nota importante sobre el nombre:** el módulo se llama **`LibraryCOT`**, NO `COT`. En Pine, el nombre que va en el `import` es el **`title`** de la declaración `library()` del autor, no el slug de la URL. La URL del script es `ysFf2OTq-LibraryCOT`, y el título publicado es `LibraryCOT`. Por eso el import correcto es `TradingView/LibraryCOT/3` y **no** `TradingView/COT/3` (este último daría error de "library not found").

> Formato general del import: `import <username>/<libraryName>/<libraryVersion> [as <alias>]`
> Ejemplo oficial: `import PineCoders/AllTimeHighLow/1 as allTime`
> — [Pine Script Docs — Libraries](https://www.tradingview.com/pine-script-docs/concepts/libraries/)

> Ejemplo real de uso de versiones anteriores en código público: `import TradingView/LibraryCOT/2 as cot`
> (la v3 es idéntica en firma, ya migrada a Pine v6) — [LibraryCOT](https://www.tradingview.com/script/ysFf2OTq-LibraryCOT/)

### Por qué la v3 importa (Pine v6)

La gran novedad de la **versión 3 (Pine v6)** es que la librería ahora puede exportar una función que llama a `request.security()` por dentro. Antes (v2 y anteriores) las librerías **no podían** exportar funciones con llamadas `request.*()`; con las **"dynamic requests" de Pine v6** esa limitación desaparece:

> "Previously libraries could not export functions containing `request.*()` calls, but with dynamic requests in Pine Script v6, this limitation no longer applies, allowing the library to export the `requestCommitmentOfTraders()` function."
> — [Pine Script® v6 has landed](https://www.tradingview.com/blog/en/pine-script-v6-has-landed-48830/) / [LibraryCOT](https://www.tradingview.com/script/ysFf2OTq-LibraryCOT/)

Esto significa que con la v3 puedes pedir COT en **una sola línea** sin construir el ticker a mano.

---

## 3. Funciones que expone la librería

### 3.1 `requestCommitmentOfTraders()` — la principal (recomendada en v6)

Pide el dato COT directamente y devuelve un `float` (la serie).

```text
cot.requestCommitmentOfTraders(COTType, CFTCCode, includeOptions,
                               metricName, metricDirection, metricType) → series float
```

| Parámetro        | Tipo    | Qué es |
|------------------|---------|--------|
| `COTType`        | string  | `"Legacy"`, `"Disaggregated"` o `"Financial"` |
| `CFTCCode`       | string  | Código CFTC del mercado. Usa `cot.convertRootToCOTCode("Auto")` para **auto-detectar** según el símbolo del gráfico. |
| `includeOptions` | bool    | `true` = futuros + opciones; `false` = solo futuros |
| `metricName`     | string  | Ej. `"Open Interest"`, `"Commercial Positions"`, `"Noncommercial Positions"`, `"Traders Commercial"`, etc. |
| `metricDirection`| string  | `"Long"`, `"Short"`, `"Spreading"` o `"No direction"` |
| `metricType`     | string  | `"All"`, `"Old"` u `"Other"` |

Ejemplo oficial de llamada (Open Interest, informe Legacy, auto-detección):

```pinescript
float COTdataExample = cot.requestCommitmentOfTraders(
     COTType         = "Legacy",
     CFTCCode        = cot.convertRootToCOTCode("Auto"),
     includeOptions  = false,
     metricName      = "Open Interest",
     metricDirection = "No direction",
     metricType      = "All")
```
> — [LibraryCOT](https://www.tradingview.com/script/ysFf2OTq-LibraryCOT/)

### 3.2 `COTTickerid()` — construye el ticker (uso clásico con `request.security`)

Devuelve un **string** de ticker COT válido, que luego pasas a `request.security()`. Útil si quieres control total (p. ej. pedir el dato en otra `timeframe`).

```text
cot.COTTickerid(COTType, CFTCCode, includeOptions,
                metricName, metricDirection, metricType) → string
```
> "creates a valid TradingView ticker ID for a CFTC Commitment of Traders (COT) symbol... usable with `request.security()`". Lanza error si `CFTCCode` es vacío o `na`.
> — [LibraryCOT](https://www.tradingview.com/script/ysFf2OTq-LibraryCOT/)

### 3.3 `getCFTCCode()` / `convertRootToCOTCode()` — detección del código CFTC

- **`cot.convertRootToCOTCode("Auto")`** — devuelve el código CFTC correspondiente al **símbolo del gráfico actual** (auto-detección). Es la forma recomendada.
- **`cot.getCFTCCode(symbol)`** — devuelve el código CFTC de un símbolo dado; **lanza un runtime error si el símbolo no es un futuro soportado** (este es justo el comportamiento que delata que una acción no tiene COT).

> "the `getCFTCCode()` function now raising a runtime error for unsupported instruments"
> — [LibraryCOT, release notes](https://www.tradingview.com/script/ysFf2OTq-LibraryCOT/)

> Funciones auxiliares confirmadas: `currencyToCFTCCode(currency)` y `metricNameAndDirectionToTicker(metricName, metricDirection)`.

---

## 4. ¿Qué símbolos SÍ tienen COT y cuáles NO?

### SÍ tienen COT (porque cotizan como futuros regulados por la CFTC)

La regla es: **si el activo se negocia como futuro en una bolsa supervisada por la CFTC, tiene COT.**

> "The CFTC oversees derivative markets traded on different exchanges, so COT data is available for assets that can be traded on **CBOT, CME, NYMEX, COMEX, and ICEUS**."
> — [Commitments of Traders reports on TradingView](https://www.tradingview.com/blog/en/commitments-of-traders-reports-on-tradingview-29284/)

| Clase | Ejemplos con COT |
|-------|------------------|
| **Metales** | Oro (GC), Plata (SI), Cobre (HG), Platino, Paladio |
| **Energía** | WTI (CL), Brent, Gas Natural (NG), Gasolina RBOB, Heating Oil |
| **Granos / Softs** | Maíz, Trigo, Soja, Café, Cacao, Azúcar, Algodón |
| **Índices bursátiles** (vía futuro) | S&P 500 (ES), Nasdaq 100 (NQ), Dow, Russell 2000, VIX |
| **Divisas** (vía futuro de divisa) | EUR, GBP, JPY, CAD, AUD, NZD, CHF, MXN, DXY |

### NO tienen COT

- **Acciones individuales** (NVDA, AAPL, TSLA, etc.). **No existe COT para una acción** porque la CFTC reporta el mercado de **futuros**, no el de acciones.

> "Individual stocks like NVDA and AAPL do NOT have COT data... Since individual stocks are not traded on CFTC-regulated futures exchanges, they fall outside COT coverage."
> — [Commitments of Traders reports on TradingView](https://www.tradingview.com/blog/en/commitments-of-traders-reports-on-tradingview-29284/)

### Fallback recomendado para símbolos sin COT (p. ej. una acción)

1. **Detectar el caso y degradar con gracia.** Envuelve la petición para que, si `convertRootToCOTCode("Auto")` no encuentra código, el indicador no rompa el gráfico:

```pinescript
string cftc = cot.convertRootToCOTCode("Auto")
bool hasCOT = str.length(cftc) > 0
```

   (Recuerda: `getCFTCCode()` lanza error directamente; `convertRootToCOTCode` es más manejable. Aun así conviene proteger con `hasCOT`.)

2. **Para una acción concreta**, mapear al índice del que forma parte y mostrar el COT del **futuro del índice** como proxy de "riesgo institucional macro" (p. ej. para NVDA → COT del **E-mini Nasdaq 100 / NQ**, ya que NVDA es un peso pesado del Nasdaq). Esto **no es** posicionamiento sobre la acción, sino sobre su índice — hay que dejarlo claro al usuario en la UI del indicador.

3. **Si no hay índice razonable**, ocultar el panel COT y mostrar un aviso ("COT no disponible para este símbolo").

---

## 5. SNIPPET funcional (Pine v6): Comerciales vs No-comerciales y su cambio

Este indicador, en un panel separado, dibuja:
- **Posición neta de Commercial** (cobertura institucional) = Long − Short.
- **Posición neta de Non-commercial** (grandes especuladores) = Long − Short.
- El **cambio semanal** de la posición neta comercial (delta).

```pinescript
//@version=6
indicator("COT - Comerciales vs No Comerciales (neto)", overlay = false)

import TradingView/LibraryCOT/3 as cot

// --- Detección automática del código CFTC según el símbolo del gráfico ---
string cftc   = cot.convertRootToCOTCode("Auto")
bool   hasCOT = str.length(cftc) > 0

// --- Helper para pedir una métrica Legacy ---
requestLegacy(string metricName, string dir) =>
    cot.requestCommitmentOfTraders(
         COTType         = "Legacy",
         CFTCCode        = cftc,
         includeOptions  = false,
         metricName      = metricName,
         metricDirection = dir,
         metricType      = "All")

// --- Comerciales (hedgers / instituciones que cubren) ---
float commLong  = hasCOT ? requestLegacy("Commercial Positions", "Long")  : na
float commShort = hasCOT ? requestLegacy("Commercial Positions", "Short") : na
float commNet   = commLong - commShort

// --- No comerciales (grandes especuladores / fondos) ---
float ncLong  = hasCOT ? requestLegacy("Noncommercial Positions", "Long")  : na
float ncShort = hasCOT ? requestLegacy("Noncommercial Positions", "Short") : na
float ncNet   = ncLong - ncShort

// --- Cambio reciente (delta semana a semana) de la posición neta comercial ---
float commNetChange = commNet - commNet[1]

// --- Plot ---
plot(commNet, "Net Comerciales",      color = color.teal,   linewidth = 2)
plot(ncNet,   "Net No-comerciales",   color = color.orange, linewidth = 2)
hline(0, "Cero", color = color.gray, linestyle = hline.style_dotted)

// El cambio reciente como columnas (verde sube cobertura, rojo baja)
plot(commNetChange, "Δ Net Comerciales", color = commNetChange >= 0 ? color.new(color.teal, 40) : color.new(color.red, 40), style = plot.style_columns)

// Aviso si el símbolo no tiene COT (acciones individuales, etc.)
var table msg = table.new(position.top_right, 1, 1)
if barstate.islast and not hasCOT
    table.cell(msg, 0, 0, "Sin datos COT para este símbolo (¿es una acción?)", text_color = color.red, bgcolor = color.new(color.red, 85))
```

**Notas de uso:**
- Pon el gráfico en un símbolo con COT (ej. `ES1!`, `GC1!`, `CL1!`, `6E1!`) y un timeframe **diario o semanal** — el COT es semanal, no tiene sentido en intradía.
- Lectura: cuando los **comerciales** acumulan posición neta **larga** mientras los **especuladores** están muy cortos (o viceversa), suele señalar zonas de posible giro (la lógica clásica de "comerciales como contrapeso del sentimiento").
- `commNetChange` (las columnas) muestra el **flujo reciente**: si los comerciales están añadiendo cobertura larga esta semana, las columnas son positivas/teal.

---

## 6. ¿Puede Pine acceder a options flow, dark pool o trades del Congreso (tipo Unusual Whales)?

### Respuesta corta: **NO. Es imposible por diseño.**

Pine Script corre en un **entorno sandbox** que **no tiene acceso a internet**. **No existe ninguna función** en el lenguaje para hacer una petición HTTP de **entrada** a una API externa (Unusual Whales, una API de options flow, dark pool prints, datos del Congreso, etc.). Esto es una **decisión de seguridad** de TradingView, no un detalle que se pueda saltar con un truco.

> "Pine Script does not support HTTP requests, and direct HTTP requests from within a Pine Script script are not possible. This fundamental constraint is a security feature, preventing scripts from accessing arbitrary external resources... TradingView's scripting environment is sandboxed, meaning Pine Script can't directly fetch data from an external API like you would in Python or JavaScript."
> — [How to Make HTTP Requests in TradingView Pine Script? / Integrating Pine Script with External APIs](https://www.pinegen.ai/resources/pinegen-ai-blogs/integrating-pine-script-with-external-api)

> "Pine Script operates in a sandboxed environment with no direct access to external systems, filesystems, or network sockets... the language does not provide functions for making HTTP requests to arbitrary URLs (except for webhooks via alerts), opening network sockets, or interacting with local files."
> — [Documentación de seguridad de Pine / Trading Strategies Academy](https://www.tradingview.com/support/solutions/43000521061-i-want-to-know-more-about-the-security-of-my-pine-scripts/)

### El único "puente" hacia el exterior es de SALIDA, no de entrada

Lo único que Pine puede hacer respecto a internet es **disparar una alerta con webhook**: cuando se cumple una condición, TradingView envía un **POST HTTP saliente** a una URL tuya. Es **push, no pull**:

> "You can push data out of Pine Script via alerts, but not pull data in."
> — [Integrating Pine Script with External APIs](https://www.pinegen.ai/resources/pinegen-ai-blogs/integrating-pine-script-with-external-api)

Es decir: el flujo es Pine → (webhook) → tu servidor. **No** puedes hacer tu servidor → Pine. Por tanto, meter options flow / dark pool / Congreso **dentro** de un indicador de Pine es imposible.

### ¿De dónde SÍ saca datos Pine entonces?

Solo de las fuentes internas de TradingView, vía las funciones `request.*()`:
- `request.security()` / `request.security_lower_tf()` — otros símbolos/timeframes (incluido el ticker COT).
- `request.financial()` — fundamentales (FactSet) ya integrados en TradingView.
- `request.economic()`, `request.dividends()`, `request.splits()`, `request.earnings()`, etc.

Todas leen el **feed propio de TradingView**, nunca una API tuya o de terceros.
> — [Pine Script Docs — Other timeframes and data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/)

### Implicación práctica para tu proyecto

Si quieres options flow / dark pool / trades del Congreso, **no será dentro del indicador de Pine**. Las opciones reales son:
1. Consumir esas APIs **fuera** (en tu daemon Python / extensión Chrome) y mostrarlas aparte.
2. Usar el webhook de TradingView para **enviar** señales a tu sistema externo, que ahí sí combina con esos datos.

Dentro de TradingView/Pine, el "smart money" nativo y gratis disponible es **únicamente el COT**.

---

## 7. Fuentes

- [LibraryCOT by TradingView (librería oficial)](https://www.tradingview.com/script/ysFf2OTq-LibraryCOT/)
- [Commitments of Traders reports on TradingView (blog oficial)](https://www.tradingview.com/blog/en/commitments-of-traders-reports-on-tradingview-29284/)
- [Pine Script® v6 has landed (blog oficial — dynamic requests)](https://www.tradingview.com/blog/en/pine-script-v6-has-landed-48830/)
- [Pine Script Docs — Libraries (sintaxis del import)](https://www.tradingview.com/pine-script-docs/concepts/libraries/)
- [Pine Script Docs — Other timeframes and data (funciones request.*)](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/)
- [TradingView — Seguridad de Pine Scripts](https://www.tradingview.com/support/solutions/43000521061-i-want-to-know-more-about-the-security-of-my-pine-scripts/)
- [Integrating Pine Script with External APIs (confirma sandbox: push, not pull)](https://www.pinegen.ai/resources/pinegen-ai-blogs/integrating-pine-script-with-external-api)
- [Commitment of Traders (COT) — Indicators and Strategies (símbolos soportados)](https://www.tradingview.com/scripts/commitmentoftraders/)
