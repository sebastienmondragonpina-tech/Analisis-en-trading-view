# PineScope — Puente de IA externa (AI Bridge) · JSON v2.0

Este pequeño servidor es el **puente** entre tu **Dashboard de PineScope** (el indicador de
TradingView) y una IA (Claude / OpenAI / Gemini), para que cuando salte una alerta te llegue
un **análisis profesional escrito** directo a **Telegram**.

> En una frase: *el Dashboard ya calculó TODO sobre el gráfico y te lo manda en un paquete de
> datos; este servidor le pregunta a la IA "¿qué significa y qué hago?" y te envía la respuesta
> al teléfono.*

---

## 1. La idea clave: la IA recibe los DATOS NATIVOS exactos (no una foto)

Aquí hay dos formas muy distintas de que "la IA entienda tu gráfico", y conviene no confundirlas:

- **Que la IA VEA la gráfica (una imagen):** eso lo hace la **extensión FinScope** (en
  `BMW/finscope/`). FinScope vive dentro del navegador, **captura el gráfico como foto** y se la
  manda a una IA con visión. La IA *mira los píxeles*, como una persona.
- **Que la IA reciba los DATOS NATIVOS (este puente):** el **Dashboard de PineScope** no manda
  una foto. Manda los **números exactos** que describen la gráfica: la tendencia, el estocástico
  y el MACD **de los 9 marcos temporales**, el resumen táctico de intradía y swing (con su motor
  y confirmación), los niveles de soporte/resistencia y la predicción. La IA no tiene que
  "adivinar mirando una imagen": ya tiene los datos calculados, precisos y al detalle.

Las dos comparten la misma "cabeza" (los mismos proveedores de IA y el mismo método de **velas
japonesas**), así que el estilo del análisis es coherente entre ambas. Simplemente, **FinScope
ve la imagen** y **este puente recibe los datos nativos exactos**.

---

## 2. El flujo nativo, paso a paso

```
┌─────────────────────────┐   alert() con JSON v2.0   ┌─────────────────────┐
│  Dashboard PineScope    │  (todos los datos nativos)│   Alerta-webhook     │
│  (indicador Pine v6)    │ ───────────────────────▶ │   en TradingView     │
│  calcula TODO el estado │                           └──────────┬───────────┘
└─────────────────────────┘                                      │ webhook (JSON)
                                                                 ▼
   Telegram  ◀──────────  IA (Claude/OpenAI/Gemini)  ◀──────  ESTE SERVIDOR
   (tu móvil)             "interpreta los datos y                (server.js o server.py)
                           da veredicto + plan"
```

1. **El Dashboard de PineScope** calcula de forma nativa todo el análisis (9 marcos, intradía,
   swing, niveles, predicción) y lo **exporta como un JSON de una línea** mediante `alert()`.
   (Pine Script no puede llamar a una IA ni capturar la imagen; solo sabe disparar una alerta.)
2. Una **alerta con webhook** en TradingView envía ese JSON a la URL de este servidor.
3. **Este servidor** recibe el JSON, comprueba un **secreto** (para que nadie más pueda usarlo),
   y arma un **prompt de analista profesional** que aprovecha **todos** esos datos: la
   multi-temporalidad, el motor que inicia el movimiento, la confirmación, las **divergencias
   entre intradía y swing**, los niveles y la predicción. Le pide a la IA un **veredicto
   accionable + gestión de riesgo**.
4. La **IA** responde un análisis breve en español.
5. El servidor **reenvía ese texto a Telegram**.

> **Importante (límite de 3 segundos):** TradingView corta el webhook si tardas más de ~3 s.
> Por eso este servidor **responde 200 al instante** (valida el secreto y confirma recibido) y
> hace el trabajo lento (IA + Telegram) **aparte** (en Node con `setImmediate`, en Python con un
> hilo). Así nunca se pierde una alerta por tardar.

---

## 3. Qué datos le llegan a la IA (el JSON v2.0)

El Dashboard emite un JSON con TODO esto (el servidor lo entiende entero):

