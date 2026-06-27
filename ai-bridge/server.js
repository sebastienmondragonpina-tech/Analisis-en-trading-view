/* PineScope — BRIDGE de IA externa (Node + Express)  ·  JSON v2.0
 *
 * FLUJO NATIVO:
 *   El Dashboard de PineScope (Pine Script v6) calcula TODO de forma nativa sobre los
 *   datos de TradingView (estocastico/MACD/tendencia por los 9 marcos, resumen tactico
 *   INTRADIA/SWING con motor+confirmacion, niveles S/R y prediccion por reglas) y lo
 *   exporta como un JSON de UNA linea via alert(). Una alerta-webhook de TradingView
 *   manda ese JSON a este servidor, que:
 *     1) valida el 'secret' compartido,
 *     2) arma un PROMPT de analista profesional que aprovecha TODOS esos datos nativos
 *        (multi-temporalidad, motor, confirmacion, divergencias intradia vs swing,
 *        niveles y prediccion) con el metodo velas-japonesas (Tendencia+Nivel+Senal),
 *     3) llama a la IA (anthropic | openai | gemini, segun AI_PROVIDER),
 *     4) reenvia el veredicto + gestion de riesgo a Telegram.
 *
 *   Pine NO puede llamar a una IA ni "ver" la imagen del grafico: este servidor es el
 *   puente, y aqui la IA NO mira pixeles — recibe los DATOS NATIVOS EXACTOS que
 *   describen la grafica. (Para que la IA "vea" la imagen del grafico esta la extension
 *   FinScope, que captura el chart y usa vision. Aqui los datos son nativos y precisos.)
 *
 * Limite de 3s de TradingView: validamos y respondemos 200 al instante; la IA + Telegram
 * corren APARTE (setImmediate, fuera del ciclo de la respuesta HTTP).
 *
 * Arranque:   npm install  &&  npm start
 * Endpoint:   POST /webhook
 * Salud:      GET  /            -> "PineScope AI Bridge v2 OK"
 */

'use strict';

const express = require('express');

// fetch nativo en Node >=18. Si corres Node 16, instala node-fetch (ver package.json).
const fetchFn = (typeof fetch !== 'undefined')
  ? fetch
  : (...a) => import('node-fetch').then(({ default: f }) => f(...a));

// ---------- Config (variables de entorno, ver .env.example) ----------
loadDotEnv(); // parser .env minimo (sin dependencia dotenv)

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

// Orden fijo de los 9 marcos (igual que el SPEC).
const TF_ORDER = ['1m', '3m', '5m', '15m', '30m', '1H', '2H', '4H', 'Diario'];

// ---------- Chuleta del metodo de velas (skill velas-japonesas) ----------
// Condensada a proposito: "ensena" Tendencia+Nivel+Senal a la IA sin alargar el prompt.
const VELAS = `METODO VELAS JAPONESAS (aplicalo): 1) TENDENCIA = estructura (alcista: maximos y minimos mas altos; bajista: mas bajos; o lateral/caotico); el marco GRANDE manda (Diario>4H>1H>intradia). 2) NIVEL = soportes (DEBAJO del precio) y resistencias (ENCIMA), zonas. 3) SENAL = confluencia EN un nivel y A FAVOR de la tendencia (nunca una senal aislada). COHERENCIA OBLIGATORIA: soporte<precio<resistencia; el sesgo debe cuadrar con la tendencia multi-temporalidad; NO etiquetes una resistencia como soporte ni des un veredicto alcista contra una estructura claramente bajista. Entrar al INICIO del impulso (tras retroceso a un nivel), no en mitad del retroceso. R:R minimo 2:1; riesgo por operacion <=2% del capital.`;

// ---------- Lectura del payload v2.0 -> texto legible para la IA ----------
// Convierte el JSON nativo en un "briefing" tabular y resaltamos divergencias para que la
// IA no tenga que adivinar nada: ya le damos masticado motor, confirmacion y conflictos.
function tfRows(tf) {
  if (!tf || typeof tf !== 'object') return '(sin tabla por marco)';
  const lines = [];
  for (const k of TF_ORDER) {
    const c = tf[k];
    if (!c) continue;
    const trend = c.trend != null ? c.trend : '?';
    const sK = c.stochK != null ? Number(c.stochK).toFixed(1) : '-';
    const sEst = c.stochEstado != null ? c.stochEstado : '-';
    const sFz = c.stochFuerza != null ? c.stochFuerza : '-';
    const mH = c.macdHist != null ? Number(c.macdHist).toFixed(2) : '-';
    const mEst = c.macdEstado != null ? c.macdEstado : '-';
    const mFz = c.macdFuerza != null ? c.macdFuerza : '-';
    lines.push(`  ${k.padEnd(6)} | tend ${trend} | STOCH %K=${sK} ${sEst}/${sFz} | MACD hist=${mH} ${mEst}/${mFz}`);
  }
  return lines.length ? lines.join('\n') : '(sin tabla por marco)';
}

