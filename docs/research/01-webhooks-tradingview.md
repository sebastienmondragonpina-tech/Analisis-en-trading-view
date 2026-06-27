# Webhooks de Alertas en TradingView — Investigación a fondo

> **Objetivo**: Entender cómo un indicador de TradingView (Pine Script) puede "hablar" con un servidor externo (y por tanto con una IA externa) mediante **alertas con webhook**.
>
> **Fecha de la investigación**: 2026-06-26
> **Fuentes**: Documentación oficial de TradingView + Pine Script Docs + guías recientes (2024–2026). URLs citadas en cada sección y en *Referencias*.

---

## TL;DR (conclusión rápida)

- **Sí es viable**: TradingView puede enviar un `POST` HTTP a tu servidor cada vez que se dispara una alerta. Ese servidor recibe el cuerpo del mensaje (texto o JSON) y puede reenviarlo a una IA.
- **Requiere pago**: el webhook **NO** está en el plan gratuito. El plan mínimo real para webhooks hoy es **Plus** (algunas guías citan Essential como entrada, pero el camino fiable para automatización es Plus o superior).
- **El flujo**: indicador Pine → `alert()` / `alertcondition()` → al crear la alerta marcas **Webhook URL** en la pestaña *Notifications* → TradingView hace `POST` a tu URL → tu servidor valida y procesa.
- **Limitación clave para IA con visión**: TradingView **no adjunta nativamente una imagen del gráfico en el `POST` del webhook**. El snapshot hay que generarlo aparte (tu servidor o un bot que renderiza el chart).

---

## 1. Cómo se crea una alerta sobre un indicador y se le pone una URL de webhook

### 1.1 Flujo general en la interfaz

1. Tener el indicador Pine Script añadido al gráfico (o usar una condición de precio simple).
2. Abrir el diálogo **Create Alert** (icono de reloj/alarma, o `Alt+A`).
3. En **Condition**, seleccionar el indicador y la condición concreta. Si el script usa `alertcondition()`, esas condiciones aparecen aquí como opciones seleccionables. Si el script usa la función `alert()`, la alerta se dispara desde el propio código (ver sección 2).
4. En **Trigger / frecuencia** elegir cuándo dispara (Once Per Bar, Once Per Bar Close, etc.). Lo más seguro para señales confirmadas es **Once Per Bar Close** (evita repintado intrabar).
5. Ir a la pestaña **Notifications** → activar la casilla **Webhook URL** → pegar la URL HTTPS de tu servidor.
6. En **Message** escribir el cuerpo que se enviará en el `POST` (texto o JSON, con placeholders si aplica).

> "This [webhook] can be enabled when you create an alert. Add the correct URL for your app and we will send a POST request as soon as the alert is triggered."
> — TradingView Blog, *Alerts can now be sent to 1000's of apps* — https://www.tradingview.com/blog/en/webhooks-for-alerts-now-available-14054/

### 1.2 Detalles técnicos del `POST`

- TradingView envía una solicitud **HTTP POST** con el contenido del campo *Message* como cuerpo.
- **Content-Type automático**:
  - Si el mensaje es **JSON válido** → cabecera `application/json`.
  - Si no → cabecera `text/plain`.
- **Puertos**: solo se aceptan **80 y 443**. Otros puertos se rechazan.
- **Timeout**: la solicitud se cancela si tarda más de **~3 segundos** en responder (tu servidor debe responder rápido; haz el trabajo pesado en background).
- **IPv6**: no soportado actualmente (usa IPv4 / dominio con A record).
- **Requisito de cuenta**: el webhook **solo se permite con 2FA (autenticación de dos factores) habilitada**.

> Fuente oficial: *How to configure webhook alerts* — https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/

---

## 2. Formato del mensaje de alerta: placeholders y funciones de Pine

Hay **dos mecanismos** distintos en Pine Script para emitir alertas, y se comportan de forma **muy diferente** respecto a los placeholders. Esto es lo más importante de entender.

### 2.1 `alertcondition()` — placeholders `{{...}}` (mensajes estáticos con sustitución)

