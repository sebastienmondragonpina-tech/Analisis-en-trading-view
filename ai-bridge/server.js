/* PineScope — BRIDGE de IA externa (Node + Express)
 *
 * FLUJO: indicador Pine emite una alerta -> TradingView envía un webhook (JSON) aquí
 * -> validamos un secreto compartido -> construimos un prompt de analista financiero
 * (método VELAS JAPONESAS: Tendencia + Nivel + Señal) -> llamamos a la IA
 * (anthropic | openai | gemini, según AI_PROVIDER) -> reenviamos el texto a Telegram.
 *
 * Pine NO puede llamar a una IA por sí mismo; este servidor es el puente.
 *
 * Arranque:   npm install  &&  npm start
 * Endpoint:   POST /webhook
 * Salud:      GET  /            -> "PineScope AI Bridge OK"
 */

'use strict';

const express = require('express');

// fetch nativo en Node >=18. Si corres Node 16, instala node-fetch y descomenta:
// const fetch = (...a) => import('node-fetch').then(({ default: f }) => f(...a));
const fetchFn = (typeof fetch !== 'undefined')
  ? fetch
  : (...a) => import('node-fetch').then(({ default: f }) => f(...a));

// ---------- Config (variables de entorno, ver .env.example) ----------
// Carga .env si existe (sin dependencia: parser mínimo). Así no obligamos a instalar dotenv.
loadDotEnv();

const CFG = {
  provider: (process.env.AI_PROVIDER || 'anthropic').toLowerCase(),
  anthropicKey: process.env.ANTHROPIC_API_KEY || '',
  openaiKey: process.env.OPENAI_API_KEY || '',
  geminiKey: process.env.GEMINI_API_KEY || '',
  anthropicModel: process.env.ANTHROPIC_MODEL || 'claude-haiku-4-5-20251001',
  openaiModel: process.env.OPENAI_MODEL || 'gpt-4o-mini',
  geminiModel: process.env.GEMINI_MODEL || 'gemini-2.0-flash',
  tgToken: process.env.TELEGRAM_BOT_TOKEN || '',
  tgChat: process.env.TELEGRAM_CHAT_ID || '',
  secret: process.env.WEBHOOK_SECRET || '',
  port: parseInt(process.env.PORT || '8080', 10),
  timeoutMs: parseInt(process.env.AI_TIMEOUT_MS || '45000', 10), // ~45s
};

// ---------- Chuleta del método de velas (skill velas-japonesas) ----------
// Condensada a propósito: "enseña" Tendencia+Nivel+Señal a la IA sin alargar el prompt.
const VELAS = `MÉTODO VELAS JAPONESAS (aplícalo): 1) TENDENCIA = estructura (alcista: máximos y mínimos más altos; bajista: más bajos; o lateral/caótico). 2) NIVEL = soportes (DEBAJO del precio) y resistencias (ENCIMA), medias 50/200, zonas. 3) SEÑAL = patrón de vela EN un nivel y A FAVOR de la tendencia (nunca un patrón aislado). Patrones: engulfing alcista/bajista, martillo=pin bar alcista (fondo/soporte), estrella fugaz=pin bar bajista (techo/resistencia), doji (indecisión/giro), estrella de la mañana/de la tarde, harami/inside bar, pinzas. El marco grande manda (semanal>diario>intradía). Tras una ruptura, resistencia rota->soporte (y viceversa). COHERENCIA: soporte<precio<resistencia; el sesgo alcista/bajista debe cuadrar con precio vs SMA50/200 y la tendencia multi-temporalidad.`;

// ---------- Prompt del analista a partir del JSON de la alerta ----------
function buildPrompt(alert) {
  return `Eres un analista financiero experto en VELAS JAPONESAS. ${VELAS}
Recibes una ALERTA disparada por un indicador de TradingView (Pine Script) con los datos de abajo (símbolo, temporalidad, precio, señal, niveles, indicadores, etc.). Interpreta la alerta con el método Tendencia+Nivel+Señal y explícala como un analista profesional, EN ESPAÑOL.
Responde con un mensaje BREVE y claro listo para enviar por Telegram (texto plano, sin markdown pesado; puedes usar emojis sobrios y saltos de línea). Estructura sugerida:
- Una primera línea-resumen en MAYÚSCULAS con el veredicto.
- 3 a 5 viñetas con: tendencia/estructura, el nivel donde ocurre la señal, el patrón o señal de la vela, y el riesgo.
- Una línea "A vigilar:" con el nivel o señal clave.
- Cierra recordando que es análisis educativo, NO recomendación de compra/venta.
Usa los números reales de la alerta; si falta un dato, no lo inventes. Sé conciso (máx ~12 líneas).
DATOS DE LA ALERTA (JSON):
${JSON.stringify(alert)}`;
}

