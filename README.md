# PineScope

**El hermano nativo de TradingView de FinScope.**

PineScope es la version de tu analista financiero que **corre DENTRO de TradingView**.
No es una extension del navegador ni un programa que instalas: son **indicadores escritos
en Pine Script** (el lenguaje propio de TradingView) que pegas en el grafico y se quedan ahi,
dibujando tablas, semaforos, soportes/resistencias y patrones de velas directamente sobre el precio.

> En una frase: **FinScope** vive en tu navegador *encima* de la pagina;
> **PineScope** vive *dentro* de TradingView, como un indicador mas.

---

## Indice

1. [Que es PineScope](#1-que-es-pinescope)
2. [Que SI se porto y que NO se puede dentro de Pine](#2-que-si-se-porto-y-que-no-se-puede-dentro-de-pine)
3. [Los 3 indicadores](#3-los-3-indicadores)
4. [Conectar con IA](#4-conectar-con-ia)
5. [Como empezar (agregar a TradingView)](#5-como-empezar-agregar-a-tradingview)
6. [Estructura del proyecto](#6-estructura-del-proyecto)
7. [Aviso](#7-aviso)

---

## 1. Que es PineScope

FinScope es una **extension de Chrome** que se pone encima de cualquier pagina (incluido TradingView),
captura el grafico y los datos, calcula indicadores y le pide a una **IA** que escriba el analisis.

PineScope hace **lo mismo en cuanto a los calculos**, pero **sin salir de TradingView**:

- No se instala nada en el navegador.
- No depende de la pagina web ni de capturar imagenes.
- Los calculos corren en los **servidores de TradingView**, sobre los datos oficiales del grafico.
- Cualquiera puede usarlo: solo hay que **pegar el codigo** y darle a "Agregar al grafico".

La diferencia clave es **la IA y la vision**: eso FinScope si lo hace (porque vive en el navegador),
y PineScope **no puede hacerlo solo** (lo veremos en la tabla siguiente). Para eso existe la
carpeta `ai-bridge/`.

---

## 2. Que SI se porto y que NO se puede dentro de Pine

Pine Script es muy potente para **calcular sobre el precio**, pero tiene un limite duro:
**no puede llamar a internet ni a una IA**. Solo sabe trabajar con los datos del propio grafico
(precio, volumen, etc.) y, como mucho, **disparar una alerta**.

| Funcion de FinScope | Estado en PineScope | Detalle |
|---|---|---|
| Indicadores RSI / MACD / EMA / SMA / ATR | **SI** | Mismos calculos (RSI y ATR de Wilder, MACD 12/26/9, EMAs, SMA200). |
| Tabla multi-temporalidad (15m ... Mes) | **SI** | Una fila por marco con su estado y fuerza. |
| Semaforo verde / amarillo / rojo | **SI** | Resume la tendencia dominante y avisa de sobrecompra/sobreventa. |
| Soportes y resistencias | **SI** | Por pivotes (swing highs/lows), dibujados sobre el precio. |
| Patrones de velas japonesas | **SI** | Martillo, envolvente, doji, estrellas, harami... con filtro de contexto. |
| Prediccion por reglas (objetivo de subida/bajada) | **SI** | Con ATR + niveles de soporte/resistencia. Orientativa, **no** es IA. |
| **Analisis escrito por una IA** | **NO (dentro de Pine)** | Pine no puede llamar a Claude/OpenAI/Gemini. -> Se resuelve con `ai-bridge/`. |
| **Vision (leer el grafico como imagen)** | **NO (dentro de Pine)** | Pine no captura imagenes ni llama a un modelo de vision. -> FinScope si. |

**Resumen:** todo lo que es **calculo sobre el precio** se porto tal cual. Lo que **necesita internet o IA**
no cabe dentro de Pine; por eso hay un puente externo (`ai-bridge/`) y, como alternativa gratis, la
extension FinScope.

---

## 3. Los 3 indicadores

| Indicador | Archivo | Que hace en una linea |
|---|---|---|
| **PineScope Analyst** | `finscope/pine/PineScope_Analyst.pine` | El "cerebro": tabla multi-temporalidad, semaforo, veredicto, soportes/resistencias y prediccion por reglas, todo sobre el precio. |
| **PineScope Momentum** | `finscope/pine/PineScope_Momentum.pine` | El panel inferior de impulso: histograma MACD a 4 colores + RSI + tabla de momentum por temporalidad (1m ... Dia). |
| **PineScope Patterns** | `pine/PineScope_Patterns.pine` | Detecta patrones de velas japonesas y solo valida los que concuerdan con la tendencia y el nivel (S/R). |

Los tres son **independientes**: puedes agregar uno, dos o los tres al mismo grafico.

---

## 4. Conectar con IA

Como Pine no puede hablar con una IA, el truco es: el indicador **dispara una alerta** y esa alerta
manda los datos (en JSON) a un pequeno servidor que **si** llama a la IA y te devuelve el analisis.

- Ese servidor esta en la carpeta **`ai-bridge/`** (tiene version Node y version Python).
- La guia paso a paso para crear la alerta con webhook esta en
  **[COMO-AGREGAR-A-TRADINGVIEW.md](COMO-AGREGAR-A-TRADINGVIEW.md)**.

> Aviso importante: los **webhooks de TradingView suelen requerir un plan de pago**.
> Si no quieres pagar, la **alternativa 100% gratis** es la extension **FinScope**, que hace
> el analisis con IA gratis y sin servidores. Lo explica el README de `ai-bridge/`.

---

## 5. Como empezar (agregar a TradingView)

La guia completa con clics esta en **[COMO-AGREGAR-A-TRADINGVIEW.md](COMO-AGREGAR-A-TRADINGVIEW.md)**.
En resumen:

1. Abre TradingView y un grafico cualquiera.
2. Abajo, abre el **Pine Editor**.
3. **Pega** el contenido de un archivo `.pine`.
4. Pulsa **"Agregar al grafico"**.
5. Repite para los otros dos indicadores.

---

## 6. Estructura del proyecto

| Ruta | Que es |
|---|---|
| `finscope/pine/PineScope_Analyst.pine` | Indicador principal (tabla, semaforo, S/R, prediccion). |
| `finscope/pine/PineScope_Momentum.pine` | Panel de momentum (MACD + RSI + tabla). |
| `pine/PineScope_Patterns.pine` | Patrones de velas con filtro de contexto. |
| `ai-bridge/` | Servidor puente para conectar las alertas con una IA (Node y Python). |
| `ai-bridge/README.md` | Guia detallada del puente de IA. |
| `docs/research/` | Investigaciones sobre la conexion con IA (las escribe otro equipo). |
| `COMO-AGREGAR-A-TRADINGVIEW.md` | Pasos con clics para agregar, publicar y conectar con IA. |

---

## 7. Aviso

PineScope es una herramienta de **analisis educativo**. Los indicadores, semaforos y predicciones
**pueden fallar** y **no son una recomendacion** de compra o venta. Decide siempre por tu cuenta.
