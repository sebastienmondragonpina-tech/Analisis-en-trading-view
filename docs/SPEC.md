# PineScope Pro — Especificación / Contrato

Versión profesional del dashboard de la imagen de referencia (NVDA 4h con paneles
"Chris EstoB2 Master" y "Chris IA MC Master"). Este documento es el CONTRATO: todos
los indicadores Pine deben respetar exactamente estos nombres, marcos, reglas,
vocabulario de lecturas y el esquema JSON de salida para que encajen entre sí y con
el bridge de IA.

> Recordatorio duro: Pine Script v6 NO puede llamar a internet, NI a una IA, NI
> capturar la imagen del gráfico. Todo el análisis se calcula de forma NATIVA sobre
> los datos de TradingView. La IA se conecta POR FUERA: el indicador exporta un JSON
> completo vía `alert()` y un servidor externo (ai-bridge/) lo manda a la IA.

---

## 1. Inventario de la imagen (TODO esto debe existir)

### Panel A — Estocástico ("EstoB2")
Tabla resumen (2 filas) con columnas: **MARCO · TENDENCIA · MOTOR · CONFIRMACIÓN · SCORE · LECTURA**
- INTRADÍA · POSIBLE BAJISTA · 5m manda arriba · 15m/30m confirma caída · -1.5 · Buscar largos finos 1m/3m
- SWING · POSIBLE ALCISTA · 1H manda arriba · falta 2H/4H | Diario a favor · 2 · Swing alcista en desarrollo

Tabla multi-TF con columnas **TF · ESTADO · FUERZA** para: 1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, Diario.
Vocabulario de FUERZA visto: `BAJISTA`, `ALCISTA`, `BAJISTA FUERTE`, `VIGILAR BAJISTA`,
`INICIO ALCISTA`, `NACE BAJISTA`, `REBOTE DESDE VENTA`. ESTADO incluye `CRUCE ALCISTA` / `CRUCE BAJISTA`.

### Panel B — MACD ("MC")
Tabla resumen igual (MARCO·TENDENCIA·MOTOR·CONFIRMACIÓN·SCORE·LECTURA):
- INTRADÍA · POSIBLE ALCISTA · 5m manda arriba · falta 15m/30m · 1.25 · Buscar largos finos 1m/3m
- SWING · BAJISTA · 1H manda arriba · 2H/4H confirman caída | Diario en contra · -5.5 · Swing alcista en desarrollo

Tabla multi-TF con columnas **TF · HIST · ESTADO · FUERZA** (HIST = valor numérico del histograma, ej. -0.03, 0.23, -1.09).
Vocabulario de FUERZA: `IMPULSO ALCISTA SANO`, `IMPULSO BAJISTA SANO`, `PERDIENDO FUERZA`,
`RECUPERANDO FUERZA`, `VIGILAR CRUCE ALCISTA`, `VIGILAR CRUCE BAJISTA`.

### Gráfico
NVDA 4h, líneas de tendencia, niveles horizontales, etiqueta de precio actual, marcadores de eventos.

---

## 2. Temporalidades (orden fijo, 9 marcos)
`1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, Diario` → en Pine: `"1","3","5","15","30","60","120","240","D"`.
- Grupo **INTRADÍA** = {1m, 3m, 5m, 15m, 30m}
- Grupo **SWING** = {1H, 2H, 4H, Diario}

## 3. Indicadores base (calculados por marco vía request.security, lookahead OFF)
- EMA rápida 12, EMA lenta 26, SMA 200, RSI 14, ATR 14.
- MACD(12,26,9): macdLine, signalLine, hist = macdLine - signalLine.
- Estocástico: %K = ta.stoch(close,high,low,14) suavizado 3 (SMA 3); %D = SMA(%K,3).

## 4. Tabla Estocástico — reglas ESTADO + FUERZA
Por marco, con %K, %D y sus valores previos:
- **ESTADO**: si %K cruza por encima de %D este cierre → `CRUCE ALCISTA`; si cruza por debajo → `CRUCE BAJISTA`;
  si %K>%D → `ALCISTA`; si %K<%D → `BAJISTA`; iguales → `NEUTRAL`.
