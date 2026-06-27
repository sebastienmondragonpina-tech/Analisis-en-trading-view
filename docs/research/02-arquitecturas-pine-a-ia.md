# Arquitecturas END-TO-END: de Pine Script / TradingView a una IA externa

> Investigación: cómo conectar señales de Pine Script / TradingView a una IA (Claude / OpenAI / Gemini) que corre **fuera** de TradingView.
> Fecha: 2026-06-26.

---

## 0. El problema de base (y por qué la IA va por fuera)

Pine Script **no puede hacer llamadas de red arbitrarias** (no hay `http.get`, no hay sockets). Lo único que Pine puede hacer hacia el exterior es **disparar una alerta**, y esa alerta puede:

1. Mostrarse en pantalla / app.
2. Enviar un **webhook** (un `POST` HTTP) a una URL tuya con un cuerpo de texto o JSON.

Por tanto, la arquitectura **siempre** es la misma forma de embudo:

```
Pine Script (indicador/estrategia)
   └── alert() / alertcondition()  → dispara cuando se cumple tu condición
        └── Webhook POST (JSON)  → a una URL pública tuya (HTTPS)
             └── Tu servidor / función recibe el JSON
                  └── Llama a la IA (Claude / OpenAI / Gemini) con el contexto
                       └── Devuelve el análisis → Telegram / Discord / email / broker
```

La IA **nunca** vive dentro de TradingView: vive en tu endpoint. TradingView solo "empuja" el evento.

### Restricciones oficiales del webhook de TradingView (críticas para el diseño)

Tomadas de la documentación oficial:

- **Puertos**: solo se aceptan **80 y 443**. Cualquier otro puerto se rechaza. **No hay soporte IPv6**.
- **Timeout**: si tu servidor tarda **más de 3 segundos** en responder, TradingView **cancela** la petición. → Esto obliga a **responder rápido (200 OK) y procesar la IA en segundo plano**, porque una llamada a un LLM tarda varios segundos.
- **Content-Type**: si el mensaje de la alerta es JSON válido, TradingView lo envía con `application/json`; si no, va como `text/plain`.
- **Requisito de cuenta**: los webhooks requieren un **plan de pago** (Pro o superior) y **2FA habilitado** en la cuenta.
- **IPs de origen** de TradingView (útiles para *allowlist* en el firewall):
  - `52.89.214.238`
  - `34.212.75.30`
  - `54.218.53.128`
  - `52.32.178.7`
- Como TradingView no firma la petición, la práctica estándar es meter una **clave secreta dentro del propio JSON** (`"key": "..."`) y validarla en el servidor. **Nunca** metas credenciales sensibles reales en el cuerpo.

