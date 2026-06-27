# PineScope Pro

**El dashboard profesional de trading que vive DENTRO de TradingView.**

PineScope Pro es la version *nativa de TradingView* de FinScope: un **centro de mando
multi-temporalidad** que **replica y MEJORA** los paneles de la imagen de referencia
(NVDA 4h con los paneles "Chris EstoB2 Master" —estocastico— y "Chris IA MC Master" —MACD—),
pero reescrito 100% como **indicadores de Pine Script v6**.

No es una extension del navegador ni un programa que instalas. Son indicadores que
**copias y pegas** en TradingView y se quedan ahi: dibujan tablas, semaforos,
soportes/resistencias, niveles, patrones de velas y un resumen tactico de **9 marcos
temporales** directamente sobre tu grafico, calculados en los servidores de TradingView
sobre los datos oficiales del activo.

> En una frase: **FinScope** vive en tu navegador *encima* de la pagina y le da a la IA
> la **imagen** del grafico; **PineScope Pro** vive *dentro* de TradingView como un
> indicador mas y le da a la IA los **datos nativos exactos**.

---

## Indice

1. [Que es PineScope Pro](#1-que-es-pinescope-pro)
2. [Los 4 indicadores](#2-los-4-indicadores)
3. [Que SI es nativo vs. que necesita el bridge / la extension](#3-que-si-es-nativo-vs-que-necesita-el-bridge--la-extension)
4. [Conexion con IA](#4-conexion-con-ia)
5. [Como empezar (agregar a TradingView)](#5-como-empezar-agregar-a-tradingview)
6. [Estructura del proyecto](#6-estructura-del-proyecto)
7. [Aviso](#7-aviso)

---

## 1. Que es PineScope Pro

La imagen de referencia mostraba dos paneles separados (uno de estocastico, otro de MACD)
con tablas de tendencia, motor, confirmacion, score y lectura. PineScope Pro toma esa idea
y la lleva a un nivel profesional:

- **Multi-temporalidad real:** analiza **9 marcos a la vez** — `1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, Diario` —
  sin que tengas que cambiar de grafico.
- **Resumen tactico INTRADIA vs SWING:** separa los marcos cortos (intradia) de los largos
  (swing) y te dice, para cada grupo, la **tendencia**, el **motor** (el marco mas pequeno que
  inicia el movimiento), la **confirmacion** (que marcos mayores acompanan o faltan), un **score**
  numerico y una **lectura accionable**.
- **Semaforo y veredicto:** un // que resume la fuerza global y avisa de sobrecompra/sobreventa.
- **Soportes y resistencias por pivotes**, niveles, y una **prediccion por reglas** (objetivo de
  subida y de bajada con ATR + niveles). Todo orientativo, **nunca** una recomendacion.
- **Export de datos para IA:** el Dashboard puede emitir un **JSON v2.0** con TODO el estado
  calculado, listo para que un servidor externo se lo pase a una IA (ver seccion 4).

Todo esto corre sobre los **datos oficiales de TradingView**, sin instalar nada y sin depender
de capturar la pantalla.

---

## 2. Los 4 indicadores

Son cuatro indicadores **independientes**: puedes agregar uno, varios o los cuatro al mismo
grafico. El **Dashboard** es el "cerebro" y el unico que exporta el JSON para IA; los otros tres
son paneles especializados que reproducen y mejoran los de la imagen.

| Indicador | Archivo | Donde aparece | Que muestra |
|---|---|---|---|
| **Dashboard** (centro de mando) | `pine/PineScope_Dashboard.pine` | **Encima** del precio | Tabla **MATRIZ por marco** (TF / ESTADO / FUERZA de la tendencia unificada de los 9 marcos) · **resumen tactico INTRADIA y SWING** con las 6 columnas (MARCO · TENDENCIA · MOTOR · CONFIRMACION · SCORE · LECTURA) · **semaforo** // + veredicto · **soportes/resistencias** por pivotes · **prediccion por reglas** (objetivo sube/baja) · **export JSON v2.0 para IA**. |
| **Stochastic** (panel estocastico, "EstoB2") | `pine/PineScope_Stochastic.pine` | **Panel inferior** | %K / %D dibujados con zonas 20/80 · tabla **TF · ESTADO · FUERZA** de los 9 marcos, con el vocabulario de la imagen (`CRUCE ALCISTA/BAJISTA`, `REBOTE DESDE VENTA`, `INICIO ALCISTA`, `NACE BAJISTA`, `VIGILAR BAJISTA`, `SOBRECOMPRA/SOBREVENTA`...) · su propio resumen INTRADIA/SWING basado en el estocastico. |
| **MACD** (panel de momentum, "MC") | `pine/PineScope_MACD.pine` | **Panel inferior** | Histograma MACD a **4 colores** (positivo/negativo × creciente/decreciente) + lineas MACD y senal · tabla **TF · HIST · ESTADO · FUERZA** de los 9 marcos (HIST = valor numerico del histograma) con el vocabulario de la imagen (`IMPULSO ALCISTA/BAJISTA SANO`, `PERDIENDO FUERZA`, `RECUPERANDO FUERZA`, `VIGILAR CRUCE ALCISTA/BAJISTA`) · su resumen INTRADIA/SWING basado en el MACD. |
| **Patterns** (patrones de velas) | `pine/PineScope_Patterns.pine` | **Encima** del precio | Patrones de velas japonesas (martillo, envolvente, doji, estrellas, harami...) con **filtro de contexto** (Tendencia + Nivel): solo valida los patrones que concuerdan con la tendencia y el nivel de S/R; los aislados se atenuan. |

> Los nombres de archivo siguen el contrato de [`docs/SPEC.md`](docs/SPEC.md). El Dashboard y el
> panel Stochastic comparten exactamente el mismo motor de estocastico, y el Dashboard y el panel
> MACD comparten el mismo motor de MACD, para que las lecturas coincidan entre paneles.

---

## 3. Que SI es nativo vs. que necesita el bridge / la extension

Pine Script es potentisimo para **calcular sobre el precio**, pero tiene un limite duro:
**no puede llamar a internet, ni a una IA, ni capturar la imagen del grafico**. Solo trabaja con
los datos del propio grafico y, como mucho, **disparar una alerta**. Por eso conviene separar lo
que PineScope Pro hace **solo** (nativo) de lo que necesita ayuda externa:

| Capacidad | Estado | Quien lo hace |
|---|---|---|
| Indicadores RSI / MACD / EMA / SMA / ATR / Estocastico | **NATIVO** | Dashboard, Stochastic y MACD (calculo puro sobre OHLCV). |
| Analisis de **9 marcos** a la vez (1m...Diario) | **NATIVO** | `request.security` con lookahead OFF en los tres indicadores de tablas. |
| Tablas TF / ESTADO / FUERZA y resumen INTRADIA/SWING | **NATIVO** | Dashboard, Stochastic y MACD. |
| Semaforo // + veredicto | **NATIVO** | Dashboard. |
| Soportes/resistencias y prediccion por reglas | **NATIVO** | Dashboard (pivotes + ATR; orientativa, no es IA). |
| Patrones de velas con filtro de contexto | **NATIVO** | Patterns. |
| **Exportar todos los datos en un JSON v2.0** | **NATIVO** | Dashboard, via `alert()` (es solo el "puente de salida"). |
| **Mandar esos datos a una IA y recibir un analisis escrito** | **NECESITA el bridge** | Carpeta `ai-bridge/` (servidor externo: webhook → IA → Telegram). **Requiere plan de pago** de TradingView para usar webhooks. |
| **Que la IA VEA el grafico como imagen (vision)** | **NECESITA la extension** | La extension de Chrome **FinScope** captura la imagen y se la da a una IA con vision. Es la **alternativa gratis**, sin webhooks ni servidores. |
| **Que la IA redibuje/anote sobre TradingView** | **NO se puede** | Ninguna IA puede pintar sobre tu grafico de TradingView. Lo que se dibuja lo dibujan **los propios indicadores Pine** (tablas, lineas, etiquetas). |

**Resumen:** todo el **calculo** (incluido el paquete de datos para la IA) es **nativo**. Lo unico
que sale de TradingView es **mandar esos datos a la IA** (el `ai-bridge/`, de pago) o **darle la
imagen** (la extension FinScope, gratis).

---

## 4. Conexion con IA

El Dashboard ya calculo TODO sobre tu grafico. Para que una IA lo **interprete y escriba un
veredicto**, el truco es: el Dashboard **dispara una alerta** con un **JSON v2.0** que contiene
todos los datos nativos, y un servidor externo (`ai-bridge/`) se lo pasa a la IA y te devuelve la
respuesta (por ejemplo, a Telegram).

- El detalle completo del **modelo de analisis** (marcos, estocastico, MACD, scores, resumen
  intradia/swing) y de **como se conecta exactamente con la IA** (que lleva el JSON, el flujo
  webhook → bridge → IA → Telegram, y que puede y que NO puede hacer la IA) esta en
  **[docs/ANALISIS-Y-IA.md](docs/ANALISIS-Y-IA.md)**.
- Los pasos con clics para **crear la alerta con webhook** estan en
  **[COMO-AGREGAR-A-TRADINGVIEW.md](COMO-AGREGAR-A-TRADINGVIEW.md)**.
- La guia tecnica del servidor (montarlo, claves, exponerlo a internet) esta en
  **[ai-bridge/README.md](ai-bridge/README.md)**.

> **Aviso clave:** los **webhooks de TradingView casi siempre requieren un plan de pago**. Si no
> quieres pagar, la **alternativa 100% gratis** es la extension **FinScope** (`BMW/finscope/`), que
> hace el analisis con IA gratis y con un clic, dandole a la IA la **imagen** del grafico en lugar
> de los datos por webhook.

---

## 5. Como empezar (agregar a TradingView)

La guia completa, con clics y sin saber programar, esta en
**[COMO-AGREGAR-A-TRADINGVIEW.md](COMO-AGREGAR-A-TRADINGVIEW.md)**. En resumen:

1. Abre TradingView y entra a un grafico cualquiera.
2. Abajo, abre el **Pine Editor**.
3. **Pega** el contenido de un archivo `.pine` (borra antes el de ejemplo).
4. Pulsa **"Agregar al grafico"**.
5. Repite para los otros indicadores (puedes tener los cuatro a la vez).

---

## 6. Estructura del proyecto

| Ruta | Que es |
|---|---|
| `pine/PineScope_Dashboard.pine` | Centro de mando: matriz por marco + resumen tactico + semaforo + S/R + prediccion + export JSON IA. |
| `pine/PineScope_Stochastic.pine` | Panel estocastico (%K/%D + zonas + tabla TF/ESTADO/FUERZA + resumen). |
| `pine/PineScope_MACD.pine` | Panel MACD (histograma 4 colores + lineas + tabla TF/HIST/ESTADO/FUERZA + resumen). |
| `pine/PineScope_Patterns.pine` | Patrones de velas con filtro de contexto (Tendencia + Nivel). |
| `ai-bridge/` | Servidor puente para conectar las alertas con una IA (versiones Node y Python). |
| `ai-bridge/README.md` | Guia tecnica del puente de IA. |
| `docs/SPEC.md` | Contrato: nombres, marcos, reglas, vocabulario y esquema JSON que todo debe respetar. |
| `docs/ANALISIS-Y-IA.md` | Como funciona el modelo de analisis y como se conecta con la IA. |
| `docs/research/` | Investigaciones sobre webhooks, arquitecturas Pine→IA y alternativas gratis. |
| `COMO-AGREGAR-A-TRADINGVIEW.md` | Pasos con clics: agregar, publicar y crear la alerta-webhook. |

---

## 7. Aviso

PineScope Pro es una herramienta de **analisis educativo**. Los indicadores, semaforos, scores y
predicciones **pueden fallar** y **no son una recomendacion** de compra o venta. El analisis de la
IA es una opinion automatizada, no asesoramiento financiero. Decide siempre por tu cuenta y bajo tu
responsabilidad.