- **FUERZA** (prioridad de arriba abajo):
  1. %K<20 y subiendo y cruzó/recién cruzó → `REBOTE DESDE VENTA`
  2. cruce alcista reciente (≤2 barras) → `INICIO ALCISTA`
  3. cruce bajista reciente (≤2 barras) → `NACE BAJISTA`
  4. %K>%D pero la distancia se está cerrando (pendiente de %K < pendiente de %D) → `VIGILAR BAJISTA`
  5. %K<%D pero la distancia se está cerrando al alza → `VIGILAR ALCISTA`
  6. %K>80 → `SOBRECOMPRA`; %K<20 → `SOBREVENTA`
  7. |%K-%D| grande y a favor → `ALCISTA FUERTE` / `BAJISTA FUERTE`
  8. resto → `ALCISTA` / `BAJISTA`
- Color: alcista verde, bajista rojo, vigilar/cruce/sobre* ámbar.

## 5. Tabla MACD — reglas HIST + ESTADO + FUERZA
Por marco, con hist y hist previo:
- **HIST**: número formateado a 2 decimales (str.tostring(hist, "#.##")).
- **ESTADO**: hist>0 → `ALCISTA`; hist<0 → `BAJISTA`; 0 → `NEUTRAL`.
- **FUERZA** (lectura):
  - hist>0 y hist>hist[1] → `IMPULSO ALCISTA SANO`
  - hist>0 y hist<hist[1] → `PERDIENDO FUERZA`
  - hist<0 y hist<hist[1] → `IMPULSO BAJISTA SANO`
  - hist<0 y hist>hist[1] → `RECUPERANDO FUERZA`
  - |hist| muy pequeño (cerca de 0) y subiendo → `VIGILAR CRUCE ALCISTA`
  - |hist| muy pequeño y bajando → `VIGILAR CRUCE BAJISTA`
- Color igual criterio.

## 6. Tendencia unificada por TF (para el Dashboard overlay)
Score por marco [-4..+4] = sign(emaF-emaS) + sign(macdLine-signal) + sign(close-sma200) + rsiScore
(rsiScore: +1 si RSI>55, -1 si RSI<45, 0 si no). ESTADO: >0 ALCISTA, <0 BAJISTA, 0 NEUTRAL.
FUERZA: |score|>=3 FUERTE, ==0 EQUILIBRIO, resto normal.

## 7. Resumen táctico INTRADÍA / SWING (MARCO·TENDENCIA·MOTOR·CONFIRMACIÓN·SCORE·LECTURA)
Para cada grupo (intradía, swing):
- **SCORE** (float): suma ponderada de los marcos del grupo. Pesos sugeridos intradía {1m:0.5,3m:0.75,5m:1,15m:1.25,30m:1.5}, swing {1H:1,2H:1.25,4H:1.5,Diario:2}. Cada marco aporta peso × signo(score unificado del marco). Redondear a 2 decimales (da valores tipo -1.5, 2, 1.25, -5.5).
- **TENDENCIA**: score>umbralFuerte → `ALCISTA`; 0<score<=umbral → `POSIBLE ALCISTA`; simétrico para bajista; ~0 → `NEUTRAL`.
- **MOTOR**: el marco MÁS PEQUEÑO del grupo cuyo ESTADO coincide con el signo de la TENDENCIA (el que "manda"/inicia). Texto: "5m manda arriba" / "1H manda arriba" (arriba si alcista, abajo si bajista).
- **CONFIRMACIÓN**: texto dinámico que lista los marcos MAYORES del grupo que confirman o faltan respecto a la tendencia. Ej: "15m/30m confirma caída", "falta 2H/4H". Para SWING añade el estado del Diario: "Diario a favor" / "Diario en contra".
- **LECTURA**: frase accionable derivada de (tendencia, score, confirmación):
  - intradía alcista débil → "Buscar largos finos 1m/3m"; intradía bajista → "Buscar cortos finos 1m/3m" o "Esperar fin de caída".
  - swing alcista → "Swing alcista en desarrollo"; swing bajista → "Swing bajista en desarrollo / proteger".
  (Define un pequeño mapa de frases coherente; mantén el estilo de la imagen.)

