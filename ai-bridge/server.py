"""PineScope - BRIDGE de IA externa (Python + Flask)  ·  JSON v2.0

Equivalente de server.js, pensado tambien para enchufarse al proyecto "Agente-de-finanzas"
del usuario (que ya manda mensajes por Telegram).

FLUJO NATIVO:
  El Dashboard de PineScope (Pine Script v6) calcula TODO de forma nativa sobre los datos
  de TradingView (estocastico/MACD/tendencia por los 9 marcos, resumen tactico
  INTRADIA/SWING con motor+confirmacion, niveles S/R y prediccion por reglas) y lo exporta
  como un JSON de UNA linea via alert(). Una alerta-webhook de TradingView manda ese JSON
  aqui, y este servidor:
    1) valida el 'secret' compartido,
    2) arma un PROMPT de analista profesional que aprovecha TODOS esos datos nativos
       (multi-temporalidad, motor, confirmacion, divergencias intradia vs swing, niveles
       y prediccion) con el metodo velas-japonesas (Tendencia+Nivel+Senal),
    3) llama a la IA (anthropic | openai | gemini, segun AI_PROVIDER),
    4) reenvia el veredicto + gestion de riesgo a Telegram.

  Pine NO puede llamar a una IA ni "ver" la imagen del grafico: este servidor es el puente,
  y aqui la IA NO mira pixeles: recibe los DATOS NATIVOS EXACTOS que describen la grafica.
  (Para que la IA "vea" la imagen del grafico esta la extension FinScope, que captura el
  chart y usa vision. Aqui los datos son nativos y precisos.)

Limite de 3s de TradingView: validamos y respondemos 200 al instante; la IA + Telegram
corren en un HILO aparte (threading.Thread), fuera del ciclo de la respuesta HTTP.

Arranque:
    pip install flask requests
    python server.py
Endpoint:  POST /webhook
Salud:     GET  /            -> "PineScope AI Bridge v2 OK"

Integracion con Agente-de-finanzas: si ya tienes una funcion para mandar a Telegram en ese
proyecto, importa este modulo y reemplaza send_telegram() por la tuya, o corre este server.py
como un proceso aparte que comparte el mismo bot/chat.
"""

import json
import os
import threading

import requests
from flask import Flask, request, jsonify


# ---------- Carga .env si existe (parser minimo, sin dependencia python-dotenv) ----------
def _load_dotenv():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                os.environ.setdefault(key, val)
    except OSError:
        pass


_load_dotenv()

# ---------- Config (variables de entorno, ver .env.example) ----------
PROVIDER = os.environ.get("AI_PROVIDER", "anthropic").lower()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
PORT = int(os.environ.get("PORT", "8080"))
AI_TIMEOUT = float(os.environ.get("AI_TIMEOUT_MS", "45000")) / 1000.0  # ~45s

# Orden fijo de los 9 marcos (igual que el SPEC).
TF_ORDER = ["1m", "3m", "5m", "15m", "30m", "1H", "2H", "4H", "Diario"]

# ---------- Chuleta del metodo de velas (skill velas-japonesas) ----------
VELAS = (
    "METODO VELAS JAPONESAS (aplicalo): 1) TENDENCIA = estructura (alcista: maximos y minimos "
    "mas altos; bajista: mas bajos; o lateral/caotico); el marco GRANDE manda "
    "(Diario>4H>1H>intradia). 2) NIVEL = soportes (DEBAJO del precio) y resistencias (ENCIMA), "
    "zonas. 3) SENAL = confluencia EN un nivel y A FAVOR de la tendencia (nunca una senal aislada). "
    "COHERENCIA OBLIGATORIA: soporte<precio<resistencia; el sesgo debe cuadrar con la tendencia "
    "multi-temporalidad; NO etiquetes una resistencia como soporte ni des un veredicto alcista "
    "contra una estructura claramente bajista. Entrar al INICIO del impulso (tras retroceso a un "
    "nivel), no en mitad del retroceso. R:R minimo 2:1; riesgo por operacion <=2% del capital."
)