function grupoTxt(nombre, g) {
  if (!g || typeof g !== 'object') return `${nombre}: (sin datos)`;
  return `${nombre}: tendencia=${g.tendencia != null ? g.tendencia : '?'} | score=${g.score != null ? g.score : '?'} | motor=${g.motor != null ? g.motor : '?'} (el marco que manda) | confirmacion=${g.confirmacion != null ? g.confirmacion : '?'} | lectura nativa="${g.lectura != null ? g.lectura : ''}"`;
}

// Divergencia entre intradia y swing: el conflicto mas accionable del dashboard.
function divergencia(a) {
  const i = a && a.intradia && a.intradia.tendencia;
  const s = a && a.swing && a.swing.tendencia;
  if (!i || !s) return '';
  const alc = (x) => /ALCISTA/i.test(x) && !/BAJISTA/i.test(x);
  const baj = (x) => /BAJISTA/i.test(x);
  if (alc(i) && baj(s)) return 'DIVERGENCIA: intradia ALCISTA contra swing BAJISTA -> probable rebote dentro de tendencia mayor bajista (largos finos y rapidos, el swing manda).';
  if (baj(i) && alc(s)) return 'DIVERGENCIA: intradia BAJISTA dentro de swing ALCISTA -> probable retroceso; vigilar fin de caida para sumarse al swing alcista.';
  if (alc(i) && alc(s)) return 'ALINEACION ALCISTA: intradia y swing apuntan arriba (mayor probabilidad).';
  if (baj(i) && baj(s)) return 'ALINEACION BAJISTA: intradia y swing apuntan abajo (mayor probabilidad).';
  return '';
}

function nivelesTxt(a) {
  const n = (a && a.niveles) || {};
  const p = (a && a.prediccion) || {};
  return [
    `Precio actual: ${a && a.price != null ? a.price : '?'} | Marco del grafico: ${a && a.chartTF != null ? a.chartTF : '?'} | Semaforo: ${a && a.semaforo != null ? a.semaforo : '?'} | scoreGlobal: ${a && a.scoreGlobal != null ? a.scoreGlobal : '?'}`,
    `Niveles nativos: soporte=${n.soporte != null ? n.soporte : '?'} (debajo) | resistencia=${n.resistencia != null ? n.resistencia : '?'} (encima)`,
    `Prediccion por reglas (orientativa, sin IA): objetivoSube=${p.objetivoSube != null ? p.objetivoSube : '?'} | objetivoBaja=${p.objetivoBaja != null ? p.objetivoBaja : '?'}`,
  ].join('\n');
}

function briefing(a) {
  const div = divergencia(a);
  return [
    nivelesTxt(a),
    '',
    'RESUMEN TACTICO NATIVO (calculado en el indicador, NO por ti):',
    grupoTxt('  INTRADIA', a && a.intradia),
    grupoTxt('  SWING   ', a && a.swing),
    div ? ('  ' + div) : '',
    '',
    'TABLA POR MARCO (9 temporalidades, tendencia + estocastico + MACD):',
    tfRows(a && a.tf),
  ].filter((x) => x !== '').join('\n');
}

