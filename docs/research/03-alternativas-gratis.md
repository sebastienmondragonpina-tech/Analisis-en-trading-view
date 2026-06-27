# Conectar TradingView / Pine Script con una IA — vías GRATIS (sin plan de pago de TradingView)

> **Objetivo:** que un usuario NO técnico (~40 años) conecte lo que ve en TradingView / sus indicadores Pine
> con una IA, **sin pagar** el plan de TradingView (los webhooks oficiales exigen plan de pago).
> **Fecha del análisis:** 26 de junio de 2026.

---

## TL;DR (resumen ejecutivo)

- Los **webhooks oficiales de TradingView exigen plan de pago** (Essential/Plus o superior). El plan
  gratuito **NO** tiene webhooks. ([TradingView Hub](https://www.tv-hub.org/guide/tradingview-alerts-setup),
  [Tickerly](https://tickerly.net/best-tradingview-plan/))
- Para un usuario no técnico y sin pago, la vía **más realista** es una **extensión de navegador**
  (como la propia **FinScope** del usuario) que lee el DOM y/o captura el gráfico con
  `chrome.tabs.captureVisibleTab` y lo manda a una **IA con visión**. Es el enfoque con menos piezas y
  cero servidores. ([MDN captureVisibleTab](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/captureVisibleTab))
- ⚠️ **Aviso de modelo:** **Gemini 2.0 Flash fue descontinuado y se apagó el 1 de junio de 2026**. Hoy el
  modelo gratuito con visión equivalente es **Gemini 2.5 Flash** (o 3 Flash). El README de FinScope todavía
  recomienda `gemini-2.0-flash`; hay que actualizarlo. ([Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing),
  [Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits))

---

## El problema de fondo: ¿qué necesita el plan de pago?

| Plan TradingView | Webhooks | Alertas por email | Nº alertas activas |
|---|---|---|---|
| **Free / Basic** | ❌ No | ✅ Sí | 1 (free) |
| **Essential** | ✅ Sí | ✅ Sí | 20 |
| **Plus** | ✅ Sí | ✅ Sí | 100 |
| **Premium** | ✅ Sí | ✅ Sí | 400 |

Fuentes: [TradingView Hub — webhooks requieren Plus o superior](https://www.tv-hub.org/guide/tradingview-alerts-setup),
[Tickerly — qué plan elegir 2026](https://tickerly.net/best-tradingview-plan/),
[QuantRoutine — comparativa de planes](https://quantroutine.com/tools/tradingview-free-vs-pro/).
Requisito adicional: los webhooks **solo** funcionan con **2FA activado**
([doc oficial de webhooks](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/)).

> Pine Script **no tiene "visión"**: solo opera con datos numéricos (series OHLCV, valores de indicadores).
> No "ve" la forma del gráfico, patrones de velas dibujados, líneas de tendencia, etc. Por eso la opción (d)
> —mandar la **imagen** del gráfico a un modelo de visión— es interesante: *recupera* lo que Pine no puede ver.

---

## (a) Bridge vía EXTENSIÓN DE NAVEGADOR (leer DOM o capturar el gráfico) — **la más realista para "gratis"**

**Cómo funciona.** Una extensión Chrome MV3 (exactamente el patrón de **FinScope**) corre encima de la
pestaña de TradingView. Tiene dos formas de "leer" el gráfico:

1. **Leer el DOM / tabla de valores del indicador** (texto): precio, RSI, valores de la leyenda del
   indicador, etc. Es lo que FinScope ya hace con sus *adapters* de scraping y los datos de Yahoo.
2. **Capturar la imagen visible** con `chrome.tabs.captureVisibleTab`, que devuelve un *data URL* (PNG/JPEG)
   de lo que se ve en pantalla, y mandarla a una **IA con visión** (Gemini Flash, GPT-4o-mini, etc.).
   ([MDN captureVisibleTab](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/captureVisibleTab),
   [tutorial captura MV3](https://medium.com/@chandanaug13/chrome-extension-capture-tab-tutorial-b4a7960a06ae),
   [ejemplo MV3 screenshot](https://github.com/hacess/chrome-extension-manifestv3-screenshot))

**Ya existe como producto.** Hay extensiones que hacen justo esto:
- **Screenshot to AI** — captura la pantalla (o una región) y la manda con un prompt a Gemini/Copilot/Claude/Perplexity de un clic. ([Chrome Web Store](https://chromewebstore.google.com/detail/screenshot-to-ai/jhlolbkodlggdbhijicplfhcpigdjoij))
- **tradingview-chart-analyzer** — extensión Chrome que captura el gráfico de TradingView, lo manda (base64) a un webhook n8n y lo analiza con GPT-4o-mini de visión, con un disclaimer de riesgo. ([GitHub Shubeetheanalyst](https://github.com/Shubeetheanalyst/tradingview-chart-analyzer))

**Pros**
- ✅ **Cero plan de pago** de TradingView: no toca alertas ni webhooks; lee la página directamente.
- ✅ **Cero servidor / cero hosting:** todo ocurre en el navegador del usuario.
- ✅ **Recupera la visión:** si captura la imagen y usa un modelo de visión, "ve" velas, patrones y dibujos
  que Pine no puede leer.
- ✅ **Es exactamente lo que el usuario ya tiene** (FinScope): la curva de aprendizaje es nula porque ya sabe
  instalarla y configurar Gemini.
- ✅ Funciona "bajo demanda" (cuando el usuario aprieta un botón) — ideal para alguien no técnico.

**Cons / límites**
- ⚠️ El gráfico de TradingView es un **`<canvas>`**: el DOM **no** da los valores píxel a píxel; por eso el
  scraping de texto se limita a la leyenda/cabecera y hay que apoyarse en datos externos (Yahoo) o en la
  **imagen**. Es justo el "Límite conocido" que el propio README de FinScope documenta.
- ⚠️ Es **bajo demanda**, no automático 24/7: necesita que la pestaña esté abierta y, normalmente, un clic.
  No sustituye a una alerta que dispara sola de madrugada.
- ⚠️ El scraping del DOM puede romperse si TradingView cambia su maquetación.

> **Veredicto (a): SÍ, es la opción más realista para "gratis"** para un usuario no técnico, porque elimina
> por completo la necesidad de plan de pago, de servidores y de webhooks. Es el camino que FinScope ya recorre.

---

## (b) Servidor LOCAL expuesto con ngrok / cloudflared (recibir webhooks sin hosting de pago)

**Cómo funciona.** Levantas un mini-servidor en tu PC (p. ej. Flask en Python) que escucha POSTs, y lo
"expones" a Internet con un túnel:
- `ngrok http 5000` → te da una URL pública `https://abc123.ngrok.io` que apuntas en el campo Webhook URL.
- `cloudflared tunnel --url http://localhost:3000` → subdominio `*.trycloudflare.com`, **sin cuenta** y
  **sin límite de ancho de banda**, los túneles **no caducan**.

Fuentes: [ngrok vs cloudflared (DEV)](https://dev.to/aryan_shourie/secure-tunneling-explained-ngrok-vs-cloudflared-mcl),
[recibir webhooks de TradingView en local (Zerodha QnA)](https://tradingqna.com/t/receive-tradingview-webhooks-locally/182847),
[tradingview-webhooks-bot](https://github.com/maginso/tradingview-webhooks-bot),
[TV connector — correr en PC local](https://tv-connector.gitbook.io/docs/setup/run-on-local-pc).

**Pros**
- ✅ El **túnel** sí es gratis (cloudflared incluso sin cuenta y sin caducidad; ngrok gratis con cuenta).
- ✅ Sin coste de servidor en la nube.

**Cons (decisivos para un no técnico)**
- ❌ **NO resuelve el problema raíz:** los webhooks de TradingView **siguen exigiendo plan de pago**. El túnel
  solo te da la URL que recibe; si TradingView no te deja poner webhooks, esto no aplica. (Sirve para alertas
  *por email* reconvertidas a webhook, lo que añade aún más piezas.)
- ❌ Exige instalar Python, escribir/copiar un servidor Flask, abrir terminal, dejar el PC encendido y
  arrancar el túnel cada vez. La guía local se califica literalmente "💀💀 (muy difícil)".
  ([soranoo — getting started](https://github.com/soranoo/TradingView-Free-Webhook-Alerts/blob/main/docs/gettingstarted.md))
- ❌ ngrok gratis cambia de URL y/o "se cae cada 8 horas" si no creas cuenta.

> **Veredicto (b): NO apto para usuario no técnico.** El túnel es gratis, pero el cuello de botella (webhooks
> de pago) y el montaje (Python + servidor + terminal) lo descartan. Es la vía de un perfil developer.

---

## (c) Servicios TERCEROS gratuitos (TradingView → Telegram / Discord)

Hay dos sub-caminos muy distintos:

### c.1 — Webhook nativo a Telegram/Discord (gratis **pero requiere plan de pago de TradingView**)
TradingView puede mandar la alerta directamente a un bot de Telegram (creado con **@BotFather**) o a un
webhook de Discord, sin intermediarios y "gratis"… **siempre que tengas webhooks**, es decir, plan de pago.
([QuantNomad — Telegram 100% free](https://quantnomad.com/how-to-connect-tradingview-alerts-to-telegram-bots-100-free/),
[fabston/TradingView-Webhook-Bot](https://github.com/fabston/TradingView-Webhook-Bot),
[MasDenk/TradingViewTelegram](https://github.com/MasDenk/TradingViewTelegram)).
→ Mismo problema que (b): el "gratis" presupone webhooks de pago.

### c.2 — Extensión que intercepta el popup de la alerta (sin webhook, sin plan de pago)
**Profit Robots** ofrece una **extensión de Chrome** que, con TradingView abierto, **intercepta las ventanas
emergentes (popups)** de las alertas y **reenvía** ese texto a Telegram/Discord — **sin webhooks** y por tanto
**sin necesitar plan de pago**. ([Profit Robots — Notifications for TradingView](https://profitrobots.com/Home/NotificationsTradingView)).
Esto es, en el fondo, **el mismo enfoque que (a)**: una extensión de navegador como puente.

**Pros**
- ✅ c.2 evita el plan de pago (intercepta en la página, no usa webhooks).
- ✅ Telegram/Discord son canales que un no técnico ya conoce.

**Cons**
- ⚠️ c.1 vuelve a chocar con el muro del plan de pago.
- ⚠️ Estos servicios mandan **texto** de la alerta, **no análisis de IA** ni la **imagen** del gráfico. Para
  meter IA por en medio harías falta un paso más (un bot que reciba el mensaje y llame a un modelo).
- ⚠️ La ruta "alerta por email gratis → servicio que lee el inbox → webhook → IA" (TV-Hub, AlgoWay,
  TradingView-Free-Webhook-Alerts) existe, pero **suma muchas piezas** y configurar el lector de correo /
  Apps Script no es trivial. ([TV-Hub](https://www.tv-hub.org/guide/tradingview-alerts-setup),
  [AlgoWay](https://algoway.trade/blog/tradingview-free-webhook-alerts.html),
  [soranoo/TradingView-Free-Webhook-Alerts](https://github.com/soranoo/TradingView-Free-Webhook-Alerts)).

> **Veredicto (c):** útil para **notificar** a Telegram/Discord, pero **no es "TradingView ↔ IA"** por sí solo,
> y la variante verdaderamente gratis (c.2) acaba siendo otra **extensión de navegador** → refuerza la opción (a).

---

## (d) Capturar el SNAPSHOT del gráfico y mandarlo a un modelo de VISIÓN — "recuperar la visión que Pine no tiene"

**Cómo funciona.** TradingView tiene un **botón de cámara** arriba del gráfico que genera un **snapshot**.
Te deja **descargar la imagen**, **copiarla al portapapeles**, o **copiar un enlace** a una imagen pública
**permanente** (tipo `s3.tradingview.com/snapshots/.../xxxx.png`) que **no caduca**.
([Doc oficial — compartir snapshot](https://www.tradingview.com/support/solutions/43000482537-how-do-i-take-a-snapshot-and-share-it-afterwards/)).
Esa imagen (o su URL) se manda a un modelo de visión gratuito/barato para que la "lea".

- En **alertas**, los servicios de pago (p. ej. **Alertatron**, **CHART-IMG**) pueden **adjuntar el snapshot**
  automáticamente; CHART-IMG incluso ofrece una **API REST** que devuelve la URL de la imagen del gráfico.
  ([Alertatron — capturar gráfico en alertas](https://alertatron.com/docs/how-to-capture-a-chart-with-your-tradingview-alerts),
  [CHART-IMG — snapshot vía REST](https://chart-img.medium.com/tradingview-snapshot-with-rest-api-part1-74f4d8403015),
  [abinthomasonline/tradingview-image-alert](https://github.com/abinthomasonline/tradingview-image-alert)).
- En **plan gratuito**, el snapshot manual (botón de cámara → "Copiar imagen" / "Copiar enlace") **sí está
  disponible**; lo que no es gratis es la **automatización** del adjunto en cada alerta.

**El modelo de visión.** Aquí está el matiz importante de 2026:
- **Gemini 2.0 Flash YA NO existe:** descontinuado y **apagado el 1 de junio de 2026**. El sustituto gratuito
  con visión es **Gemini 2.5 Flash** (o **3 Flash**), que en el **free tier** es "Free of charge" para
  entrada/salida y **lee imágenes**. ([Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)).
- **Cuotas del free tier (2026):** del orden de **10 req/min y ~1.500 req/día** para los modelos Flash
  gratuitos — suficiente para uso manual de una persona. ([Rate limits](https://ai.google.dev/gemini-api/docs/rate-limits),
  [Gemini Free Tier 2026](https://pecollective.com/tools/gemini-free-tier-guide/)).

**Pros**
- ✅ **Recupera la visión real** del gráfico: patrones de velas, líneas, formas — lo que Pine no puede leer.
- ✅ El snapshot manual y la copia de imagen/enlace **funcionan en plan gratuito**.
- ✅ El modelo de visión Flash es **gratis** (con cuota) y barato si se excede.

**Cons**
- ⚠️ La **automatización** del snapshot en cada alerta es de **pago** (Alertatron/CHART-IMG/plan TradingView).
  En gratis, alguien (o la extensión) tiene que disparar la captura.
- ⚠️ Pegar enlaces/imágenes y llamar a una API a mano es engorroso para un no técnico **si no hay una
  extensión que lo automatice**. → De nuevo todo apunta a empaquetarlo dentro de la extensión (a).
- ⚠️ Mantener el nombre del modelo al día (ya no `gemini-2.0-flash`).

> **Veredicto (d):** es la pieza que **da "ojos"** a la IA y encaja perfecto **dentro** de la extensión (a):
> en vez de copiar la URL del snapshot a mano, la extensión captura el gráfico (`captureVisibleTab` o el
> snapshot de TradingView) y lo manda a **Gemini 2.5 Flash** de visión. (a) + (d) = la combinación ganadora.

---

## Comparativa rápida

| Vía | ¿Evita plan de pago TV? | ¿Aporta IA/visión? | ¿Sin servidor? | Dificultad (no técnico) |
|---|---|---|---|---|
| **(a) Extensión navegador (DOM + captura)** | ✅ Sí | ✅ Sí (con visión) | ✅ Sí | 🟢 Baja (ya usa FinScope) |
| (b) Servidor local + ngrok/cloudflared | ❌ No (webhooks de pago) | Depende | ❌ No | 🔴 Alta |
| (c.1) Webhook → Telegram/Discord | ❌ No (de pago) | ❌ Solo texto | ✅/❌ | 🟡 Media |
| (c.2) Extensión que intercepta popup | ✅ Sí | ❌ Solo texto | ✅ Sí | 🟢 Baja |
| **(d) Snapshot → modelo de visión** | ✅ Sí (manual) | ✅ Sí (visión) | ✅ Sí | 🟢 Baja **si va dentro de (a)** |

---

## Recomendación final

Para un usuario **no técnico que NO quiere pagar el plan de TradingView**, la mejor vía es **(a) la extensión
de navegador, combinada con (d) la captura del gráfico hacia un modelo de visión gratuito** — es decir,
**exactamente lo que FinScope ya es**, llevándolo un paso más allá:

1. **Por qué (a)+(d) y no las demás:** elimina de raíz el muro del plan de pago (no toca webhooks ni alertas
   automatizadas), **no necesita servidores, túneles ni terminal**, y la captura de imagen + modelo de visión
   le devuelve a la IA la "vista" que Pine no tiene. (b) y (c.1) tropiezan con que los **webhooks de
   TradingView son de pago**; (c.2) acaba siendo, de nuevo, una extensión de navegador.
2. **Acción concreta sobre FinScope:** ya hace el scraping del DOM y usa Gemini. El upgrade es **(i)** capturar
   la imagen del gráfico con `chrome.tabs.captureVisibleTab` (o el snapshot de TradingView) y mandarla al
   modelo de **visión**, y **(ii)** actualizar el modelo: **`gemini-2.0-flash` quedó apagado el 1-jun-2026**;
   usar **`gemini-2.5-flash`** (o 3 Flash), que es gratis con visión.
3. **Límite honesto:** es **bajo demanda** (con la pestaña abierta y un clic), no una alerta automática 24/7.
   Para alertas autónomas de madrugada sí haría falta plan de pago de TradingView o el daemon de Python que el
   usuario ya tiene aparte. Pero para "ver el gráfico y que la IA lo lea sin pagar", (a)+(d) es la vía limpia.

---

### Fuentes (URLs citadas)

- TradingView — Cómo configurar webhooks (oficial): https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/
- TradingView — Compartir snapshot (oficial): https://www.tradingview.com/support/solutions/43000482537-how-do-i-take-a-snapshot-and-share-it-afterwards/
- TradingView Hub — Alertas 2026 (webhooks = Plus+): https://www.tv-hub.org/guide/tradingview-alerts-setup
- Tickerly — Qué plan de TradingView elegir 2026: https://tickerly.net/best-tradingview-plan/
- QuantRoutine — Free vs Pro (5 planes): https://quantroutine.com/tools/tradingview-free-vs-pro/
- MDN — tabs.captureVisibleTab(): https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/captureVisibleTab
- Tutorial captura de tab (MV3): https://medium.com/@chandanaug13/chrome-extension-capture-tab-tutorial-b4a7960a06ae
- Ejemplo MV3 screenshot (GitHub): https://github.com/hacess/chrome-extension-manifestv3-screenshot
- Screenshot to AI (Chrome Web Store): https://chromewebstore.google.com/detail/screenshot-to-ai/jhlolbkodlggdbhijicplfhcpigdjoij
- tradingview-chart-analyzer (extensión + n8n + GPT-4o-mini visión): https://github.com/Shubeetheanalyst/tradingview-chart-analyzer
- ngrok vs cloudflared (DEV): https://dev.to/aryan_shourie/secure-tunneling-explained-ngrok-vs-cloudflared-mcl
- Recibir webhooks de TradingView en local (Zerodha QnA): https://tradingqna.com/t/receive-tradingview-webhooks-locally/182847
- tradingview-webhooks-bot (GitHub): https://github.com/maginso/tradingview-webhooks-bot
- TV connector — correr en PC local: https://tv-connector.gitbook.io/docs/setup/run-on-local-pc
- soranoo/TradingView-Free-Webhook-Alerts (vía email→webhook): https://github.com/soranoo/TradingView-Free-Webhook-Alerts
- soranoo — getting started (dificultad local "💀💀"): https://github.com/soranoo/TradingView-Free-Webhook-Alerts/blob/main/docs/gettingstarted.md
- AlgoWay — webhook gratis vía email: https://algoway.trade/blog/tradingview-free-webhook-alerts.html
- Profit Robots — extensión que intercepta popups → Telegram/Discord: https://profitrobots.com/Home/NotificationsTradingView
- QuantNomad — TradingView → Telegram 100% free: https://quantnomad.com/how-to-connect-tradingview-alerts-to-telegram-bots-100-free/
- fabston/TradingView-Webhook-Bot: https://github.com/fabston/TradingView-Webhook-Bot
- MasDenk/TradingViewTelegram: https://github.com/MasDenk/TradingViewTelegram
- Alertatron — capturar gráfico en alertas: https://alertatron.com/docs/how-to-capture-a-chart-with-your-tradingview-alerts
- CHART-IMG — snapshot vía REST API (Part 1): https://chart-img.medium.com/tradingview-snapshot-with-rest-api-part1-74f4d8403015
- abinthomasonline/tradingview-image-alert: https://github.com/abinthomasonline/tradingview-image-alert
- Gemini API — Pricing (free tier Flash con visión; 2.0 Flash apagado 1-jun-2026): https://ai.google.dev/gemini-api/docs/pricing
- Gemini API — Rate limits (cuotas free tier): https://ai.google.dev/gemini-api/docs/rate-limits
- Gemini Free Tier 2026 (resumen cuotas): https://pecollective.com/tools/gemini-free-tier-guide/