// ---------- fetch con timeout (AbortController) ----------
async function fetchTO(url, opts, ms) {
  const ctrl = new AbortController();
  const to = setTimeout(() => ctrl.abort(), ms || CFG.timeoutMs);
  try {
    return await fetchFn(url, Object.assign({}, opts, { signal: ctrl.signal }));
  } finally {
    clearTimeout(to);
  }
}

// ---------- Extractores defensivos de la respuesta de cada IA ----------
function pickClaude(j) {
  const t = (j && Array.isArray(j.content) ? j.content : []).map((b) => b.text || '').join('');
  if (!t) throw new Error('Claude sin contenido: ' + JSON.stringify((j && (j.error || j.stop_reason)) || j || {}).slice(0, 200));
  return t;
}
function pickOpenAI(j) {
  const m = j && j.choices && j.choices[0] && j.choices[0].message;
  const t = m && m.content;
  if (!t) throw new Error('OpenAI sin contenido: ' + JSON.stringify((j && j.error) || j || {}).slice(0, 200));
  return t;
}
function pickGemini(j) {
  const cand = j && j.candidates && j.candidates[0];
  const parts = cand && cand.content && cand.content.parts;
  const t = (Array.isArray(parts) ? parts : []).map((p) => p.text || '').join('');
  if (!t) throw new Error('Gemini bloqueado/sin contenido: ' + JSON.stringify((j && (j.promptFeedback || j.error)) || j || {}).slice(0, 200));
  return t;
}

// ---------- Llamadas a cada proveedor ----------
async function callClaude(prompt) {
  if (!CFG.anthropicKey) throw new Error('falta ANTHROPIC_API_KEY');
  const res = await fetchTO('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': CFG.anthropicKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({ model: CFG.anthropicModel, max_tokens: 900, messages: [{ role: 'user', content: prompt }] }),
  });
  if (!res.ok) throw new Error('Claude ' + res.status + ': ' + (await res.text()).slice(0, 200));
  return pickClaude(await res.json());
}

async function callOpenAI(prompt) {
  if (!CFG.openaiKey) throw new Error('falta OPENAI_API_KEY');
  const res = await fetchTO('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + CFG.openaiKey, 'content-type': 'application/json' },
    body: JSON.stringify({ model: CFG.openaiModel, temperature: 0.4, messages: [{ role: 'user', content: prompt }] }),
  });
  if (!res.ok) throw new Error('OpenAI ' + res.status + ': ' + (await res.text()).slice(0, 200));
  return pickOpenAI(await res.json());
}

async function callGemini(prompt) {
  if (!CFG.geminiKey) throw new Error('falta GEMINI_API_KEY');
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${CFG.geminiModel}:generateContent?key=${encodeURIComponent(CFG.geminiKey)}`;
  const res = await fetchTO(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: { temperature: 0.4 } }),
  });
  if (!res.ok) throw new Error('Gemini ' + res.status + ': ' + (await res.text()).slice(0, 200));
  return pickGemini(await res.json());
}

async function callAI(prompt) {
  switch (CFG.provider) {
    case 'anthropic':
    case 'claude':
      return callClaude(prompt);
    case 'openai':
      return callOpenAI(prompt);
    case 'gemini':
    case 'google':
      return callGemini(prompt);
    default:
      throw new Error('AI_PROVIDER desconocido: "' + CFG.provider + '" (usa anthropic | openai | gemini)');
  }
}

// ---------- Telegram (Bot API) ----------
async function sendTelegram(text) {
  if (!CFG.tgToken || !CFG.tgChat) throw new Error('faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID');
  const url = `https://api.telegram.org/bot${CFG.tgToken}/sendMessage`;
  // Telegram limita a 4096 caracteres por mensaje.
  const body = { chat_id: CFG.tgChat, text: String(text).slice(0, 4096), disable_web_page_preview: true };
  const res = await fetchTO(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }, 15000);
  if (!res.ok) throw new Error('Telegram ' + res.status + ': ' + (await res.text()).slice(0, 200));
  return res.json();
}