## 8. Semáforo, Soportes/Resistencias, Predicción (en el Dashboard)
- **Semáforo** (verde / ámbar / rojo, como celda de color) a partir del score global (suma de los 9 marcos): >=+threshold verde, <=-threshold rojo, resto amarillo.
- **S/R** por pivotes (ta.pivothigh/low), invariante soporte < precio < resistencia, dibujados con líneas extendidas + etiqueta de precio.
- **Predicción por reglas** (sin IA): objetivoSube = precio + ATR×mult o la resistencia; objetivoBaja = precio - ATR×mult o el soporte. Etiqueta con aviso de que puede fallar.

## 9. Conexión IA — payload JSON del alert()
El **Dashboard** debe emitir (input "Emitir IA" + `alert(msg, alert.freq_once_per_bar_close)`) un JSON de UNA línea, construido con str.tostring/str.format, con TODO esto:
```
{"app":"PineScope","v":"2.0","secret":"PON_TU_SECRETO",
 "symbol":"{{ticker}}","price":<close>,"chartTF":"<timeframe.period>",
 "semaforo":"VERDE|AMARILLO|ROJO","scoreGlobal":<int>,
 "tf":{"1m":{...},"3m":{...},...,"Diario":{"trend":"ALCISTA","stochK":..,"stochEstado":"..","stochFuerza":"..","macdHist":..,"macdEstado":"..","macdFuerza":".."}},
 "intradia":{"tendencia":"..","motor":"5m","confirmacion":"..","score":-1.5,"lectura":".."},
 "swing":{"tendencia":"..","motor":"1H","confirmacion":"..","score":2,"lectura":".."},
 "niveles":{"soporte":..,"resistencia":..},
 "prediccion":{"objetivoSube":..,"objetivoBaja":..}}
```
El `secret` es un input.string del usuario (validado por el servidor). El servidor del
ai-bridge arma con esto un prompt de analista (método velas-japonesas) y lo manda a la IA.

## 10. Layout profesional + color (tema oscuro, legible)
- Colores: alcista `#26A69A`, bajista `#EF5350`, neutro/aviso `#E0A800`, fondo `#0E1117`,
  cabecera `#1b2230`, texto `#D1D4DC`, texto tenue `#8A93A2`. Celdas con `transp` para énfasis suave.
- Tablas: cabecera en negrita, filas alternadas sutiles, números monoespaciados (text_size acorde),
  posición configurable por input. Nada apretado: usa table.cell con padding visual via text_size y bgcolor.
- El Dashboard NO debe tapar el precio: tabla compacta arriba-derecha por defecto, input para moverla.

## 11. Archivos a producir
- `pine/PineScope_Dashboard.pine` (overlay=true): tabla matriz unificada por TF (ESTADO+FUERZA tendencia)
  + resumen táctico INTRADÍA/SWING (las 6 columnas) + semáforo + S/R + predicción + export JSON IA.
- `pine/PineScope_Stochastic.pine` (overlay=false): estocástico %K/%D dibujado + zonas 20/80 +
  tabla TF·ESTADO·FUERZA (sección 4) + su propio resumen INTRADÍA/SWING basado en estocástico.
- `pine/PineScope_MACD.pine` (overlay=false): histograma MACD coloreado + líneas MACD/señal +
  tabla TF·HIST·ESTADO·FUERZA (sección 5) + su resumen INTRADÍA/SWING basado en MACD.
- `pine/PineScope_Patterns.pine`: se mantiene (patrones de velas). No regenerar salvo ajuste menor.
- `ai-bridge/`: actualizar para parsear el JSON v2.0 completo y construir un prompt de analista profesional.
