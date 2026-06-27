# PineScope — Puente de IA externa (AI Bridge)

Este pequeño servidor es el **puente** entre tu indicador de TradingView y una IA
(Claude / OpenAI / Gemini), para que cuando tu indicador detecte una señal te llegue
un **análisis escrito** directo a **Telegram**.

> En una frase: *tu indicador grita "¡señal!", este servidor le pregunta a la IA "¿qué
> significa?" y te manda la respuesta al teléfono.*

---

## 1. ¿Por qué hace falta este puente?

Pine Script (el lenguaje de los indicadores de TradingView) **no puede llamar a una IA
por sí mismo**. Lo único que sabe hacer es disparar una **alerta**, y esa alerta puede
mandar un mensaje a una dirección de internet (un *webhook*).

Así que el plan es:

```
┌────────────────────┐   alerta    ┌──────────────────────┐   webhook (JSON)
│  Indicador Pine    │ ─────────▶  │   Alerta en          │ ───────────────┐
│  (en TradingView)  │             │   TradingView        │                │
└────────────────────┘             └──────────────────────┘                │
                                                                           ▼
   Telegram  ◀───────────  IA (Claude/OpenAI/Gemini)  ◀──────  ESTE SERVIDOR
   (tu móvil)              "interpreta la señal"               (server.js o server.py)
```

1. **Indicador Pine** detecta una condición (cruce, patrón, ruptura…).
2. **Alerta con webhook** en TradingView envía los datos en formato JSON a la URL de este servidor.
3. **Este servidor** recibe el JSON, comprueba un **secreto** (para que nadie más pueda usarlo),
   arma un **prompt de analista financiero** con el método de **velas japonesas**
   (Tendencia + Nivel + Señal) y se lo manda a la IA.
4. La **IA** devuelve un análisis breve en español.
5. El servidor **reenvía ese texto a Telegram**.

---

## 2. ⚠️ Importante: el webhook de TradingView casi siempre es de PAGO

Para que una alerta de TradingView pueda enviar un **webhook** (que es lo que alimenta a este
servidor) normalmente necesitas un **plan de pago** (a día de hoy, plan *Essential/Pro* o
superior). En el plan **gratuito** las alertas existen, pero **no dejan mandar webhooks**.

### La ALTERNATIVA 100% GRATIS: usar la extensión FinScope como puente

Si no quieres pagar TradingView, ya tienes otra forma de conseguir lo mismo **sin webhooks y
sin este servidor**: la extensión de Chrome **FinScope** (en `BMW/finscope/`).

- FinScope vive **dentro del navegador**, sobre el propio gráfico de TradingView.
- **Captura el gráfico** (una imagen) y/o los datos del activo y **llama a la IA con visión**
  (Claude/OpenAI/Gemini), usando el **mismo método de velas japonesas** que este puente.
- Te muestra el análisis ahí mismo, gratis, sin pagar el plan de TradingView y sin montar nada.

**Resumen de cuándo usar cada cosa:**

| Quieres… | Usa |
|---|---|
| Análisis automático que te llega **solo** a Telegram cuando salta una señal | **Este AI Bridge** (requiere plan de pago de TradingView para el webhook) |
| Análisis **gratis**, pidiéndolo tú con un clic mientras miras el gráfico | **Extensión FinScope** (sin webhooks, sin pagar) |

Las dos comparten la misma "cabeza" (mismos proveedores de IA y el mismo método de velas),
así que el estilo del análisis es coherente entre ambas.

---

## 3. Lo que necesitas antes de empezar

1. **Una clave de IA** del proveedor que elijas (solo una):
   - Claude (Anthropic) → console.anthropic.com
   - OpenAI → platform.openai.com
   - Gemini (Google) → aistudio.google.com (tiene plan gratis con límites)
2. **Un bot de Telegram**:
   - Abre **@BotFather** en Telegram, manda `/newbot`, sigue los pasos y copia el **token**.
   - Escríbele algo a tu bot, y consigue tu **chat id** con **@getidsbot** o **@userinfobot**.
3. **Node.js 18+** (para la versión JavaScript) **o** **Python 3.9+** (para la versión Python).

---

## 4. Configuración (igual para Node y Python)

1. Copia el archivo de ejemplo a `.env`:
   - En Windows (PowerShell): `Copy-Item .env.example .env`
   - En Mac/Linux: `cp .env.example .env`