// ---------- Prompt del analista a partir del JSON v2.0 ----------
function buildPrompt(a) {
  const symbol = a && a.symbol ? a.symbol : '(activo)';
  return `Eres un analista tecnico profesional de mercados, experto en VELAS JAPONESAS y multi-temporalidad. ${VELAS}

Recibes el ESTADO COMPLETO de un activo calculado de forma NATIVA por el dashboard PineScope en TradingView (NO es una imagen: son los datos exactos que describen la grafica, por los 9 marcos). Todo lo de abajo ya viene calculado por el indicador; tu trabajo es INTERPRETARLO como un profesional y dar un veredicto accionable, EN ESPANOL.

=== DATOS NATIVOS DE ${symbol} ===
${briefing(a)}
=== FIN DATOS ===

Como leer estos datos:
- "tend" por marco = tendencia unificada del marco (motor=que marco mas pequeno inicia el movimiento; el grande confirma).
- STOCH/MACD por marco = momentum y su salud (impulso sano, perdiendo/recuperando fuerza, cruces, sobrecompra/sobreventa).
- INTRADIA = marcos 1m..30m (timing fino). SWING = 1H..Diario (direccion de fondo, MANDA).
- Si intradia y swing divergen, dilo y prioriza el swing; el intradia solo da el timing del retroceso/rebote.
- Niveles nativos: soporte SIEMPRE debajo del precio, resistencia SIEMPRE encima.

Responde con un mensaje BREVE listo para Telegram (texto plano, sin markdown pesado; emojis sobrios y saltos de linea). Estructura EXACTA:
- 1a linea: VEREDICTO en MAYUSCULAS (ej. "SWING BAJISTA, REBOTE INTRADIA FINO") con un emoji 🟢/🟡/🔴 coherente con el semaforo.
- "Multi-marco:" 1-2 frases combinando intradia (timing) y swing (direccion), citando el motor y la confirmacion reales.
- "Momentum:" 1 frase sobre estocastico/MACD (impulso, divergencias, sobrecompra/venta) usando los numeros reales.
- "Niveles:" soporte y resistencia nativos con sus numeros; menciona la prediccion por reglas como referencia.
- "Plan accionable:" sesgo (largo/corto/esperar) coherente con la estructura, zona de entrada (en un nivel, al inicio del impulso), STOP (al otro lado del nivel) y OBJETIVO (siguiente nivel), con R:R aproximado. Si el R:R no llega a 2:1 o el mercado es caotico, di "sin operacion clara".
- "Riesgo:" arriesgar <=1-2% del capital y el escenario que invalida la idea.
- Cierra: "Analisis educativo, NO recomendacion de compra/venta."

Reglas: usa SOLO los numeros del payload (no inventes). Se coherente con la jerarquia de marcos. Maximo ~14 lineas.`;
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
  if (!t) throw new Error('Claude sin contenido: ' + ((j && (j.stop_reason || (j.error && j.error.message))) || JSON.stringify(j || {}).slice(0, 200)));
  return t;
}
function pickOpenAI(j) {
  const m = j && j.choices && j.choices[0] && j.choices[0].message;
  const t = m && m.content;
  if (!t) throw new Error('OpenAI sin contenido: ' + ((j && j.choices && j.choices[0] && j.choices[0].finish_reason) || (j && j.error && j.error.message) || JSON.stringify(j || {}).slice(0, 200)));
  return t;
}
function pickGemini(j) {
  const cand = j && j.candidates && j.candidates[0];
  const parts = cand && cand.content && cand.content.parts;
  const t = (Array.isArray(parts) ? parts : []).map((p) => p.text || '').join('');
  if (!t) throw new Error('Gemini bloqueado/sin contenido: ' + JSON.stringify((j && (j.promptFeedback || (cand && cand.finishReason) || j.error)) || j || {}).slice(0, 200));
  return t;
}