// ---------- Validación del secreto compartido ----------
// El secreto puede llegar de 3 formas (cualquiera vale): header x-webhook-secret,
// ?secret=... en la URL, o un campo "secret" dentro del JSON de la alerta.
function checkSecret(req, alert) {
  if (!CFG.secret) return true; // si no configuraste WEBHOOK_SECRET, no se exige (no recomendado)
  const got = req.get('x-webhook-secret') || req.query.secret || (alert && alert.secret);
  return got === CFG.secret;
}

// ---------- App Express ----------
const app = express();
// TradingView a veces manda el cuerpo como text/plain aunque sea JSON: aceptamos ambos.
app.use(express.json({ limit: '256kb' }));
app.use(express.text({ type: ['text/*', 'application/octet-stream'], limit: '256kb' }));

app.get('/', (_req, res) => res.send('PineScope AI Bridge OK (POST /webhook)'));

app.post('/webhook', async (req, res) => {
  // 1) Parsear el cuerpo (puede venir como objeto ya parseado o como string JSON/plano).
  let alert = req.body;
  if (typeof alert === 'string') {
    const s = alert.trim();
    try { alert = JSON.parse(s); }
    catch (_e) { alert = { mensaje: s }; } // alerta de TradingView en texto plano: la envolvemos
  }
  if (!alert || typeof alert !== 'object') alert = { mensaje: String(req.body || '') };

  // 2) Validar secreto.
  if (!checkSecret(req, alert)) {
    console.warn('[webhook] secreto inválido o ausente');
    return res.status(401).json({ ok: false, error: 'secreto inválido' });
  }

  // 3) Responder YA a TradingView (no debe esperar a la IA). El trabajo sigue en segundo plano.
  res.json({ ok: true, recibido: true });

  // 4) IA + Telegram (con manejo de errores y timeout). Si algo falla, avisamos por Telegram.
  try {
    const prompt = buildPrompt(alert);
    const analisis = await callAI(prompt);
    const symbol = alert.symbol || alert.ticker || alert.simbolo || '';
    const tf = alert.timeframe || alert.interval || alert.tf || '';
    const cabecera = `📈 PineScope — ${symbol}${tf ? ' (' + tf + ')' : ''}\n`;
    await sendTelegram(cabecera + '\n' + analisis);
    console.log('[webhook] análisis enviado a Telegram para', symbol || '(sin símbolo)');
  } catch (e) {
    const msg = String((e && e.message) || e);
    console.error('[webhook] error:', msg);
    // Avisar el fallo por Telegram (best-effort) para que el usuario no se quede a ciegas.
    try { await sendTelegram('⚠️ PineScope: no pude generar el análisis.\nMotivo: ' + msg.slice(0, 300)); }
    catch (_e2) { /* noop: si Telegram también falla, ya quedó en el log */ }
  }
});

app.listen(CFG.port, () => {
  console.log(`PineScope AI Bridge escuchando en http://localhost:${CFG.port}`);
  console.log(`  Proveedor IA: ${CFG.provider} | Telegram chat: ${CFG.tgChat || '(no configurado)'}`);
  if (!CFG.secret) console.warn('  ADVERTENCIA: WEBHOOK_SECRET vacío; cualquiera podría llamar a /webhook.');
});

// ---------- util: parser .env mínimo (evita dependencia dotenv) ----------
function loadDotEnv() {
  try {
    const fs = require('fs');
    const path = require('path');
    const p = path.join(__dirname, '.env');
    if (!fs.existsSync(p)) return;
    const lines = fs.readFileSync(p, 'utf8').split(/\r?\n/);
    for (const line of lines) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const i = t.indexOf('=');
      if (i < 0) continue;
      const k = t.slice(0, i).trim();
      let v = t.slice(i + 1).trim();
      if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
      if (!(k in process.env)) process.env[k] = v;
    }
  } catch (_e) { /* noop */ }
}