```json
{
  "app": "PineScope", "v": "2.0", "secret": "TU_SECRETO",
  "symbol": "NVDA", "price": 123.45, "chartTF": "240",
  "semaforo": "ROJO", "scoreGlobal": -4,
  "tf": {
    "1m":  {"trend":"BAJISTA","stochK":18,"stochEstado":"BAJISTA","stochFuerza":"SOBREVENTA","macdHist":-0.03,"macdEstado":"BAJISTA","macdFuerza":"RECUPERANDO FUERZA"},
    "...": {},
    "Diario": {"trend":"ALCISTA","stochK":62,"stochEstado":"ALCISTA","stochFuerza":"ALCISTA","macdHist":0.23,"macdEstado":"ALCISTA","macdFuerza":"IMPULSO ALCISTA SANO"}
  },
  "intradia": {"tendencia":"POSIBLE BAJISTA","motor":"5m","confirmacion":"15m/30m confirma caída","score":-1.5,"lectura":"Buscar largos finos 1m/3m"},
  "swing":    {"tendencia":"POSIBLE ALCISTA","motor":"1H","confirmacion":"falta 2H/4H | Diario a favor","score":2,"lectura":"Swing alcista en desarrollo"},
  "niveles":     {"soporte":118.0, "resistencia":131.5},
  "prediccion":  {"objetivoSube":131.5, "objetivoBaja":118.0}
}
```