- Firma: `alertcondition(condition, title, message)`.
- El argumento `message` debe ser **`const string`** (conocido en compilación) → es **estático**, PERO admite **placeholders** que TradingView reemplaza en tiempo de ejecución.
- Solo funciona en **indicadores** (no en estrategias) y debe declararse en el **ámbito global** (columna 0).
- Genera una *entrada de alerta seleccionable* en el diálogo Create Alert.

**Placeholders disponibles** (sustituidos al dispararse):

| Placeholder | Significado |
|---|---|
| `{{open}}` `{{high}}` `{{low}}` `{{close}}` `{{volume}}` | OHLCV de la barra que dispara la alerta |
| `{{ticker}}` | Símbolo (ej. `AAPL`, `BTCUSD`) |
| `{{exchange}}` | Exchange del símbolo (NASDAQ, NYSE…; para datos retrasados acaba en `_DL`/`_DLY`) |
| `{{interval}}` | Temporalidad del gráfico (1, 5, 60, D…) |
| `{{time}}` | Hora de apertura de la barra (UTC) |
| `{{timenow}}` | Hora actual al dispararse (UTC) |
| `{{plot_0}}` … `{{plot_19}}` | Valores de los `plot()` del script (solo los primeros 20, índices 0–19) |
| `{{plot("Name")}}` | Valor de un plot por su nombre |

> Solo los primeros 20 plots (0–19) son accesibles. Los placeholders son **case-sensitive** (minúsculas exactas).
> Fuentes: Pine Script Docs *Alerts* — https://www.tradingview.com/pine-script-docs/concepts/alerts/ ; *Use standard placeholders* — https://www.tradingcode.net/tradingview/alert-condition-standard-placeholder/ ; *Plot placeholder* — https://www.tradingcode.net/tradingview/alert-condition-plot-placeholder/

### 2.2 `alert()` — función dinámica de Pine v5/v6 (mensajes calculados, SIN placeholders)

- Firma: `alert(message, freq)`.
- El argumento `message` acepta **`series string`** → puedes construir el texto **dinámicamente** con valores calculados del script mediante **concatenación de strings** (`str.tostring(...)`).
- **No procesa placeholders `{{...}}`**: como ya puedes inyectar cualquier valor con código, no los necesita. Si pones `{{close}}` en un `alert()`, se enviaría literal.
- **No** crea una "entrada Message" en el diálogo Create Alert: el mensaje viene del código. En el diálogo eliges la condición "Any alert() function call".
- Funciona en **indicadores Y estrategias**, y se coloca **dentro de bloques condicionales** (`if`).
- Parámetro `freq` (frecuencia):
  - `alert.freq_once_per_bar` (por defecto): una vez por barra, al primer disparo intrabar.
  - `alert.freq_once_per_bar_close`: solo al **cierre** de la barra (recomendado para señales confirmadas).
  - `alert.freq_all`: cada vez que la condición es true (puede disparar varias veces por barra).

**Ejemplo Pine v6 con `alert()` dinámico (ideal para enviar JSON a un servidor/IA):**

```pinescript
//@version=6
indicator("Alerta dinamica para IA")

src = close
fast = ta.sma(src, 9)
slow = ta.sma(src, 21)

if ta.crossover(fast, slow)
    // Construimos un JSON dinámico con valores calculados:
    msg = '{"ticker":"' + syminfo.ticker +
          '","tf":"' + timeframe.period +
          '","signal":"BUY","price":' + str.tostring(close) +
          ',"rsi":' + str.tostring(ta.rsi(src, 14)) + '}'
    alert(msg, alert.freq_once_per_bar_close)
```

Ese `msg` es JSON válido → TradingView lo enviará con `Content-Type: application/json`, listo para que tu servidor lo parsee y lo pase a la IA.

> Fuentes: Pine Script Docs *Alerts* — https://www.tradingview.com/pine-script-docs/concepts/alerts/ ; *FAQ Alerts* — https://www.tradingview.com/pine-script-docs/faq/alerts/ ; CrossTrade *Pine Script variables in alerts* — https://crosstrade.io/blog/using-pine-script-variables

### 2.3 Placeholders de ESTRATEGIA (`{{strategy.*}}`)