Fuentes:
- [TradingView – How to configure webhook alerts (oficial)](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/)
- [TradingView – Pine Script docs: Alerts (FAQ)](https://www.tradingview.com/pine-script-docs/faq/alerts/)
- [Roboquant – TradingView Webhooks: Complete Guide (JSON format)](https://www.roboquant.dev/blog/tradingview-webhook-complete-guide)

---

## 1. Proyectos open-source reales en GitHub

Cinco repos representativos, ordenados por cercanía a "señal → notificación / IA":

### 1.1 `fabston/TradingView-Webhook-Bot` — el clásico de notificaciones
- **Enfoque**: servidor **Flask** que expone `/webhook`, recibe la alerta de TradingView en JSON y la **reenvía a Telegram, Discord, Slack, Twitter y/o Email**.
- **Seguridad**: cada payload lleva un campo `"key"` que debe coincidir con `sec_key` en `config.py`.
- **Payload**: campos `key`, `msg` (soporta Markdown y variables de TradingView como `{{close}}`, `{{exchange}}`), y opcionalmente el canal destino.
- Es la **plantilla mental** de "webhook → notificación". Es trivial insertar un paso de IA entre "recibo" y "envío a Telegram".
- URL: https://github.com/fabston/TradingView-Webhook-Bot

### 1.2 `robswc/tradingview-webhooks-bot` (TVWB) — framework extensible
- **Enfoque**: **framework** (no librería de trading) con **arquitectura por eventos**. Flask + GUI web. Dispara eventos (`WebhookReceived`) y tú enganchas **Actions** con tu lógica.
- Flujo de uso por CLI: `action:create` → `action:link` (a un evento) → editas el método `run()` con tu lógica. Tiene `validate_data()` para leer el payload.
- Útil si quieres una base ordenada donde "tu Action" sea **"llamar a la IA y mandar a Telegram"**.
- URL: https://github.com/robswc/tradingview-webhooks-bot

### 1.3 `tedawf/tradingview-telegram-alerts` — webhook → Telegram con captura de gráfico
- **Enfoque**: **FastAPI** que recibe el webhook, **responde al instante** y delega a un **worker en cola async**. El worker **captura un screenshot del gráfico con Playwright (Chromium headless)** y lo publica en un canal de Telegram.
- Comandos de Telegram para configurar intervalos, temas y mapeos símbolo→exchange.
- **Muy relevante** para tu caso: demuestra el patrón "responder rápido + procesar pesado (screenshot / IA) en background" que el límite de 3 s de TradingView **obliga** a usar.
- URL: https://github.com/tedawf/tradingview-telegram-alerts

### 1.4 `CryptoGnome/Tradingview-Webhook-Bot` — webhook → ejecución de órdenes
- **Enfoque**: Flask + Python pensado para correr gratis en Heroku; recibe alertas y **ejecuta operaciones reales en varios exchanges de cripto** vía API.
- Relevante como referencia de "el otro lado del embudo" (ejecutar en vez de notificar). Para tu proyecto **no** ejecutas órdenes, pero muestra el mismo esqueleto de recepción.
- URL: https://github.com/CryptoGnome/Tradingview-Webhook-Bot

### 1.5 `tradesdontlie/tradingview-mcp` — IA + TradingView SIN webhook (enfoque alternativo)
- **Enfoque**: servidor **MCP** que conecta **Claude Code** a **TradingView Desktop** vía **Chrome DevTools Protocol (CDP)** en `localhost:9222` (sin webhooks, sin tocar servidores de TradingView). 78 herramientas MCP: leer valores de indicadores, cambiar símbolo/timeframe, escribir/compilar Pine Script, replay, etc. Todo **local**.
- Es la **arquitectura opuesta**: en vez de "TradingView empuja al servidor de IA", aquí "la IA hala datos del TradingView local". Útil para análisis interactivo / desarrollo de Pine, **no** para alertas autónomas 24/7.
- URL: https://github.com/tradesdontlie/tradingview-mcp

> Mención honorable: `ndywicki/tradingview-webhooks-bot` (alertas → ByBit), `lth-elm/TradingView-Webhook-Trading-Bot` (Flask → orden o screenshot a Discord con confirmación humana).

---

## 2. Patrones serverless / hosting para recibir el webhook y llamar a la IA

Todos cumplen lo mismo: exponer una URL HTTPS (puerto 443) que reciba el `POST`. La gran disyuntiva es el **límite de 3 s de TradingView** vs. el tiempo de un LLM (varios segundos). Hay dos estrategias:

- **A) Responder 200 al instante y procesar la IA en background** (cola, worker, `fire-and-forget`). Recomendado.
- **B) Procesar inline** solo si tu prompt es cortísimo y el modelo responde <3 s (arriesgado).

### 2.1 Cloudflare Workers
- **Pros**: cold start ~0–5 ms; free tier generoso (**100.000 req/día**); facturan **solo CPU-time**, no el tiempo esperando a la API del LLM (ideal para I/O); HTTPS y dominio incluidos; `$5/mes` = 10M req. Cero gestión de servidor.
- **Contras**: runtime JS/TS/WASM (no Python nativo, no `fs`, no librerías nativas pesadas); para el patrón "background" necesitas `ctx.waitUntil()` o **Queues** (en plan pago). El límite de CPU del free tier es ajustado para prompts muy largos.
- **Cuándo**: si quieres el receptor más barato/rápido y tu lógica de IA es una simple llamada `fetch` a la API de Claude/OpenAI/Gemini.

### 2.2 Vercel Functions
- **Pros**: despliegue trivial (sobre todo si ya usas Next.js); soporta **Node, Python, Go, Rust, etc.**; buen DX.
- **Contras**: el plan **Hobby (gratis) es solo uso personal/no comercial**; Pro cuesta **$20/asiento** + consumo. Funciones con timeout; para "background" real conviene Vercel Queues/cron o devolver rápido. Más caro que Workers para esto.
- **Cuándo**: si ya tienes el ecosistema Vercel o quieres Python serverless sin montar infra.

### 2.3 AWS Lambda
- **Pros**: **runtime completo** (Python con todas tus dependencias, >10 MB); free tier de **1M req + 400.000 GB-s**; integración profunda con SQS/EventBridge para el patrón background "de libro" (Lambda recibe → mete en SQS → otra Lambda llama al LLM). Cobra `$0.20/1M req`.
- **Contras**: **cold starts de 1–3 s** en Node/Python (puede comerse tu presupuesto de 3 s si procesas inline); más piezas que configurar (API Gateway, IAM, etc.); curva de aprendizaje mayor.
- **Cuándo**: si quieres Python + dependencias pesadas (pandas, tu propia librería de señales) y no te importa montar API Gateway.

