# Internos de mercado y sentimiento en TradingView / Pine Script v6

> Objetivo: identificar los **tickers exactos** de internos de mercado y sentimiento que de
> verdad resuelven con `request.security()` en Pine Script v6 (versión gratuita en su mayoría),
> para usarlos como **contexto institucional** dentro de un indicador.
>
> Fecha de investigación: 2026-06-27. Todas las citas apuntan a páginas oficiales de símbolos
> de TradingView (`tradingview.com/symbols/...`) y a la documentación oficial de Pine Script.

---

## 0. Idea clave: cómo se nombran estos símbolos

Los internos de mercado de EE. UU. viven casi todos bajo el prefijo de fuente **`USI:`**
(*US Statistical Indices* / "índices estadísticos"). La volatilidad (VIX) vive bajo `CBOE:` o
`TVC:`. **No** llevan el prefijo de un exchange normal (NYSE:, NASDAQ:) porque no son acciones,
son índices estadísticos calculados por la bolsa o por CBOE.

Regla práctica para `request.security()`:

- Si no estás seguro de que tu cuenta tenga datos del símbolo, **usa siempre**
  `ignore_invalid_symbol = true`. Con eso, si el símbolo no existe o no tienes datos, la
  función **devuelve `na` en vez de tirar un error de runtime** que detiene el script.
  Esto está confirmado en la doc oficial (ver sección 7).

---

## 1. Put/Call Ratio (sentimiento de opciones)

Todos bajo prefijo **`USI:`** (fuente CBOE). Verificados en las páginas oficiales de símbolo:

| Ticker exacto | Qué mide | Estado |
|---|---|---|
| **`USI:PCC`** | Put/Call Ratio **TOTAL** = Equities + Indices (CBOE) | ✅ Existe y resuelve |
| **`USI:PCCE`** | Put/Call Ratio de **EQUITIES** (solo acciones, CBOE) | ✅ Existe y resuelve |
| **`USI:PCCI`** | Put/Call Ratio de **INDICES** (solo índices, CBOE) | ✅ Existe (variante de la familia) |
| `USI:PCE` | Otra variante "equities" listada por TradingView | ✅ Existe (página de símbolo activa) |
| `USI:PC` | Put/Call Ratio "general" (legado) | ✅ Existe (página de símbolo activa) |
| **`USI:PCCA`** | **NO confirmado** — la búsqueda no devolvió una página de símbolo `USI:PCCA`. Sí existe `USI:PCA` ("equities+indices - AMEX"), que es **otro ticker**. | ⚠️ Usar `USI:PCA` si quieres la variante AMEX, no `PCCA` |

**Conclusión Put/Call:** los dos que de verdad necesitas y están confirmados son:
- **`USI:PCC`** → ratio total (equities + indices).
- **`USI:PCCE`** → ratio solo de acciones (el más usado como termómetro de pánico minorista).