Solo aplican a **alertas de estrategias** (`strategy()`), no a indicadores. Útiles para señales de entrada/salida automáticas:

| Placeholder | Significado |
|---|---|
| `{{strategy.order.action}}` | `buy` o `sell` de la orden que dispara |
| `{{strategy.order.contracts}}` | Número de contratos/cantidad de la orden |
| `{{strategy.order.price}}` | Precio de ejecución de la orden |
| `{{strategy.order.id}}` | ID de la orden |
| `{{strategy.position_size}}` | Tamaño de la posición tras la orden |
| `{{strategy.market_position}}` | `long` / `short` / `flat` |
| `{{strategy.order.alert_message}}` | Texto del parámetro `alert_message` de la orden (mensaje a medida por orden) |

> Fuente: Pine Script FAQ *Alerts* — https://www.tradingview.com/pine-script-docs/faq/alerts/

### 2.4 Resumen de cuándo usar cada uno

| | `alertcondition()` | `alert()` | Alerta de estrategia |
|---|---|---|---|
| Tipo de mensaje | Estático con placeholders `{{...}}` | Dinámico (string calculado) | Placeholders `{{strategy.*}}` |
| Placeholders `{{close}}` etc. | Sí | No (usa concatenación) | Sí (+ `{{strategy.*}}`) |
| Funciona en | Indicadores | Indicadores y estrategias | Estrategias |
| **Recomendado para IA** | OK para payload simple | **Mejor**: JSON dinámico flexible | Para trading automático |

---

## 3. Qué planes permiten webhooks, límites de alertas y expiración

### 3.1 ¿Qué plan necesito para webhooks?