### 2.4 VPS con Node/Python (o tu propia máquina)
- **Pros**: control total; Python nativo con cualquier librería; **proceso de larga duración** (puedes mantener colas, estado, conexiones a Telegram abiertas); sin límites artificiales de tiempo; **encaja perfecto con un daemon que ya corre 24/7** (¡tu caso!).
- **Contras**: tú gestionas SO, HTTPS/certificados, uptime, seguridad. Necesitas IP pública o un **túnel**.
- **Tip clave para tu PC**: si el daemon corre en tu máquina sin IP pública, usa **Cloudflare Tunnel** (dominio permanente gratis, HTTPS, sin abrir puertos en el router) o **ngrok** (más simple pero URL cambiante en free tier). Cloudflare Tunnel es la mejor opción para un webhook permanente.

### Resumen comparativo

| Plataforma | Free tier | Lenguaje | Background/LLM lento | Esfuerzo | Ideal para |
|---|---|---|---|---|---|
| **Cloudflare Workers** | 100k req/día | JS/TS/WASM | `waitUntil()` / Queues | Bajo | Receptor barato y rápido |
| **Vercel Functions** | Solo personal | Node/Python/… | Cron/Queues | Bajo | Ya usas Vercel/Next |
| **AWS Lambda** | 1M req | Cualquiera | SQS/EventBridge (nativo) | Alto | Python + deps pesadas |
| **VPS / tu daemon** | (tu hardware) | Cualquiera | Trivial (proceso vivo) | Medio | **Tu caso: daemon 24/7** |