# ---------- Lectura del payload v2.0 -> texto legible para la IA ----------
def _num(v, dec):
    try:
        return ("%." + str(dec) + "f") % float(v)
    except (TypeError, ValueError):
        return "-"


def _s(v, fallback="?"):
    """Devuelve fallback si el valor es None (JSON null) o falta; si no, su texto.
    Mantiene la PARIDAD con server.js, donde `x != null ? x : '?'` ya trata el null.
    El Dashboard emite niveles.soporte/resistencia como null cuando no hay pivote,
    asi que esto evita imprimir 'None' literal en el prompt."""
    return fallback if v is None else v


def _tf_rows(tf):
    if not isinstance(tf, dict):
        return "(sin tabla por marco)"
    lines = []
    for k in TF_ORDER:
        c = tf.get(k)
        if not isinstance(c, dict):
            continue
        trend = _s(c.get("trend", "?"))
        s_k = _num(c.get("stochK"), 1)
        s_est = _s(c.get("stochEstado", "-"), "-")
        s_fz = _s(c.get("stochFuerza", "-"), "-")
        m_h = _num(c.get("macdHist"), 2)
        m_est = _s(c.get("macdEstado", "-"), "-")
        m_fz = _s(c.get("macdFuerza", "-"), "-")
        lines.append(
            "  %-6s | tend %s | STOCH %%K=%s %s/%s | MACD hist=%s %s/%s"
            % (k, trend, s_k, s_est, s_fz, m_h, m_est, m_fz)
        )
    return "\n".join(lines) if lines else "(sin tabla por marco)"


def _grupo_txt(nombre, g):
    if not isinstance(g, dict):
        return "%s: (sin datos)" % nombre
    return (
        "%s: tendencia=%s | score=%s | motor=%s (el marco que manda) | confirmacion=%s | "
        'lectura nativa="%s"'
        % (
            nombre,
            _s(g.get("tendencia", "?")),
            _s(g.get("score", "?")),
            _s(g.get("motor", "?")),
            _s(g.get("confirmacion", "?")),
            _s(g.get("lectura", ""), ""),
        )
    )


def _divergencia(a):
    intra = (a.get("intradia") or {}).get("tendencia") if isinstance(a.get("intradia"), dict) else None
    sw = (a.get("swing") or {}).get("tendencia") if isinstance(a.get("swing"), dict) else None
    if not intra or not sw:
        return ""

    def alc(x):
        u = str(x).upper()
        return "ALCISTA" in u and "BAJISTA" not in u

    def baj(x):
        return "BAJISTA" in str(x).upper()

    if alc(intra) and baj(sw):
        return ("DIVERGENCIA: intradia ALCISTA contra swing BAJISTA -> probable rebote dentro de "
                "tendencia mayor bajista (largos finos y rapidos, el swing manda).")
    if baj(intra) and alc(sw):
        return ("DIVERGENCIA: intradia BAJISTA dentro de swing ALCISTA -> probable retroceso; "
                "vigilar fin de caida para sumarse al swing alcista.")
    if alc(intra) and alc(sw):
        return "ALINEACION ALCISTA: intradia y swing apuntan arriba (mayor probabilidad)."
    if baj(intra) and baj(sw):
        return "ALINEACION BAJISTA: intradia y swing apuntan abajo (mayor probabilidad)."
    return ""


def _niveles_txt(a):
    n = a.get("niveles") or {}
    p = a.get("prediccion") or {}
    return "\n".join([
        "Precio actual: %s | Marco del grafico: %s | Semaforo: %s | scoreGlobal: %s"
        % (_s(a.get("price", "?")), _s(a.get("chartTF", "?")), _s(a.get("semaforo", "?")), _s(a.get("scoreGlobal", "?"))),
        "Niveles nativos: soporte=%s (debajo) | resistencia=%s (encima)"
        % (_s(n.get("soporte", "?")), _s(n.get("resistencia", "?"))),
        "Prediccion por reglas (orientativa, sin IA): objetivoSube=%s | objetivoBaja=%s"
        % (_s(p.get("objetivoSube", "?")), _s(p.get("objetivoBaja", "?"))),
    ])