- **Plan gratuito (Basic)**: **NO** permite webhooks. (Solo ~1 alerta activa, sin POST a URL externa).
- El blog oficial dice escuetamente: **"Feature available to paid users only."** (https://www.tradingview.com/blog/en/webhooks-for-alerts-now-available-14054/)
- En la práctica (2026), las guías coinciden en que el **plan mínimo fiable para webhooks de automatización es Plus**. Algunas fuentes mencionan Essential como punto de entrada, pero el estándar para automatizar con webhooks es **Plus o superior**.

> Guías 2026: Tickerly — https://tickerly.net/best-tradingview-plan/ ; Supa — https://supa.is/article/tradingview-essential-vs-plus-vs-premium-which-plan-2026 ; TV-Hub — https://www.tv-hub.org/guide/tradingview-alerts-setup

### 3.2 Límites de alertas activas por plan (valores 2026, sujetos a cambios)

| Plan | Alertas activas | Webhooks |
|---|---|---|
| **Basic (Free)** | ~1 | No |
| **Essential** | ~20 | Limitado / no fiable para automatización |
| **Plus** | ~100 | Sí (mínimo recomendado) |
| **Premium** | ~400 (oficial: 800 = 400 price + 400 technical) | Sí |
| **Expert** | ~800 | Sí |
| **Ultimate** | ~2000 (1000 price + 1000 technical) / "ilimitado" según fuente | Sí |

> Nota: TradingView ha reestructurado planes y cifras varias veces. La página oficial actual cita **Premium = 800 alertas activas (400 price + 400 technical)** y **Ultimate = 2000 (1000 + 1000)**. Otras guías resumen con cifras menores por categoría. **Verificar siempre en la página de precios oficial antes de comprar.**
> Fuentes: TradingView *How to get more active alerts* — https://www.tradingview.com/support/solutions/43000690941-how-to-get-more-active-alerts-per-subscription/ ; Pricing — https://www.tradingview.com/pricing/

### 3.3 Expiración de las alertas

- **Máximo por defecto: 2 meses (~60 días)** de vida útil de una alerta.
- En **Premium y Ultimate** existe la opción **"open-ended"** (sin caducidad) → la alerta puede permanecer activa indefinidamente.
- En **Essential / Plus**, las alertas **expiran tras ~2 meses** y hay que recrearlas/reactivarlas.

> "The maximum lifetime of an alert is two months. However, for Premium and Ultimate plans, the open-ended option is available."
> — TradingView *Introduction to alerts* — https://www.tradingview.com/support/solutions/43000520149-introduction-to-tradingview-alerts/

---

## 4. Seguridad: cómo verificar que el POST viene realmente de TradingView

Como la URL del webhook es pública (cualquiera que la conozca podría hacerle POST), hay que **autenticar** que la petición es legítima. Tres capas habituales:

### 4.1 Lista de IPs oficiales de TradingView (allowlist)

TradingView envía los POST desde un conjunto fijo de IPs. Tu servidor (o firewall) puede **rechazar todo lo que no venga de estas IPs**:

```
52.89.214.238
34.212.75.30
54.218.53.128
52.32.178.7
```

> Estas IPs aparecen en un tooltip del diálogo de webhook y en la documentación oficial.
> Fuente oficial: *How to configure webhook alerts* — https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/
>
> **Cuidado**: las IPs pueden cambiar con el tiempo; consúltalas en el tooltip del diálogo de alerta antes de fijar un firewall estricto.

### 4.2 Secreto compartido en el payload (recomendado, lo más robusto)

Como TradingView **no firma criptográficamente** el webhook (no hay HMAC nativo como en Stripe/GitHub), la técnica estándar es **incluir un token secreto dentro del cuerpo del mensaje** y verificarlo en el servidor:

```json
{
  "secret": "MI_TOKEN_LARGO_Y_ALEATORIO",
  "ticker": "{{ticker}}",
  "price": "{{close}}",
  "signal": "BUY"
}
```

El servidor compara `secret` con el valor esperado y descarta cualquier POST que no lo traiga. Combinar **IP allowlist + secreto en payload + HTTPS** da una defensa razonable.

### 4.3 Buenas prácticas adicionales

- **HTTPS obligatorio** en tu endpoint (el secreto viaja en el cuerpo).
- **No** incluyas credenciales reales, contraseñas o API keys de tu bróker en el mensaje del webhook (TradingView lo advierte explícitamente).
- URL "secreta"/no adivinable (path con un UUID) como capa extra.
- Responde rápido (<3 s) con 200 y procesa en background.

> Advertencia oficial: "Don't include sensitive information such as login credentials or passwords in the webhook body."
> — https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/

---

## 5. ¿Puede TradingView adjuntar un snapshot/imagen del gráfico en la alerta? (relevante para IA con visión)

**Respuesta corta: NO de forma nativa en el webhook.**

- El `POST` del webhook lleva **solo el texto/JSON** del campo *Message*. **No** incluye una imagen del gráfico ni un binario adjunto.
- TradingView **sí** puede generar un **snapshot del gráfico** en otros canales:
  - En las **notificaciones por email / app / popup** puede mostrar una miniatura del gráfico.
  - Existe la función "Get snapshot" que produce una **URL de imagen** del chart (`https://www.tradingview.com/x/...`).
- Para que tu IA con visión reciba una imagen, las opciones reales son:
  1. **Tu servidor renderiza el chart**: al recibir el webhook (con ticker + timeframe), un proceso headless (Selenium/Playwright) abre el gráfico y captura un screenshot, que luego pasas a la IA. Es el patrón de los bots open-source de "TradingView → Telegram con snapshot".
  2. **Incluir el chart ID / chart URL en el payload** y que tu servicio pida el snapshot a TradingView. Hay parámetros como `loginRequired` (para charts privados o scripts invite-only) y `delivery=asap` (envía el texto ya y la imagen después, porque generar el snapshot tarda).
  3. **Servicios/bots de terceros** (Alertatron, etc.) que ya implementan la captura del chart y la adjuntan al mensaje.

> Referencias prácticas:
> - Alertatron *How to capture a chart with your TradingView alerts* — https://alertatron.com/docs/how-to-capture-a-chart-with-your-tradingview-alerts
> - GitHub `abinthomasonline/tradingview-image-alert` — https://github.com/abinthomasonline/tradingview-image-alert
> - GitHub `rasoul707/TradingView-Webhook-Alert-SnapShot-Bot` — https://github.com/rasoul707/TradingView-Webhook-Alert-SnapShot-Bot
> - Trendoscope *Telegram webhook con chart snapshot* — https://www.tradingview.com/chart/BTCUSDT/TIWkU55b-Tradingview-Telegram-Webhook-Bot-with-Chart-Snapshot-Revised/

**Conclusión para IA con visión**: el webhook por sí solo da **datos numéricos/JSON**, no imagen. Si quieres que la IA "vea" el gráfico, tendrás que **generar el snapshot por tu cuenta** (renderizado headless en tu servidor) a partir de los datos del webhook.

---

## 6. Arquitectura recomendada para "indicador TradingView → IA externa"

```
[Indicador Pine v6]
   alert(msgJSON, alert.freq_once_per_bar_close)
        │  (POST application/json)
        ▼
[Tu servidor / webhook receiver]   ← valida IP allowlist + secret + HTTPS
   1. Verifica secreto
   2. (Opcional) Renderiza snapshot del chart (headless) para visión
   3. Llama a la IA (texto + imagen opcional)
   4. Responde 200 en <3 s; trabajo pesado en background
        │
        ▼
[Acción]  → análisis IA → Telegram / toast / log / orden
```

Recomendaciones concretas:
- Usar **`alert()` con JSON dinámico** (sección 2.2) en vez de `alertcondition()` con placeholders: más flexible y limpio para construir el payload que consume la IA.
- Disparar **once per bar close** para señales confirmadas (no repintado).
- **Plus** como plan mínimo; **Premium** si quieres que las alertas **no expiren** (open-ended) y más capacidad.
- Seguridad: **HTTPS + secreto en payload + IP allowlist + 2FA en la cuenta**.
- Para visión, generar el snapshot en tu servidor (no esperar que TradingView lo adjunte).

---

## Referencias (URLs)

**Documentación oficial de TradingView**
- Configurar webhook alerts: https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/
- Introducción a las alertas (expiración, planes): https://www.tradingview.com/support/solutions/43000520149-introduction-to-tradingview-alerts/
- Más alertas activas por suscripción (límites por plan): https://www.tradingview.com/support/solutions/43000690941-how-to-get-more-active-alerts-per-subscription/
- Blog oficial — Webhooks para alertas: https://www.tradingview.com/blog/en/webhooks-for-alerts-now-available-14054/
- Precios: https://www.tradingview.com/pricing/

**Pine Script (oficial)**
- Concepts / Alerts (alert() vs alertcondition(), freq): https://www.tradingview.com/pine-script-docs/concepts/alerts/
- FAQ / Alerts (placeholders, strategy.*): https://www.tradingview.com/pine-script-docs/faq/alerts/
- Reference Manual v6: https://www.tradingview.com/pine-script-reference/v6/

**Placeholders y variables (guías técnicas)**
- Standard placeholders: https://www.tradingcode.net/tradingview/alert-condition-standard-placeholder/
- Plot placeholder: https://www.tradingcode.net/tradingview/alert-condition-plot-placeholder/
- CrossTrade — variables Pine en alertas: https://crosstrade.io/blog/using-pine-script-variables

**Planes / webhooks (guías 2026)**
- Tickerly — qué plan elegir (bots): https://tickerly.net/best-tradingview-plan/
- Supa — Essential vs Plus vs Premium 2026: https://supa.is/article/tradingview-essential-vs-plus-vs-premium-which-plan-2026
- TV-Hub — setup de alertas 2026: https://www.tv-hub.org/guide/tradingview-alerts-setup

**Snapshot / imagen del gráfico**
- Alertatron — capturar chart con alertas: https://alertatron.com/docs/how-to-capture-a-chart-with-your-tradingview-alerts
- GitHub tradingview-image-alert: https://github.com/abinthomasonline/tradingview-image-alert
- GitHub Webhook-Alert-SnapShot-Bot: https://github.com/rasoul707/TradingView-Webhook-Alert-SnapShot-Bot
- Trendoscope — bot Telegram con snapshot: https://www.tradingview.com/chart/BTCUSDT/TIWkU55b-Tradingview-Telegram-Webhook-Bot-with-Chart-Snapshot-Revised/