Fuentes:
- [Veld Systems – AWS Lambda vs Cloudflare Workers vs Vercel Functions](https://veldsystems.com/blog/aws-lambda-vs-cloudflare-workers-vs-vercel-functions)
- [Cloudflare Workers vs Lambda 2026 (cold starts)](https://tech-insider.org/cloudflare-workers-vs-lambda-2026/)
- [Morph – Cloudflare Workers vs Vercel (pricing)](https://www.morphllm.com/comparisons/cloudflare-workers-vs-vercel)
- [Twilio – Expose localhost con ngrok / Cloudflare Tunnel / Tailscale](https://www.twilio.com/en-us/blog/expose-localhost-to-internet-with-tunnel)
- [awesome-tunneling (lista de alternativas)](https://github.com/anderspitman/awesome-tunneling)

---

## 3. Cómo pasar el contexto del gráfico a la IA y devolver el análisis

### 3.1 Construir el JSON en Pine (en el mensaje de la alerta)

En Pine Script, el **mensaje de la alerta es texto** y puede contener placeholders que TradingView sustituye en el momento del disparo. Metes ahí los valores de tu indicador. Ejemplo de mensaje de alerta:

```json
{
  "key": "MI_CLAVE_SECRETA",
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "interval": "{{interval}}",
  "time": "{{timenow}}",
  "price": {{close}},
  "signal": "BUY",
  "rsi": {{plot_0}},
  "ema_fast": {{plot_1}},
  "ema_slow": {{plot_2}},
  "comment": "Cruce alcista EMA + RSI<30"
}
```

Notas:
- `{{close}}`, `{{ticker}}`, `{{exchange}}`, `{{interval}}`, `{{timenow}}` son variables nativas de TradingView.
- `{{plot_0}}`, `{{plot_1}}`, … exponen el valor de los `plot()` de tu indicador en la barra del disparo → así **viajan los valores reales del indicador** dentro del JSON.
- En estrategias además tienes `{{strategy.order.action}}`, `{{strategy.position_size}}`, etc.
- Si el texto es JSON válido, TradingView lo manda como `application/json`; tu servidor hace `request.json()` directo.

### 3.2 Pasar ese contexto a la IA

En el servidor, conviertes el JSON en un **prompt estructurado**. Patrón recomendado:

- **System prompt**: define el rol ("Eres un analista técnico; responde en 3 líneas: tendencia, nivel clave, acción sugerida; sin recomendaciones de inversión garantizadas").
- **User prompt**: inyectas los campos del JSON + opcionalmente datos extra que tú añadas en el servidor (p. ej. precio actual de Yahoo, contexto de las ~100 acciones que ya vigila tu daemon).
- Puedes pedir **salida JSON** (`{"tendencia": "...", "nivel": "...", "accion": "..."}`) para formatear el mensaje de Telegram de forma fiable.

### 3.3 Devolver el análisis

El servidor recibe el texto/JSON del LLM y lo enruta al canal: **Telegram** (`sendMessage` vía Bot API), Discord, email, o de vuelta a un broker. Por el límite de 3 s, **responde 200 a TradingView primero** y manda a Telegram **después**, en background.

Fuentes:
- [TradingView – Pine Script docs: Alerts (placeholders {{plot_0}}, {{close}}…)](https://www.tradingview.com/pine-script-docs/faq/alerts/)
- [PickMyTrade – TradingView JSON Alert Configuration](https://docs.pickmytrade.trade/docs/tradingview-json-alert-configuration/)

---

## 4. TU CASO: enchufar el webhook al daemon "Agente-de-finanzas"

**Situación**: ya tienes un **daemon en Python** que vigila ~100 acciones y avisa por **Telegram**. Eso significa que ya tienes:
- Proceso 24/7 (ideal para el patrón "responde rápido + procesa en background", sin pelearte con límites serverless).
- Cliente de Telegram funcionando (token + chat_id).
- Probablemente tu propia lógica de señales / acceso a datos.

**La forma más limpia: añadir un mini-servidor HTTP dentro (o al lado) del daemon**, que reciba el webhook de TradingView, valide la clave, encole el evento, llame a la IA en un hilo aparte y reutilice tu función de envío a Telegram existente.

### 4.1 Arquitectura propuesta

```
TradingView alert (Pine)
   → POST https://tu-dominio/tv-webhook   (vía Cloudflare Tunnel → tu PC/daemon)
        → FastAPI/Flask dentro del daemon
             → valida "key"  → 200 OK inmediato (<3 s)
             → encola (queue) el payload
                  → worker en background:
                       → arma prompt con los valores del indicador (+ datos de tu daemon)
                       → llama a Claude/OpenAI/Gemini
                       → envía el análisis con tu telegram_send() YA EXISTENTE
```

- **Exposición**: como el daemon corre en tu máquina, usa **Cloudflare Tunnel** (HTTPS permanente, gratis, sin abrir puertos). Configuras el dominio una vez y la URL del webhook no cambia. (`cloudflared`)
- **Puerto**: TradingView solo habla 443 → el túnel resuelve esto; tu FastAPI puede escuchar en `localhost:8000` y el túnel publica en 443.
- **Seguridad**: valida `key` del JSON **y** opcionalmente restringe por IP de origen (las 4 IPs de TradingView).
- **Background**: imprescindible por el timeout de 3 s — responde 200 antes de llamar al LLM.

### 4.2 Esqueleto del endpoint (FastAPI + worker en hilo)

```python
# tv_webhook.py  — se ejecuta dentro de tu daemon "Agente-de-finanzas"
import os, queue, threading
from fastapi import FastAPI, Request, HTTPException
import uvicorn

# --- Reutiliza lo que YA tiene tu daemon ---
# from agente_finanzas import telegram_send   # tu función existente
# from agente_finanzas import get_extra_context  # opcional: precio Yahoo, etc.

WEBHOOK_KEY = os.environ["TV_WEBHOOK_KEY"]          # la "key" que pones en el JSON de la alerta
TV_IPS = {"52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"}

app = FastAPI()
work_q: "queue.Queue[dict]" = queue.Queue()


@app.post("/tv-webhook")
async def tv_webhook(request: Request):
    # (opcional) allowlist por IP de origen de TradingView
    client_ip = request.headers.get("cf-connecting-ip") or request.client.host
    # if client_ip not in TV_IPS: raise HTTPException(403, "IP no permitida")

    # TradingView manda application/json si el mensaje es JSON válido
    data = await request.json()

    if data.get("key") != WEBHOOK_KEY:
        raise HTTPException(status_code=403, detail="clave inválida")

    # NO llamamos al LLM aquí: el límite de 3 s de TradingView nos obliga a
    # responder ya y procesar en background.
    work_q.put(data)
    return {"status": "ok"}        # 200 inmediato (<3 s)


def ask_ai(payload: dict) -> str:
    """Arma el prompt con los valores del indicador y llama a la IA."""
    system = ("Eres un analista técnico. Responde en 3 lineas: "
              "Tendencia, Nivel clave, Accion sugerida. Sin garantias.")
    user = (
        f"Senal: {payload.get('signal')} en {payload.get('ticker')} "
        f"({payload.get('exchange')}, {payload.get('interval')})\n"
        f"Precio: {payload.get('price')}  RSI: {payload.get('rsi')}  "
        f"EMA rapida: {payload.get('ema_fast')}  EMA lenta: {payload.get('ema_slow')}\n"
        f"Comentario del script: {payload.get('comment')}"
        # + get_extra_context(payload['ticker'])  # datos extra de tu daemon
    )

    # --- Claude (Anthropic) ---
    from anthropic import Anthropic
    client = Anthropic()  # usa ANTHROPIC_API_KEY del entorno
    msg = client.messages.create(
        model="claude-sonnet-4-5",       # modelo a tu elección
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text

    # --- Alternativa OpenAI ---
    # from openai import OpenAI
    # r = OpenAI().chat.completions.create(
    #     model="gpt-4.1-mini",
    #     messages=[{"role":"system","content":system},
    #               {"role":"user","content":user}])
    # return r.choices[0].message.content

    # --- Alternativa Gemini ---
    # from google import genai
    # r = genai.Client().models.generate_content(
    #     model="gemini-2.5-flash", contents=f"{system}\n\n{user}")
    # return r.text


def worker():
    while True:
        payload = work_q.get()
        try:
            analysis = ask_ai(payload)
            texto = (f"🔔 {payload.get('signal')} {payload.get('ticker')} "
                     f"@ {payload.get('price')}\n\n{analysis}")
            # telegram_send(texto)   # ← REUTILIZA tu envío a Telegram existente
            print(texto)
        except Exception as e:
            print("error procesando señal:", e)
        finally:
            work_q.task_done()


def start_webhook_server():
    """Llama esto desde el arranque de tu daemon (en un hilo)."""
    threading.Thread(target=worker, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)   # Cloudflare Tunnel publica en 443
```

### 4.3 Pasos concretos de integración

1. **Pine**: en tu indicador, en la condición, usa `alert(message=...)` con el JSON de la sección 3.1 (incluye tu `key` y los `{{plot_n}}` de tus indicadores).
2. **Daemon**: añade `tv_webhook.py` y llama a `start_webhook_server()` en un hilo al arrancar (o córrelo como proceso hermano). Reemplaza `telegram_send()` y `get_extra_context()` por tus funciones reales.
3. **Túnel**: instala `cloudflared`, crea un tunnel con dominio permanente apuntando a `localhost:8000`. Anota la URL HTTPS pública.
4. **Alerta en TradingView**: en "Notificaciones → Webhook URL" pega `https://tu-dominio/tv-webhook`. Activa 2FA (requisito).
5. **Probar**: dispara la alerta manualmente; confirma 200 OK y que llega el análisis de la IA a Telegram.

### 4.4 Por qué este encaje es el mejor para ti

- **Reutiliza** tu cliente de Telegram, tus claves y tu lógica — no montas infra nueva.
- El daemon **ya está vivo 24/7**, así que el patrón "responder rápido + LLM en background" es trivial (cola en memoria, hilo worker), sin pelear con cold starts ni timeouts de serverless.
- Cloudflare Tunnel resuelve HTTPS/puerto 443 sin tocar tu router.
- Mantienes la IA **multi-proveedor** (igual que FinScope): basta cambiar la función `ask_ai`.

Fuentes para esta sección:
- [fabston/TradingView-Webhook-Bot (patrón key + reenvío a Telegram)](https://github.com/fabston/TradingView-Webhook-Bot)
- [tedawf/tradingview-telegram-alerts (FastAPI + worker async)](https://github.com/tedawf/tradingview-telegram-alerts)
- [TradingView – webhook oficial (IPs, puertos, timeout 3 s)](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/)
- [Cloudflare Tunnel para exponer localhost](https://developers.cloudflare.com/pages/how-to/preview-with-cloudflare-tunnel/)

---

## 5. Conclusión / arquitectura recomendada

Para tu caso, **no montes nada serverless nuevo**: añade un endpoint HTTP ligero (FastAPI) **dentro de tu daemon Python existente**. Pine dispara una alerta con webhook cuyo **mensaje es un JSON** que incluye una `key` secreta y los valores de tus indicadores (`{{plot_0}}`, `{{close}}`, etc.). El daemon **valida la clave, responde 200 en menos de 3 s y encola el evento**; un hilo *worker* arma el prompt, llama a la IA (Claude/OpenAI/Gemini, intercambiables) y **reutiliza tu envío a Telegram** ya existente. Expones el endpoint con **Cloudflare Tunnel** (HTTPS permanente, gratis, sin abrir puertos), porque TradingView solo habla por el puerto 443. Si algún día quieres independizarlo del PC, la alternativa serverless más barata y rápida es **Cloudflare Workers** (100k req/día gratis, facturación solo por CPU).