def _briefing(a):
    div = _divergencia(a)
    bloques = [
        _niveles_txt(a),
        "",
        "RESUMEN TACTICO NATIVO (calculado en el indicador, NO por ti):",
        _grupo_txt("  INTRADIA", a.get("intradia")),
        _grupo_txt("  SWING   ", a.get("swing")),
        ("  " + div) if div else "",
        "",
        "TABLA POR MARCO (9 temporalidades, tendencia + estocastico + MACD):",
        _tf_rows(a.get("tf")),
    ]
    return "\n".join(b for b in bloques if b != "")


def build_prompt(a):
    """Construye el prompt del analista a partir del JSON v2.0 de la alerta de TradingView."""
    symbol = a.get("symbol") or "(activo)"
    return (
        "Eres un analista tecnico profesional de mercados, experto en VELAS JAPONESAS y "
        "multi-temporalidad. " + VELAS + "\n\n"
        "Recibes el ESTADO COMPLETO de un activo calculado de forma NATIVA por el dashboard "
        "PineScope en TradingView (NO es una imagen: son los datos exactos que describen la "
        "grafica, por los 9 marcos). Todo lo de abajo ya viene calculado por el indicador; tu "
        "trabajo es INTERPRETARLO como un profesional y dar un veredicto accionable, EN ESPANOL.\n\n"
        "=== DATOS NATIVOS DE " + symbol + " ===\n"
        + _briefing(a) + "\n"
        "=== FIN DATOS ===\n\n"
        "Como leer estos datos:\n"
        "- 'tend' por marco = tendencia unificada del marco (motor=que marco mas pequeno inicia el "
        "movimiento; el grande confirma).\n"
        "- STOCH/MACD por marco = momentum y su salud (impulso sano, perdiendo/recuperando fuerza, "
        "cruces, sobrecompra/sobreventa).\n"
        "- INTRADIA = marcos 1m..30m (timing fino). SWING = 1H..Diario (direccion de fondo, MANDA).\n"
        "- Si intradia y swing divergen, dilo y prioriza el swing; el intradia solo da el timing del "
        "retroceso/rebote.\n"
        "- Niveles nativos: soporte SIEMPRE debajo del precio, resistencia SIEMPRE encima.\n\n"
        "Responde con un mensaje BREVE listo para Telegram (texto plano, sin markdown pesado, "
        "SIN EMOJIS, con saltos de linea). Estructura EXACTA:\n"
        "- 1a linea: VEREDICTO en MAYUSCULAS (ej. 'SWING BAJISTA, REBOTE INTRADIA FINO') seguido del "
        "semaforo en texto entre corchetes: [VERDE], [AMBAR] o [ROJO], coherente con el calculado.\n"
        "- 'Multi-marco:' 1-2 frases combinando intradia (timing) y swing (direccion), citando el "
        "motor y la confirmacion reales.\n"
        "- 'Momentum:' 1 frase sobre estocastico/MACD (impulso, divergencias, sobrecompra/venta) "
        "usando los numeros reales.\n"
        "- 'Niveles:' soporte y resistencia nativos con sus numeros; menciona la prediccion por "
        "reglas como referencia.\n"
        "- 'Plan accionable:' sesgo (largo/corto/esperar) coherente con la estructura, zona de "
        "entrada (en un nivel, al inicio del impulso), STOP (al otro lado del nivel) y OBJETIVO "
        "(siguiente nivel), con R:R aproximado. Si el R:R no llega a 2:1 o el mercado es caotico, "
        "di 'sin operacion clara'.\n"
        "- 'Riesgo:' arriesgar <=1-2% del capital y el escenario que invalida la idea.\n"
        "- Cierra: 'Analisis educativo, NO recomendacion de compra/venta.'\n\n"
        "Reglas: usa SOLO los numeros del payload (no inventes). Se coherente con la jerarquia de "
        "marcos. Maximo ~14 lineas."
    )