El servidor convierte esto en un "briefing" ordenado (tabla por marco + resumen intradía/swing +
niveles + predicción) y **detecta las divergencias** (por ejemplo, "intradía alcista contra swing
bajista") antes de dárselo a la IA, para que el análisis sea directo y accionable.

---

## 4. Lo que necesitas antes de empezar

1. **Una clave de IA** del proveedor que elijas (solo una):
   - Claude (Anthropic) → console.anthropic.com
   - OpenAI → platform.openai.com
   - Gemini (Google) → aistudio.google.com (tiene plan gratis con límites)
2. **Un bot de Telegram**:
   - Abre **@BotFather** en Telegram, manda `/newbot`, sigue los pasos y copia el **token**.
   - Escríbele algo a tu bot y consigue tu **chat id** con **@getidsbot** o **@userinfobot**.
3. **Node.js 18+** (versión JavaScript) **o** **Python 3.9+** (versión Python).

---

## 5. Configuración (igual para Node y Python)

1. Copia el archivo de ejemplo a `.env`:
   - En Windows (PowerShell): `Copy-Item .env.example .env`
   - En Mac/Linux: `cp .env.example .env`
2. Abre `.env` y rellena:
   - `AI_PROVIDER` = `anthropic`, `openai` o `gemini`.
   - La **clave** de ese proveedor (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` o `GEMINI_API_KEY`).
   - `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
   - `WEBHOOK_SECRET` = una cadena **larga y difícil**. **Debe ser la misma** que pongas en el
     input `secret` del Dashboard de PineScope.

> Nunca subas tu `.env` a GitHub: contiene tus claves.

---

## 6. Cómo correrlo

### Opción A — Node.js

```bash
cd ai-bridge
npm install
npm start
```

Verás: `PineScope AI Bridge v2 escuchando en http://localhost:8080`.

### Opción B — Python (ideal para enchufar a tu proyecto "Agente-de-finanzas")

```bash
cd ai-bridge
pip install -r requirements.txt
python server.py
```

El `server.py` está pensado para integrarse con tu **Agente-de-finanzas** (que ya manda
Telegram): usa el **mismo bot y chat**. Si prefieres, importa `server.py` y reemplaza su función
`send_telegram()` por la que ya tengas en ese proyecto.

**Prueba rápida (sin TradingView)** con un JSON v2.0 de ejemplo:

```bash
curl -X POST http://localhost:8080/webhook ^
  -H "Content-Type: application/json" ^
  -d "{\"app\":\"PineScope\",\"v\":\"2.0\",\"secret\":\"TU_SECRETO\",\"symbol\":\"NVDA\",\"price\":123.45,\"chartTF\":\"240\",\"semaforo\":\"ROJO\",\"scoreGlobal\":-4,\"intradia\":{\"tendencia\":\"POSIBLE BAJISTA\",\"motor\":\"5m\",\"confirmacion\":\"15m/30m confirma caída\",\"score\":-1.5,\"lectura\":\"Buscar largos finos 1m/3m\"},\"swing\":{\"tendencia\":\"BAJISTA\",\"motor\":\"1H\",\"confirmacion\":\"2H/4H confirman caída | Diario en contra\",\"score\":-5.5,\"lectura\":\"Swing bajista en desarrollo\"},\"niveles\":{\"soporte\":118.0,\"resistencia\":131.5},\"prediccion\":{\"objetivoSube\":131.5,\"objetivoBaja\":118.0}}"
```

(En Mac/Linux usa `\` en vez de `^` para los saltos de línea.) Si todo está bien, en unos
segundos te llega el análisis a Telegram.

---

## 7. Exponerlo a internet (para que TradingView lo alcance)

TradingView necesita una **URL pública** (tu `localhost` no le sirve). Dos caminos:

### a) ngrok (rápido, para pruebas)
1. Instala ngrok (ngrok.com) y crea una cuenta gratis.
2. Con el servidor corriendo en el puerto 8080, ejecuta: `ngrok http 8080`.
3. ngrok te da una URL tipo `https://abc123.ngrok-free.app`. Tu webhook será
   `https://abc123.ngrok-free.app/webhook`.

> La URL gratis de ngrok **cambia cada vez** que lo reinicias; tendrás que actualizar la alerta.

### b) Hosting gratis (para dejarlo siempre encendido)
Servicios con plan gratuito: **Render**, **Railway**, **Fly.io**, **Replit**, etc. Sube la carpeta
`ai-bridge`, configura las mismas variables del `.env` en su panel y te darán una URL fija
`https://...` → tu webhook será `https://tu-app.../webhook`.

---

## 8. Configurar la alerta en TradingView

1. En el Dashboard de PineScope, activa el input **"Emitir IA"** y pon tu **secreto** en el input
   `secret` (el mismo de tu `.env`).
2. Crea una **Alerta** sobre el Dashboard. Como condición, usa la del propio indicador (el
   Dashboard ya hace `alert(..., alert.freq_once_per_bar_close)` con el JSON completo).
3. En la alerta, activa **Webhook URL** y pega tu URL pública: `https://.../webhook`.
4. **No necesitas escribir el mensaje a mano**: el Dashboard ya construye el JSON v2.0 con todos
   los datos. Asegúrate de que el mensaje de la alerta use `{{strategy.order.alert_message}}` /
   el mensaje del `alert()` del indicador (según cómo lo dispares).

> ⚠️ Para que una alerta de TradingView pueda enviar **webhooks** normalmente necesitas un **plan
> de pago** (Essential/Pro o superior). En el plan **gratuito** las alertas existen pero **no
> mandan webhooks**. Si no quieres pagar, usa la **extensión FinScope** (ver punto 1): hace el
> análisis gratis, con un clic, mientras miras el gráfico — la diferencia es que FinScope le da a
> la IA la **imagen** del gráfico, y este puente le da los **datos nativos exactos**.

¡Listo! Cuando el Dashboard dispare la alerta, recibirás el veredicto en Telegram.

---

## 9. Si algo falla

- **No llega nada a Telegram:** revisa `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` y que le hayas
  escrito **tú primero** al bot. El servidor también te avisa por Telegram si la IA falla.
- **401 "secreto inválido":** el `secret` del JSON (input del Dashboard) no coincide con
  `WEBHOOK_SECRET`.
- **Error de la IA:** revisa que la clave del proveedor sea correcta y que `AI_PROVIDER` apunte
  al proveedor del que pusiste la clave. Gemini gratis tiene límites: si ves error de cuota,
  espera o cambia de proveedor (el servidor ya prueba modelos de respaldo de Gemini si el tuyo
  no existe).
- **TradingView no llama:** confirma que tu plan permite **webhooks** y que la URL pública
  (ngrok/hosting) está activa y termina en `/webhook`.

---

## 10. Archivos de esta carpeta

| Archivo | Qué es |
|---|---|
| `server.js` | Servidor en Node/Express (entiende el JSON v2.0). |
| `server.py` | Servidor en Python/Flask (mismo comportamiento; para "Agente-de-finanzas"). |
| `.env.example` | Plantilla de configuración (cópiala a `.env`). |
| `package.json` | Dependencias y script `start` de Node. |
| `requirements.txt` | Dependencias de Python (`flask`, `requests`). |
| `README.md` | Este archivo. |

*Análisis educativo, NO recomendación de compra/venta.*