// ¿Error de MODELO inexistente (404)? -> probamos modelos de respaldo de Gemini.
function isModelErr(msg) {
  const s = String(msg || '');
  return /(^|\D)404(\D|$)/.test(s) || /not found|not supported|NOT_FOUND|ListModels/i.test(s);
}
const GEMINI_FALLBACKS = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-1.5-flash'];
function geminiModels(model) {
  const m = (model || '').trim();
  const list = m ? [m] : [];
  for (const f of GEMINI_FALLBACKS) if (!list.includes(f)) list.push(f);
  return list;
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
    body: JSON.stringify({ model: CFG.anthropicModel, max_tokens: 1100, messages: [{ role: 'user', content: prompt }] }),
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

// Gemini probando varios modelos: si uno da 404 (no existe), pasa al siguiente.
async function callGemini(prompt) {
  if (!CFG.geminiKey) throw new Error('falta GEMINI_API_KEY');
  const body = { contents: [{ parts: [{ text: prompt }] }], generationConfig: { temperature: 0.4 } };
  let lastErr;
  for (const m of geminiModels(CFG.geminiModel)) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent?key=${encodeURIComponent(CFG.geminiKey)}`;
    const res = await fetchTO(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.ok) return pickGemini(await res.json());
    const errTxt = (await res.text()).slice(0, 200);
    lastErr = new Error('Gemini ' + res.status + ': ' + errTxt);
    if (!isModelErr(res.status + ' ' + errTxt)) throw lastErr; // no es problema de modelo: corta
  }
  throw lastErr;
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
  const body = { chat_id: CFG.tgChat, text: String(text).slice(0, 4096), disable_web_page_preview: true };
  const res = await fetchTO(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  }, 15000);
  if (!res.ok) throw new Error('Telegram ' + res.status + ': ' + (await res.text()).slice(0, 200));
  return res.json();
}

// ---------- Validacion del secreto compartido ----------
// El secreto puede llegar de 3 formas: header x-webhook-secret, ?secret=... en la URL,
// o el campo "secret" del JSON v2.0 (que es la forma que define el SPEC).
function checkSecret(req, alert) {
  if (!CFG.secret) return true; // si no configuraste WEBHOOK_SECRET, no se exige (no recomendado)
  const got = req.get('x-webhook-secret') || req.query.secret || (alert && alert.secret);
  return got === CFG.secret;
}

// ¿El payload parece un JSON v2.0 de PineScope? (para avisar si llega otra cosa).
function esPineScopeV2(a) {
  return a && typeof a === 'object' && (a.app === 'PineScope' || a.tf || a.intradia || a.swing);
}

// ---------- Trabajo pesado APARTE (IA + Telegram) ----------
// Se llama con setImmediate tras responder 200, para no bloquear la respuesta a TradingView.
async function processAlert(alert) {
  try {
    const prompt = buildPrompt(alert);
    const analisis = await callAI(prompt);
    const symbol = alert.symbol || alert.ticker || '';
    const tf = alert.chartTF || alert.timeframe || '';
    const sem = alert.semaforo ? ({ VERDE: '🟢', AMARILLO: '🟡', ROJO: '🔴' }[alert.semaforo] || '') : '';
    const cabecera = `📈 PineScope ${sem} — ${symbol}${tf ? ' (' + tf + ')' : ''}\n`;
    await sendTelegram(cabecera + '\n' + analisis);
    console.log('[webhook] analisis enviado a Telegram para', symbol || '(sin simbolo)');
  } catch (e) {
    const msg = String((e && e.message) || e);
    console.error('[webhook] error:', msg);
    try { await sendTelegram('⚠️ PineScope: no pude generar el analisis.\nMotivo: ' + msg.slice(0, 300)); }
    catch (_e2) { /* si Telegram tambien falla, ya quedo en el log */ }
  }
}

// ---------- App Express ----------
const app = express();
// TradingView a veces manda el cuerpo como text/plain aunque sea JSON: aceptamos ambos.
app.use(express.json({ limit: '256kb' }));
app.use(express.text({ type: ['text/*', 'application/octet-stream'], limit: '256kb' }));

app.get('/', (_req, res) => res.send('PineScope AI Bridge v2 OK (POST /webhook)'));

app.post('/webhook', (req, res) => {
  // 1) Parsear el cuerpo (objeto ya parseado o string JSON/plano).
  let alert = req.body;
  if (typeof alert === 'string') {
    const s = alert.trim();
    try { alert = JSON.parse(s); }
    catch (_e) { alert = { mensaje: s }; } // alerta en texto plano: la envolvemos
  }
  if (!alert || typeof alert !== 'object') alert = { mensaje: String(req.body || '') };

  // 2) Validar secreto.
  if (!checkSecret(req, alert)) {
    console.warn('[webhook] secreto invalido o ausente');
    return res.status(401).json({ ok: false, error: 'secreto invalido' });
  }

  // 3) Responder YA a TradingView (limite ~3s). El trabajo pesado va aparte.
  res.json({ ok: true, recibido: true, v2: esPineScopeV2(alert) });

  // 4) IA + Telegram fuera del ciclo de la respuesta HTTP (no bloquea el 200).
  setImmediate(() => { processAlert(alert); });
});

app.listen(CFG.port, () => {
  console.log(`PineScope AI Bridge v2 escuchando en http://localhost:${CFG.port}`);
  console.log(`  Proveedor IA: ${CFG.provider} | Telegram chat: ${CFG.tgChat || '(no configurado)'}`);
  if (!CFG.secret) console.warn('  ADVERTENCIA: WEBHOOK_SECRET vacio; cualquiera podria llamar a /webhook.');
});

// ---------- util: parser .env minimo (evita dependencia dotenv) ----------
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