# ---------- Extractores defensivos de la respuesta de cada IA ----------
def _pick_claude(j):
    parts = j.get("content") if isinstance(j, dict) else None
    text = "".join(b.get("text", "") for b in parts) if isinstance(parts, list) else ""
    if not text:
        raise RuntimeError("Claude sin contenido: " + json.dumps(j.get("error") or j.get("stop_reason") or j)[:200])
    return text


def _pick_openai(j):
    try:
        text = j["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        text = ""
    if not text:
        raise RuntimeError("OpenAI sin contenido: " + json.dumps(j.get("error") or j)[:200])
    return text


def _pick_gemini(j):
    try:
        parts = j["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts)
    except (KeyError, IndexError, TypeError):
        text = ""
    if not text:
        raise RuntimeError(
            "Gemini bloqueado/sin contenido: "
            + json.dumps(j.get("promptFeedback") or j.get("error") or j)[:200]
        )
    return text


def _is_model_err(msg):
    s = str(msg or "")
    return " 404" in s or "404 " in s or any(
        k in s for k in ("not found", "not supported", "NOT_FOUND", "ListModels")
    )


GEMINI_FALLBACKS = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]


def _gemini_models(model):
    m = (model or "").strip()
    out = [m] if m else []
    for f in GEMINI_FALLBACKS:
        if f not in out:
            out.append(f)
    return out


# ---------- Llamadas a cada proveedor ----------
def call_claude(prompt):
    if not ANTHROPIC_KEY:
        raise RuntimeError("falta ANTHROPIC_API_KEY")
    res = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={"model": ANTHROPIC_MODEL, "max_tokens": 1100, "messages": [{"role": "user", "content": prompt}]},
        timeout=AI_TIMEOUT,
    )
    if not res.ok:
        raise RuntimeError("Claude %s: %s" % (res.status_code, res.text[:200]))
    return _pick_claude(res.json())


def call_openai(prompt):
    if not OPENAI_KEY:
        raise RuntimeError("falta OPENAI_API_KEY")
    res = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": "Bearer " + OPENAI_KEY, "content-type": "application/json"},
        json={"model": OPENAI_MODEL, "temperature": 0.4, "messages": [{"role": "user", "content": prompt}]},
        timeout=AI_TIMEOUT,
    )
    if not res.ok:
        raise RuntimeError("OpenAI %s: %s" % (res.status_code, res.text[:200]))
    return _pick_openai(res.json())


def call_gemini(prompt):
    if not GEMINI_KEY:
        raise RuntimeError("falta GEMINI_API_KEY")
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.4}}
    last_err = None
    for m in _gemini_models(GEMINI_MODEL):
        url = ("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s"
               % (m, GEMINI_KEY))
        res = requests.post(url, headers={"content-type": "application/json"}, json=body, timeout=AI_TIMEOUT)
        if res.ok:
            return _pick_gemini(res.json())
        err_txt = res.text[:200]
        last_err = RuntimeError("Gemini %s: %s" % (res.status_code, err_txt))
        if not _is_model_err("%s %s" % (res.status_code, err_txt)):
            raise last_err  # no es problema de modelo: corta aqui
    raise last_err


def call_ai(prompt):
    if PROVIDER in ("anthropic", "claude"):
        return call_claude(prompt)
    if PROVIDER == "openai":
        return call_openai(prompt)
    if PROVIDER in ("gemini", "google"):
        return call_gemini(prompt)
    raise RuntimeError('AI_PROVIDER desconocido: "%s" (usa anthropic | openai | gemini)' % PROVIDER)