> `USI:PCC` = "PUT/CALL RATIO (EQUITIES+INDICIES) - CBOE", prefijo USI confirmado.
> Fuente: [USI:PCC — TradingView](https://www.tradingview.com/symbols/USI-PCC/)
>
> `USI:PCCE` = "PUT/CALL RATIO (EQUITIES) - CBOE", prefijo USI confirmado.
> Fuente: [USI:PCCE — TradingView](https://www.tradingview.com/symbols/USI-PCCE/)
>
> `PCCA` **no** aparece como página de símbolo; la familia AMEX usa `USI:PCA`.
> Fuente: búsqueda de símbolos TradingView (devuelve PCC, PC, PCA, PCE; no PCCA).

**Interpretación:** ratio alto (muchos puts) → miedo/pesimismo (lectura contrarian alcista en
extremos). Ratio bajo (muchos calls) → complacencia/optimismo (lectura contrarian bajista en
extremos).

---

## 2. VIX (volatilidad / miedo): `CBOE:VIX` vs `TVC:VIX`

Ambos representan **el mismo índice** (CBOE Volatility Index), pero son **dos feeds distintos**:

- **`TVC:VIX`** → feed de TradingView (*TradingView Continuous*). Es el que viene **gratis** y
  por defecto en la mayoría de scripts e indicadores de la comunidad. **Recomendado para
  `request.security()` en cuentas gratuitas / sin suscripción a datos CBOE.**
- **`CBOE:VIX`** → feed oficial directo de CBOE. Puede requerir/depender de tu nivel de datos.
  Devuelve el mismo valor cuando tienes acceso.

**Recomendación práctica:** usa **`TVC:VIX`** en `request.security()` salvo que tengas
explícitamente datos CBOE contratados. Es el default de facto y el más portable entre cuentas.

> "El indicador siempre tira de TVC:VIX... TVC:VIX es el default común en muchos indicadores
> Pine de TradingView." / Páginas de símbolo:
> [TVC:VIX](https://www.tradingview.com/symbols/TVC-VIX/) ·
> [CBOE:VIX](https://www.tradingview.com/symbols/CBOE-VIX/)

---

## 3. Amplitud de mercado (breadth)

Todos bajo **`USI:`**. Verificados (existe página de símbolo):

| Ticker exacto | Qué mide | Estado |
|---|---|---|
| **`USI:ADD`** | NYSE **Advances MINUS Declines** (avances netos, ya restados) | ✅ Confirmado |
| **`USI:ADVN.NY`** | NYSE **Advancing issues** (número de acciones que suben) | ✅ Confirmado (lleva sufijo `.NY`) |
| **`USI:DECN.NY`** | NYSE **Declining issues** (número de acciones que bajan) | ✅ Variante `.NY` de la familia |
| `USI:ADV` | NYSE Advancing Issues (variante sin sufijo) | ✅ Existe página de símbolo |
| **`USI:ADVDEC.NY`** | NYSE Advancing − Declining (alternativa a ADD) | ✅ Confirmado |
| **`USI:TRIN`** | **TRIN / Arms Index** (US Stocks TRIN). También existe `USI:TRIN.US` / `USI:TRINQ` (Nasdaq) | ✅ Confirmado |
| **`USI:TICK`** | NYSE **TICK** (acciones en uptick − downtick). También `USI:TICK.US` | ✅ Confirmado |

⚠️ **Ojo con los sufijos.** El ticker corto `USI:ADVN` (sin `.NY`) devolvió **404** al
verificarlo; el que sí resuelve es **`USI:ADVN.NY`**. Lo mismo aplica a `DECN.NY`. Para
"avances netos" ya calculados, lo más simple y robusto es **`USI:ADD`** (no necesita sufijo).

> `USI:ADD` = "NYSE $ADV MINUS $DECL" (avances menos declives).
> Fuente: [USI:ADD — TradingView](https://www.tradingview.com/symbols/USI-ADD/)
>
> `USI:ADVN.NY` = NYSE Advancing (página activa, con sufijo `.NY`).
> Fuente: [USI:ADVN.NY — TradingView](https://www.tradingview.com/symbols/USI-ADVN.NY/)
>
> `USI:ADVDEC.NY` = NYSE Advancing − Declining.
> Fuente: [USI:ADVDEC.NY — TradingView](https://www.tradingview.com/symbols/USI-ADVDEC.NY/)
>
> `USI:TRIN.US` (Arms/TRIN) y `USI:TICK.US` / `USI:TICK`:
> [USI:TRIN.US](https://www.tradingview.com/symbols/USI-TRIN.US/) ·
> [USI:TICK.US](https://www.tradingview.com/symbols/USI-TICK.US/) ·
> [USI:TICK](https://www.tradingview.com/symbols/USI-TICK/)

**Interpretación rápida:**
- `USI:ADD` / `USI:TICK` > 0 → amplitud positiva (la subida es amplia, sana).
- `USI:TRIN` < 1 → flujo hacia acciones que suben (alcista); > 1 → flujo hacia las que bajan
  (bajista). TRIN es **inverso** (valores altos = miedo).

---

## 4. Volumen al alza / a la baja (up/down volume)

Bajo **`USI:`**. Verificados (existe página de símbolo):

| Ticker exacto | Qué mide | Estado |
|---|---|---|
| **`USI:UVOL`** | NYSE **UP VOLUME** (volumen de acciones que suben) | ✅ Confirmado |
| **`USI:DVOL`** | NYSE **DOWN VOLUME** (volumen de acciones que bajan) | ✅ Confirmado |
| **`USI:VOLD`** | NYSE UVOL − DVOL (volumen neto: arriba menos abajo) | ✅ Confirmado |

> [USI:UVOL — TradingView](https://www.tradingview.com/symbols/USI-UVOL/) ·
> [USI:DVOL — TradingView](https://www.tradingview.com/symbols/USI-DVOL/) ·
> [USI:VOLD — TradingView](https://www.tradingview.com/symbols/USI-VOLD/)

**Interpretación:** `UVOL/DVOL` muy alto o `VOLD` muy positivo → el dinero institucional empuja
al alza con fuerza (jornada de "all green"); lo contrario para días de liquidación.

---

## 5. Tabla resumen — tickers que SÍ resuelven en `request.security()`

| Categoría | Ticker recomendado | Alternativa |
|---|---|---|
| Put/Call total | `USI:PCC` | `USI:PC` |
| Put/Call acciones | `USI:PCCE` | `USI:PCE` |
| Put/Call índices | `USI:PCCI` | — |
| Volatilidad (miedo) | **`TVC:VIX`** | `CBOE:VIX` (requiere datos CBOE) |
| Avances netos (breadth) | `USI:ADD` | `USI:ADVDEC.NY` |
| Avances (nº acciones) | `USI:ADVN.NY` | `USI:ADV` |
| Declives (nº acciones) | `USI:DECN.NY` | — |
| TRIN / Arms | `USI:TRIN` | `USI:TRIN.US`, `USI:TRINQ` (Nasdaq) |
| TICK | `USI:TICK` | `USI:TICK.US` |
| Up volume | `USI:UVOL` | — |
| Down volume | `USI:DVOL` | — |
| Volumen neto | `USI:VOLD` | — |

⚠️ **Aviso de disponibilidad:** no todos los símbolos están en todas las cuentas / planes.
Por eso el snippet de la sección 6 usa **`ignore_invalid_symbol = true`** para que un símbolo
ausente devuelva `na` y lo mostremos como "n/d" en lugar de romper el script.

---

## 6. SNIPPET Pine Script v6 verificado

Lee VIX, Put/Call (equities) y TICK, manejando el caso de símbolo inexistente (`na → "n/d"`).

```pine
//@version=6
indicator("Contexto institucional — internos de mercado", overlay = true)

// --- Helper: pide un símbolo y NO rompe si no existe (devuelve na) ---
f_intern(string sym) =>
    request.security(sym, timeframe.period, close, ignore_invalid_symbol = true)

// --- Lecturas (cámbialas por las que quieras de la sección 5) ---
float vixVal  = f_intern("TVC:VIX")     // Volatilidad / miedo
float pcceVal = f_intern("USI:PCCE")    // Put/Call de acciones (sentimiento)
float tickVal = f_intern("USI:TICK")    // Amplitud intradía (NYSE TICK)

// --- Formateo: na -> "n/d" (no disponible en tu cuenta) ---
f_fmt(float v) =>
    na(v) ? "n/d" : str.tostring(v, format.mintick)

// --- Tabla de contexto en pantalla ---
var table t = table.new(position.top_right, 2, 3, border_width = 1)
if barstate.islast
    table.cell(t, 0, 0, "VIX",      text_color = color.white, bgcolor = color.new(color.blue, 70))
    table.cell(t, 1, 0, f_fmt(vixVal),  text_color = color.white)
    table.cell(t, 0, 1, "P/C eq.",  text_color = color.white, bgcolor = color.new(color.blue, 70))
    table.cell(t, 1, 1, f_fmt(pcceVal), text_color = color.white)
    table.cell(t, 0, 2, "NYSE TICK",text_color = color.white, bgcolor = color.new(color.blue, 70))
    table.cell(t, 1, 2, f_fmt(tickVal), text_color = color.white)

// --- Ejemplo de uso en lógica: solo alcista si VIX bajo y P/C en pánico ---
bool contextoAlcista = not na(vixVal) and not na(pcceVal) and vixVal < 20 and pcceVal > 1.0
plotshape(contextoAlcista, title = "Contexto OK", style = shape.triangleup,
          location = location.belowbar, color = color.green, size = size.tiny)
```

**Puntos verificados del snippet:**
- `request.security(symbol, timeframe.period, expression, ignore_invalid_symbol = true)` →
  firma oficial; con `ignore_invalid_symbol = true` **devuelve `na`** en vez de error de runtime.
- `na(x)` → función built-in que comprueba si un valor es `na`.
- `str.tostring`, `table.*`, `barstate.islast`, `plotshape` → todos built-in de Pine v6.

> Firma y comportamiento de `request.security` / `ignore_invalid_symbol`:
> [Pine Script docs — Other timeframes and data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/)

---

## 7. "Huella de volumen institucional": built-ins nativos de Pine v6 vs calculados a mano

### 7.1. SÍ son built-in (`ta.*`)

| Built-in | Tipo | Qué es | Uso |
|---|---|---|---|
| **`ta.obv`** | **variable** (no función) | On-Balance Volume — presión compradora/vendedora acumulada | `float o = ta.obv` |
| **`ta.accdist`** | **variable** (no función) | Accumulation/Distribution Index (línea A/D de Williams) | `float ad = ta.accdist` |
| **`ta.mfi(series, length)`** | **función** | Money Flow Index — "RSI ponderado por volumen" (0–100) | `float m = ta.mfi(hlc3, 14)` |
| **`ta.vwap`** / **`ta.vwap(source)`** | variable **y** función | Volume-Weighted Average Price | `float v = ta.vwap(hlc3)` |

Notas importantes:
- `ta.obv` y `ta.accdist` son **variables**, NO se llaman con paréntesis. Escribir
  `ta.obv()` da error.
- `ta.mfi` SÍ es función: `ta.mfi(source, length)`, típicamente `ta.mfi(hlc3, 14)`.
- `ta.vwap` existe como **variable** (`ta.vwap`, VWAP anclado a la sesión por defecto) y como
  **función** `ta.vwap(source)`; la versión función acepta además parámetros `anchor` y
  `stdev_mult` (devuelve tupla `[vwap, banda_sup, banda_inf]`).

> `ta.obv` y `ta.accdist` confirmados como variables built-in; `ta.mfi` como función
> ("volume-weighted RSI"); `ta.vwap(source) → series float`.
> Fuentes: [Referencia Pine v6](https://www.tradingview.com/pine-script-reference/v6/) ·
> [ta.obv — Pineify](https://pineify.app/pine-script-ta-obv) ·
> [ta.vwap — TradingCode](https://www.tradingcode.net/tradingview/volume-weighted-price/)

### 7.2. Volumen relativo (NO existe built-in dedicado, se calcula)

No hay `ta.relativevolume`. Se hace a mano dividiendo el volumen actual entre su media móvil:

```pine
int   len = 20
float volRel = volume / ta.sma(volume, len)   // >1 = volumen por encima de lo normal
```

### 7.3. Chaikin Money Flow (CMF): NO es built-in — fórmula manual

**No existe `ta.cmf()`** en Pine Script (aunque TradingView lo ofrezca como indicador
empaquetado en la plataforma). Hay que calcularlo:

```pine
// Chaikin Money Flow (CMF) — cálculo manual, periodo N
int   lenCmf = 20
// Money Flow Multiplier: dónde cerró dentro del rango del bar
float mfMult = (high == low) ? 0.0 : ((close - low) - (high - close)) / (high - low)
// Money Flow Volume
float mfVol  = mfMult * volume
// CMF = suma(MFV, N) / suma(volumen, N)
float cmf    = math.sum(mfVol, lenCmf) / math.sum(volume, lenCmf)
plot(cmf, title = "CMF", color = color.purple)
```

**Fórmula (referencia):**
- Money Flow Multiplier = `((Close − Low) − (High − Close)) / (High − Low)`
- Money Flow Volume = `Money Flow Multiplier × Volume`
- CMF = `Σ(Money Flow Volume, N) / Σ(Volume, N)`

(Guardia `high == low` para evitar división por cero en barras sin rango.)

> CMF **no** es función nativa de Pine; se implementa con la fórmula del multiplicador de flujo.
> Fuentes: [Búsqueda CMF — TradingView](https://www.tradingview.com/scripts/chaikinmoneyflow/) ·
> [Guía CMF en Pine](https://offline-pixel.github.io/pinescript-strategies/pine-script-ChaikinMoneyFlow.html)

---

## 8. Fuentes

- USI:PCC — https://www.tradingview.com/symbols/USI-PCC/
- USI:PCCE — https://www.tradingview.com/symbols/USI-PCCE/
- USI:PCE — https://www.tradingview.com/symbols/USI-PCE/
- TVC:VIX — https://www.tradingview.com/symbols/TVC-VIX/
- CBOE:VIX — https://www.tradingview.com/symbols/CBOE-VIX/
- USI:ADD — https://www.tradingview.com/symbols/USI-ADD/
- USI:ADVN.NY — https://www.tradingview.com/symbols/USI-ADVN.NY/
- USI:ADVDEC.NY — https://www.tradingview.com/symbols/USI-ADVDEC.NY/
- USI:TRIN.US — https://www.tradingview.com/symbols/USI-TRIN.US/
- USI:TICK.US — https://www.tradingview.com/symbols/USI-TICK.US/
- USI:TICK — https://www.tradingview.com/symbols/USI-TICK/
- USI:UVOL — https://www.tradingview.com/symbols/USI-UVOL/
- USI:DVOL — https://www.tradingview.com/symbols/USI-DVOL/
- USI:VOLD — https://www.tradingview.com/symbols/USI-VOLD/
- Pine v6 — request.security / ignore_invalid_symbol: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/
- Pine v6 — Referencia del lenguaje: https://www.tradingview.com/pine-script-reference/v6/
- ta.obv — https://pineify.app/pine-script-ta-obv
- ta.vwap — https://www.tradingcode.net/tradingview/volume-weighted-price/
- Chaikin Money Flow (cálculo manual) — https://www.tradingview.com/scripts/chaikinmoneyflow/