2. Abre `.env` y rellena:
   - `AI_PROVIDER` = `anthropic`, `openai` o `gemini`.
   - La **clave** de ese proveedor (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY` o `GEMINI_API_KEY`).
   - `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
   - `WEBHOOK_SECRET` = invéntate una cadena **larga y difícil** (la pondrás también en TradingView).

> Nunca subas tu `.env` a GitHub: contiene tus claves.

---

## 5. Cómo correrlo

### Opción A — Node.js

```bash
cd ai-bridge
npm install
npm start
```

Verás: `PineScope AI Bridge escuchando en http://localhost:8080`.

### Opción B — Python (ideal para enchufar a tu proyecto "Agente-de-finanzas")

```bash
cd ai-bridge
pip install flask requests
python server.py
```

El `server.py` está pensado para integrarse con tu **Agente-de-finanzas** (que ya manda
Telegram): usa el **mismo bot y chat**. Si prefieres, puedes importar `server.py` y reemplazar
su función `send_telegram()` por la que ya tengas en ese proyecto.

**Prueba rápida (sin TradingView)** para ver que todo funciona, simula una alerta:

```bash
curl -X POST http://localhost:8080/webhook ^
  -H "Content-Type: application/json" ^
  -H "x-webhook-secret: TU_SECRETO" ^
  -d "{\"symbol\":\"AAPL\",\"timeframe\":\"1D\",\"price\":195.3,\"signal\":\"cruce alcista SMA50\",\"rsi\":58}"
```

(En Mac/Linux usa `\` en vez de `^` para los saltos de línea.) Si todo está bien, te llegará
un mensaje a Telegram en unos segundos.

---

## 6. Exponerlo a internet (para que TradingView lo alcance)

TradingView necesita una **URL pública** (tu `localhost` no le sirve). Dos caminos:

### a) ngrok (rápido, para pruebas)
1. Instala ngrok (ngrok.com) y crea una cuenta gratis.
2. Con el servidor corriendo en el puerto 8080, ejecuta: `ngrok http 8080`
3. ngrok te da una URL tipo `https://abc123.ngrok-free.app`. Tu webhook será
   `https://abc123.ngrok-free.app/webhook`.

> La URL gratis de ngrok **cambia cada vez** que lo reinicias; tendrás que actualizar la alerta.

### b) Hosting gratis (para dejarlo siempre encendido)
Servicios con plan gratuito donde puedes subir este servidor: **Render**, **Railway**,
**Fly.io**, **Replit**, **Deta/Cyclic**, etc. Sube la carpeta `ai-bridge`, configura las
mismas variables del `.env` en su panel y te darán una URL fija `https://...` →
tu webhook será `https://tu-app.../webhook`.

---

## 7. Configurar la alerta en TradingView

1. Abre tu indicador en el gráfico y crea una **Alerta**.
2. En la alerta, activa **Webhook URL** y pega tu URL pública: `https://.../webhook`.
3. En el **mensaje** de la alerta, pon un **JSON** con los datos. Ejemplo (TradingView reemplaza
   los `{{...}}` por valores reales):

```json
{
  "secret": "TU_SECRETO",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "price": {{close}},
  "signal": "Mi indicador disparó la condición",
  "rsi": {{plot_0}}
}
```

- `secret` debe coincidir con tu `WEBHOOK_SECRET` (también puedes mandarlo en el header
  `x-webhook-secret` o como `?secret=...` al final de la URL).
- Cuantos más datos útiles metas (precio, temporalidad, niveles, RSI…), **mejor** será el análisis.

¡Listo! Cuando tu indicador dispare la alerta, recibirás el análisis en Telegram.

---

## 8. Si algo falla

- **No llega nada a Telegram:** revisa `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` y que le hayas
  escrito **tú primero** al bot. El servidor también te avisa por Telegram si la IA falla.
- **401 "secreto inválido":** el `secret` de la alerta no coincide con `WEBHOOK_SECRET`.
- **Error de la IA:** revisa que la clave del proveedor sea correcta y que `AI_PROVIDER` apunte
  al proveedor del que pusiste la clave. Gemini gratis tiene límites: si ves error de cuota,
  espera o cambia de proveedor.
- **TradingView no llama:** confirma que tu plan permite **webhooks** y que la URL pública
  (ngrok/hosting) está activa y termina en `/webhook`.

---

## 9. Archivos de esta carpeta

| Archivo | Qué es |
|---|---|
| `server.js` | Servidor en Node/Express. |
| `server.py` | Servidor en Python/Flask (para "Agente-de-finanzas"). |
| `.env.example` | Plantilla de configuración (cópiala a `.env`). |
| `package.json` | Dependencias y script `start` de Node. |
| `README.md` | Este archivo. |

*Análisis educativo, NO recomendación de compra/venta.*