# ---------- Telegram (Bot API) ----------
# Si integras este modulo en "Agente-de-finanzas", sustituye esta funcion por la que ya uses
# alli para mandar mensajes (mismo bot/chat).
def send_telegram(text):
    if not TG_TOKEN or not TG_CHAT:
        raise RuntimeError("faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID")
    url = "https://api.telegram.org/bot%s/sendMessage" % TG_TOKEN
    res = requests.post(
        url,
        json={"chat_id": TG_CHAT, "text": str(text)[:4096], "disable_web_page_preview": True},
        timeout=15,
    )
    if not res.ok:
        raise RuntimeError("Telegram %s: %s" % (res.status_code, res.text[:200]))
    return res.json()


# ---------- Validacion del secreto compartido ----------
def check_secret(req, alert):
    """El secreto puede llegar por: header x-webhook-secret, ?secret=... en la URL, o el campo
    "secret" del JSON v2.0 (la forma que define el SPEC). Si WEBHOOK_SECRET esta vacio, no se exige."""
    if not WEBHOOK_SECRET:
        return True
    got = req.headers.get("x-webhook-secret") or req.args.get("secret")
    if not got and isinstance(alert, dict):
        got = alert.get("secret")
    return got == WEBHOOK_SECRET


def es_pinescope_v2(a):
    """Heuristica: el payload parece un JSON v2.0 de PineScope."""
    return isinstance(a, dict) and (a.get("app") == "PineScope" or "tf" in a or "intradia" in a or "swing" in a)


_SEMA_EMOJI = {"VERDE": "verde", "AMARILLO": "amarillo", "ROJO": "rojo"}


# ---------- Trabajo pesado en segundo plano (IA + Telegram) ----------
def process_alert(alert):
    try:
        prompt = build_prompt(alert)
        analisis = call_ai(prompt)
        symbol = alert.get("symbol") or alert.get("ticker") or ""
        tf = alert.get("chartTF") or alert.get("timeframe") or ""
        cabecera = "PineScope - %s%s\n" % (symbol, (" (%s)" % tf) if tf else "")
        send_telegram(cabecera + "\n" + analisis)
        print("[webhook] analisis enviado a Telegram para", symbol or "(sin simbolo)")
    except Exception as exc:  # noqa: BLE001 - queremos avisar de cualquier fallo
        msg = str(exc)
        print("[webhook] error:", msg)
        try:
            send_telegram("PineScope: no pude generar el analisis.\nMotivo: " + msg[:300])
        except Exception:  # noqa: BLE001
            pass


# ---------- App Flask ----------
app = Flask(__name__)


@app.get("/")
def health():
    return "PineScope AI Bridge v2 OK (POST /webhook)"


@app.post("/webhook")
def webhook():
    # 1) Parsear el cuerpo: TradingView puede mandar JSON o texto plano.
    alert = request.get_json(silent=True)
    if alert is None:
        raw = (request.get_data(as_text=True) or "").strip()
        try:
            alert = json.loads(raw)
        except (ValueError, TypeError):
            alert = {"mensaje": raw}
    if not isinstance(alert, dict):
        alert = {"mensaje": str(alert)}

    # 2) Validar secreto.
    if not check_secret(request, alert):
        print("[webhook] secreto invalido o ausente")
        return jsonify({"ok": False, "error": "secreto invalido"}), 401

    # 3) Lanzar IA+Telegram en un HILO y responder YA a TradingView (limite ~3s).
    threading.Thread(target=process_alert, args=(alert,), daemon=True).start()
    return jsonify({"ok": True, "recibido": True, "v2": es_pinescope_v2(alert)})


if __name__ == "__main__":
    print("PineScope AI Bridge v2 escuchando en http://localhost:%d" % PORT)
    print("  Proveedor IA: %s | Telegram chat: %s" % (PROVIDER, TG_CHAT or "(no configurado)"))
    if not WEBHOOK_SECRET:
        print("  ADVERTENCIA: WEBHOOK_SECRET vacio; cualquiera podria llamar a /webhook.")
    # threaded=True para atender varias alertas a la vez. host=0.0.0.0 para que ngrok/hosting lo alcance.
    app.run(host="0.0.0.0", port=PORT, threaded=True)
