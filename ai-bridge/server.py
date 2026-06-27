"""PineScope — BRIDGE de IA externa (Python + Flask)

Equivalente de server.js, pensado para enchufarse al proyecto "Agente-de-finanzas"
del usuario (que ya manda mensajes por Telegram).

FLUJO: indicador Pine emite una alerta -> TradingView envia un webhook (JSON) aqui
-> validamos un secreto compartido -> construimos un prompt de analista financiero
(metodo VELAS JAPONESAS: Tendencia + Nivel + Senal) -> llamamos a la IA
(anthropic | openai | gemini, segun AI_PROVIDER) -> reenviamos el texto a Telegram.

Pine NO puede llamar a una IA por si mismo; este servidor es el puente.

Arranque:
    pip install flask requests
    python server.py
Endpoint:  POST /webhook
Salud:     GET  /            -> "PineScope AI Bridge OK"

Integracion con Agente-de-finanzas: si ya tienes una funcion para mandar a Telegram
en ese proyecto, puedes importar este modulo y reemplazar send_telegram() por la tuya,
o simplemente correr este server.py como un proceso aparte que comparte el mismo bot.
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

# ---------- Chuleta del metodo de velas (skill velas-japonesas) ----------
# Condensada a proposito: "ensena" Tendencia+Nivel+Senal a la IA sin alargar el prompt.
VELAS = (
    "METODO VELAS JAPONESAS (aplicalo): 1) TENDENCIA = estructura (alcista: maximos y minimos "
    "mas altos; bajista: mas bajos; o lateral/caotico). 2) NIVEL = soportes (DEBAJO del precio) "
    "y resistencias (ENCIMA), medias 50/200, zonas. 3) SENAL = patron de vela EN un nivel y A FAVOR "
    "de la tendencia (nunca un patron aislado). Patrones: engulfing alcista/bajista, martillo=pin bar "
    "alcista (fondo/soporte), estrella fugaz=pin bar bajista (techo/resistencia), doji (indecision/giro), "
    "estrella de la manana/de la tarde, harami/inside bar, pinzas. El marco grande manda "
    "(semanal>diario>intradia). Tras una ruptura, resistencia rota->soporte (y viceversa). "
    "COHERENCIA: soporte<precio<resistencia; el sesgo alcista/bajista debe cuadrar con precio vs "
    "SMA50/200 y la tendencia multi-temporalidad."
)


def build_prompt(alert):
    """Construye el prompt del analista a partir del JSON de la alerta de TradingView."""
    return (
        "Eres un analista financiero experto en VELAS JAPONESAS. " + VELAS + "\n"
        "Recibes una ALERTA disparada por un indicador de TradingView (Pine Script) con los datos de "
        "abajo (simbolo, temporalidad, precio, senal, niveles, indicadores, etc.). Interpreta la alerta "
        "con el metodo Tendencia+Nivel+Senal y explicala como un analista profesional, EN ESPANOL.\n"
        "Responde con un mensaje BREVE y claro listo para enviar por Telegram (texto plano, sin markdown "
        "pesado; puedes usar emojis sobrios y saltos de linea). Estructura sugerida:\n"
        "- Una primera linea-resumen en MAYUSCULAS con el veredicto.\n"
        "- 3 a 5 vinetas con: tendencia/estructura, el nivel donde ocurre la senal, el patron o senal de la "
        "vela, y el riesgo.\n"
        "- Una linea 'A vigilar:' con el nivel o senal clave.\n"
        "- Cierra recordando que es analisis educativo, NO recomendacion de compra/venta.\n"
        "Usa los numeros reales de la alerta; si falta un dato, no lo inventes. Se conciso (max ~12 lineas).\n"
        "DATOS DE LA ALERTA (JSON):\n" + json.dumps(alert, ensure_ascii=False)
    )


# ---------- Extractores defensivos de la respuesta de cada IA ----------
def _pick_claude(j):
    parts = j.get("content") if isinstance(j, dict) else None
    text = "".join(b.get("text", "") for b in parts) if isinstance(parts, list) else ""
    if not text:
        raise RuntimeError("Claude sin contenido: " + json.dumps(j.get("error") or j)[:200])
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
        raise RuntimeError("Gemini bloqueado/sin contenido: " + json.dumps(j.get("promptFeedback") or j.get("error") or j)[:200])
    return text


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
        json={"model": ANTHROPIC_MODEL, "max_tokens": 900, "messages": [{"role": "user", "content": prompt}]},
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
    url = ("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s"
           % (GEMINI_MODEL, GEMINI_KEY))
    res = requests.post(
        url,
        headers={"content-type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.4}},
        timeout=AI_TIMEOUT,
    )
    if not res.ok:
        raise RuntimeError("Gemini %s: %s" % (res.status_code, res.text[:200]))
    return _pick_gemini(res.json())


def call_ai(prompt):
    if PROVIDER in ("anthropic", "claude"):
        return call_claude(prompt)
    if PROVIDER == "openai":
        return call_openai(prompt)
    if PROVIDER in ("gemini", "google"):
        return call_gemini(prompt)
    raise RuntimeError('AI_PROVIDER desconocido: "%s" (usa anthropic | openai | gemini)' % PROVIDER)


# ---------- Telegram (Bot API) ----------
# Si integras este modulo en "Agente-de-finanzas", puedes sustituir esta funcion por la
# que ya uses alli para mandar mensajes (mismo bot/chat).
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
    """El secreto puede llegar por: header x-webhook-secret, ?secret=... en la URL,
    o un campo "secret" dentro del JSON. Si WEBHOOK_SECRET esta vacio, no se exige."""
    if not WEBHOOK_SECRET:
        return True
    got = req.headers.get("x-webhook-secret") or req.args.get("secret")
    if not got and isinstance(alert, dict):
        got = alert.get("secret")
    return got == WEBHOOK_SECRET


# ---------- Trabajo pesado en segundo plano (IA + Telegram) ----------
def process_alert(alert):
    try:
        prompt = build_prompt(alert)
        analisis = call_ai(prompt)
        symbol = alert.get("symbol") or alert.get("ticker") or alert.get("simbolo") or ""
        tf = alert.get("timeframe") or alert.get("interval") or alert.get("tf") or ""
        cabecera = "PineScope — %s%s\n" % (symbol, (" (%s)" % tf) if tf else "")
        send_telegram(cabecera + "\n" + analisis)
        print("[webhook] analisis enviado a Telegram para", symbol or "(sin simbolo)")
    except Exception as exc:  # noqa: BLE001 — queremos avisar de cualquier fallo
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
    return "PineScope AI Bridge OK (POST /webhook)"


@app.post("/webhook")
def webhook():
    # 1) Parsear el cuerpo: TradingView puede mandar JSON o texto plano.
    alert = request.get_json(silent=True)
    if alert is None:
        raw = request.get_data(as_text=True) or ""
        raw = raw.strip()
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

    # 3) Lanzar IA+Telegram en un hilo y responder YA a TradingView (no debe esperar a la IA).
    threading.Thread(target=process_alert, args=(alert,), daemon=True).start()
    return jsonify({"ok": True, "recibido": True})


if __name__ == "__main__":
    print("PineScope AI Bridge escuchando en http://localhost:%d" % PORT)
    print("  Proveedor IA: %s | Telegram chat: %s" % (PROVIDER, TG_CHAT or "(no configurado)"))
    if not WEBHOOK_SECRET:
        print("  ADVERTENCIA: WEBHOOK_SECRET vacio; cualquiera podria llamar a /webhook.")
    # threaded=True para atender varias alertas a la vez. host=0.0.0.0 para que ngrok/hosting lo alcance.
    app.run(host="0.0.0.0", port=PORT, threaded=True)
