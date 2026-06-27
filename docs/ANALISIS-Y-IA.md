# PineScope Pro — El modelo de analisis y como se conecta con la IA

Este documento explica **dos cosas**:

1. **Como piensa PineScope Pro** (el modelo de analisis: los 9 marcos, el estocastico, el MACD, el
   resumen intradia/swing y los scores).
2. **Como se conecta exactamente con la IA**: el Dashboard exporta un **JSON v2.0** con todos los
   datos nativos → un **webhook** lo lleva al **ai-bridge** → el bridge se lo pasa a la **IA** → la
   IA responde y el resultado llega a **Telegram**.

Esta escrito para que se entienda **sin saber programar**, pero es preciso: lo que dice aqui es lo
que de verdad hace el codigo (ver el contrato en [SPEC.md](SPEC.md)).

---

## Indice

1. [La idea en una imagen](#1-la-idea-en-una-imagen)
2. [El modelo de analisis](#2-el-modelo-de-analisis)
   - [2.1 Los 9 marcos temporales](#21-los-9-marcos-temporales)
   - [2.2 Indicadores base por marco](#22-indicadores-base-por-marco)
   - [2.3 El estocastico (panel EstoB2)](#23-el-estocastico-panel-estob2)
   - [2.4 El MACD (panel MC)](#24-el-macd-panel-mc)
   - [2.5 Tendencia unificada y scores](#25-tendencia-unificada-y-scores)
   - [2.6 Resumen tactico INTRADIA / SWING](#26-resumen-tactico-intradia--swing)
   - [2.7 Semaforo, soportes/resistencias y prediccion](#27-semaforo-soportesresistencias-y-prediccion)
3. [Como se conecta con la IA (exacto)](#3-como-se-conecta-con-la-ia-exacto)
   - [3.1 El flujo de extremo a extremo](#31-el-flujo-de-extremo-a-extremo)
   - [3.2 El JSON v2.0: que datos viajan](#32-el-json-v20-que-datos-viajan)
   - [3.3 Que hace el ai-bridge con esos datos](#33-que-hace-el-ai-bridge-con-esos-datos)
4. [Honestidad: que SI y que NO puede la IA](#4-honestidad-que-si-y-que-no-puede-la-ia)
5. [Aviso](#5-aviso)

---

## 1. La idea en una imagen

```
   TradingView (datos oficiales del activo)
            │
            ▼
   ┌──────────────────────────────┐
   │   PineScope Pro (Pine v6)    │   Calcula TODO de forma NATIVA:
   │   Dashboard + Stochastic +   │   9 marcos, estocastico, MACD,
   │   MACD + Patterns            │   tendencia, scores, S/R, prediccion.
   └──────────────┬──────────────┘
                  │  El Dashboard EXPORTA un JSON v2.0 (todos los datos)
                  │  via alert()  ──────►  Alerta-webhook (TradingView)
                  │                                         │ webhook (JSON)
                  ▼                                         ▼
        Las tablas/lineas/etiquetas              ai-bridge (server.js / server.py)
        se dibujan en TU grafico                          │ arma un prompt de analista
        (eso lo hacen los indicadores,                    ▼
         NO la IA)                                IA (Claude / OpenAI / Gemini)
                                                          │ veredicto + plan + riesgo
                                                          ▼
                                                       Telegram (tu movil)
```

La clave: **el calculo es nativo** (lo hace Pine dentro de TradingView). La IA entra **al final**,
solo para **interpretar** los datos ya calculados y escribir un veredicto. La IA **no** dibuja nada
en tu grafico.

---

## 2. El modelo de analisis

### 2.1 Los 9 marcos temporales

PineScope Pro analiza **9 temporalidades a la vez**, en un orden fijo:

`1m · 3m · 5m · 15m · 30m · 1H · 2H · 4H · Diario`

y las agrupa en dos bloques:

- **INTRADIA** = {1m, 3m, 5m, 15m, 30m} — el corto plazo, para operar el dia.
- **SWING** = {1H, 2H, 4H, Diario} — el plazo medio, para mantener dias/semanas.

Tecnicamente, cada marco se calcula con `request.security` (con *lookahead OFF*, es decir, **sin
hacer trampa mirando el futuro**), asi que ves el estado real de cada temporalidad sin cambiar de
grafico.

### 2.2 Indicadores base por marco

En **cada** uno de los 9 marcos se calculan los mismos indicadores (los mismos que usa FinScope):

- **EMA rapida (12)** y **EMA lenta (26)** → cruce de medias.
- **SMA 200** → estructura de largo plazo (precio por encima/por debajo).
- **RSI (14)** de Wilder → impulso.
- **ATR (14)** de Wilder → volatilidad (para los objetivos de la prediccion).
- **MACD (12, 26, 9)** → linea, senal e **histograma** (= linea − senal).
- **Estocastico** → %K = `stoch(14)` suavizado 3, %D = SMA(%K, 3).

### 2.3 El estocastico (panel EstoB2)

Para cada marco, el estocastico produce dos lecturas (esto es lo que ves en el panel **Stochastic**
y dentro del Dashboard):

- **ESTADO**: `CRUCE ALCISTA` si %K acaba de cruzar por encima de %D; `CRUCE BAJISTA` si cruza por
  debajo; si no hay cruce, `ALCISTA` (%K>%D) o `BAJISTA` (%K<%D).
- **FUERZA** (por prioridad, este es el "matiz" de la imagen):
  1. `REBOTE DESDE VENTA` — %K bajo (<20), subiendo y recien cruzado.
  2. `INICIO ALCISTA` / `NACE BAJISTA` — cruce reciente (≤2 velas).
  3. `VIGILAR BAJISTA` / `VIGILAR ALCISTA` — van a favor pero la distancia se cierra (puede girar).
  4. `SOBRECOMPRA` (%K>80) / `SOBREVENTA` (%K<20).
  5. `ALCISTA FUERTE` / `BAJISTA FUERTE` — separacion grande a favor.
  6. `ALCISTA` / `BAJISTA` — el caso normal.

### 2.4 El MACD (panel MC)

Para cada marco, a partir del **histograma** (HIST = linea − senal) y su valor previo:

- **HIST**: el numero del histograma (ej. `-0.03`, `0.23`, `-1.09`).
- **ESTADO**: `ALCISTA` si HIST>0, `BAJISTA` si HIST<0.
- **FUERZA** (la lectura de la imagen):
  - `IMPULSO ALCISTA SANO` — HIST>0 y creciendo.
  - `PERDIENDO FUERZA` — HIST>0 pero decreciendo.
  - `IMPULSO BAJISTA SANO` — HIST<0 y cayendo.
  - `RECUPERANDO FUERZA` — HIST<0 pero subiendo hacia cero.
  - `VIGILAR CRUCE ALCISTA` / `VIGILAR CRUCE BAJISTA` — HIST muy cerca de 0 y a punto de cruzar.

### 2.5 Tendencia unificada y scores

Para combinar todo en una sola lectura por marco, cada temporalidad recibe un **score unificado**
entre −4 y +4:

```
score = signo(EMA rapida − EMA lenta)     (+1 / −1)
      + signo(MACD − senal)               (+1 / −1)
      + signo(precio − SMA200)            (+1 / −1)
      + RSI    (+1 si RSI>55, −1 si RSI<45, 0 si en medio)
```

De ese score salen:

- **ESTADO**: `ALCISTA` (>0), `BAJISTA` (<0), `NEUTRAL` (0).
- **FUERZA**: `FUERTE` si |score|≥3, `EQUILIBRIO` si es 0, `NORMAL` en el resto.

Esto es lo que llena la tabla **MATRIZ** del Dashboard (una fila por marco: TF / ESTADO / FUERZA).

El **score global** es la suma de los 9 scores unificados; alimenta el semaforo.

### 2.6 Resumen tactico INTRADIA / SWING

Es la parte "pro" que reproduce las tablas de la imagen. Para **cada grupo** (intradia y swing) se
calcula una fila con **6 columnas**:

- **SCORE** (numero con decimales): suma ponderada de los marcos del grupo, donde los marcos mayores
  pesan mas. Intradia: `{1m:0.5, 3m:0.75, 5m:1, 15m:1.25, 30m:1.5}`. Swing: `{1H:1, 2H:1.25, 4H:1.5,
  Diario:2}`. Da valores tipo `-1.5`, `2`, `1.25`, `-5.5`.
- **TENDENCIA**: `ALCISTA` / `BAJISTA` si el score supera el umbral fuerte; `POSIBLE ALCISTA` /
  `POSIBLE BAJISTA` si es moderado; `NEUTRAL` si esta cerca de cero.
- **MOTOR**: el marco **mas pequeno** del grupo que ya va en la direccion de la tendencia (el que
  "inicia" el movimiento). Se muestra como `5m manda arriba`, `1H manda arriba`, etc.
- **CONFIRMACION**: que marcos **mayores** acompanan o faltan. Ej.: `15m/30m confirma caida`,
  `falta 2H/4H`. En swing se anade el estado del Diario: `Diario a favor` / `Diario en contra`.
- **LECTURA**: una frase accionable derivada de lo anterior. Ej.: `Buscar largos finos 1m/3m`,
  `Esperar fin de caida`, `Swing alcista en desarrollo`, `Swing bajista en desarrollo / proteger`.

Cada panel (Dashboard, Stochastic, MACD) calcula **su propio** resumen intradia/swing con la misma
estructura, pero basado en su indicador (tendencia unificada en el Dashboard, estocastico en
Stochastic, momentum MACD en MACD). Asi puedes comparar "que dice cada motor".

### 2.7 Semaforo, soportes/resistencias y prediccion

Solo el **Dashboard** anade la capa de decision:

- **Semaforo** (verde / ambar / rojo, mostrado como **celda de color**, sin emojis) a partir del score global: verde si supera +umbral, rojo si baja de −umbral,
  amarillo en medio. Acompanado de un **veredicto** (con matiz de sobrecompra/sobreventa por RSI).
- **Soportes / Resistencias** por **pivotes** (swing highs/lows), respetando siempre la invariante
  *soporte < precio < resistencia*; se dibujan como lineas extendidas con su etiqueta de precio.
- **Prediccion por reglas** (no es IA): `objetivoSube` = la resistencia o `precio + ATR×mult`;
  `objetivoBaja` = el soporte o `precio − ATR×mult`. Lleva siempre el aviso de que **puede fallar**.

---

## 3. Como se conecta con la IA (exacto)

### 3.1 El flujo de extremo a extremo

1. **El Dashboard calcula** todo lo anterior de forma nativa, vela a vela.
2. Si activas el input **"Emitir IA (webhook)"**, al **cierre de cada vela** el Dashboard ejecuta
   `alert(...)` con un **JSON v2.0 de una sola linea** que contiene **todos** los datos.
3. Una **alerta con webhook** en TradingView (condicion *"Any alert() function call"*) envia ese JSON
   a la URL de tu servidor **ai-bridge**.
4. El **ai-bridge** valida un **secreto** (para que nadie mas lo use), arma un **prompt de analista
   profesional** con esos datos y se lo manda a la **IA** (Claude / OpenAI / Gemini, el que
   configures).
5. La **IA responde** un analisis breve en espanol (veredicto + plan + gestion de riesgo).
6. El servidor **reenvia ese texto a Telegram**, a tu movil.

> **Detalle tecnico (limite de 3 s):** TradingView corta el webhook si tarda mas de ~3 segundos. Por
> eso el ai-bridge **responde 200 al instante** y hace el trabajo lento (IA + Telegram) **aparte**.
> Asi no se pierde ninguna alerta. Los pasos con clics para crear esta alerta estan en
> [../COMO-AGREGAR-A-TRADINGVIEW.md](../COMO-AGREGAR-A-TRADINGVIEW.md), y el montaje del servidor en
> [../ai-bridge/README.md](../ai-bridge/README.md).

### 3.2 El JSON v2.0: que datos viajan

El Dashboard **no manda una foto**. Manda los **numeros exactos** que describen el grafico. Asi es el
paquete (resumido):

```json
{
  "app": "PineScope", "v": "2.0", "secret": "TU_SECRETO",
  "symbol": "NVDA", "price": 123.45, "chartTF": "240",
  "semaforo": "ROJO", "scoreGlobal": -4,
  "tf": {
    "1m":     {"trend":"BAJISTA","stochK":18,"stochEstado":"BAJISTA","stochFuerza":"SOBREVENTA","macdHist":-0.03,"macdEstado":"BAJISTA","macdFuerza":"RECUPERANDO FUERZA"},
    "...":    {},
    "Diario": {"trend":"ALCISTA","stochK":62,"stochEstado":"ALCISTA","stochFuerza":"ALCISTA","macdHist":0.23,"macdEstado":"ALCISTA","macdFuerza":"IMPULSO ALCISTA SANO"}
  },
  "intradia": {"tendencia":"POSIBLE BAJISTA","motor":"5m","confirmacion":"15m/30m confirma caida","score":-1.5,"lectura":"Buscar largos finos 1m/3m"},
  "swing":    {"tendencia":"POSIBLE ALCISTA","motor":"1H","confirmacion":"falta 2H/4H | Diario a favor","score":2,"lectura":"Swing alcista en desarrollo"},
  "niveles":     {"soporte":118.0, "resistencia":131.5},
  "prediccion":  {"objetivoSube":131.5, "objetivoBaja":118.0}
}
```

Es decir, la IA recibe: el **simbolo y precio**, el **marco del grafico**, el **semaforo** y el
**score global**, el bloque **`tf`** con la tendencia + estocastico (ESTADO/FUERZA/%K) + MACD
(HIST/ESTADO/FUERZA) **de los 9 marcos**, los **resumenes intradia y swing** (con su motor y
confirmacion), los **niveles** de S/R y la **prediccion** por reglas. El `secret` lo valida el
servidor. El esquema exacto esta en la seccion 9 de [SPEC.md](SPEC.md).

### 3.3 Que hace el ai-bridge con esos datos

El servidor no le pasa el JSON crudo a la IA: primero lo **ordena en un briefing** (tabla por marco
+ resumen intradia/swing + niveles + prediccion) y **detecta divergencias** importantes (por
ejemplo, "intradia alcista contra swing bajista", o "el Diario va en contra del swing"). Con eso
construye un prompt de **analista profesional** que usa el metodo de **velas japonesas** (Tendencia +
Nivel + Senal) y pide a la IA un **veredicto accionable + gestion de riesgo**, no un texto vago. El
resultado es lo que te llega a Telegram.

---

## 4. Honestidad: que SI y que NO puede la IA

Para no vender humo, conviene ser claros sobre los limites reales:

- **La IA recibe los datos NATIVOS exactos** (no pixeles). El Dashboard ya calculo tendencia,
  estocastico y MACD de los 9 marcos con precision; la IA no tiene que "adivinar mirando una foto".
  En la practica, esto suele dar un analisis **mas fiable** que partir de una imagen, porque los
  numeros son exactos y completos.
- **"Ver la grafica" como imagen es cosa de la extension FinScope**, no de este puente. Si quieres
  que una IA **mire los pixeles** del grafico (como haria una persona), eso lo hace **FinScope**
  (`BMW/finscope/`), que captura la pantalla y se la da a una IA con vision. PineScope Pro + ai-bridge
  trabajan con **datos**, no con imagenes.
- **La IA NO puede redibujar ni anotar sobre TradingView.** Ninguna IA pinta lineas, flechas o
  etiquetas en tu grafico. **Todo lo que ves dibujado lo dibujan los propios indicadores Pine**
  (las tablas, los soportes/resistencias, las etiquetas de prediccion y de patrones). La IA solo
  devuelve **texto** (a Telegram); no toca el grafico.
- **El puente con IA por webhook requiere plan de pago** de TradingView. La alternativa **gratis**
  es FinScope (un clic, sin servidores), a cambio de que la IA trabaje con la **imagen** en vez de
  con los datos nativos.

En resumen: **el calculo es nativo y exacto; la IA solo interpreta y escribe; el dibujo lo hacen los
indicadores; y ver la imagen es cosa de FinScope.**

---

## 5. Aviso

Todo esto es **analisis educativo**. Los indicadores, scores, semaforos, predicciones y el texto que
escriba la IA **pueden fallar** y **no son una recomendacion** de compra o venta. La IA produce una
opinion automatizada, no asesoramiento financiero. Decide siempre por tu cuenta y bajo tu
responsabilidad.
