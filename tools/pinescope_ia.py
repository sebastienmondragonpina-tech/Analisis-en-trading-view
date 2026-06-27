#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PineScope IA  -  analiza el JSON de PineScope con la IA que elijas.
Proveedores: claude | openai | gemini | grok | ollama (local, gratis).

Sin dependencias: usa solo la libreria estandar de Python (urllib).

USO RAPIDO
----------
1) Elige proveedor y pon tu API key como variable de entorno (una vez):
   Windows PowerShell:
     $env:AI_PROVIDER="gemini"
     $env:GEMINI_API_KEY="tu_key"
   (claude -> ANTHROPIC_API_KEY ; openai -> OPENAI_API_KEY ; grok -> XAI_API_KEY ;
    ollama -> no necesita key; opcional OLLAMA_URL, por defecto http://localhost:11434)

2) Pega el JSON de la alerta de TradingView y analiza:
     python pinescope_ia.py            (pega el JSON y pulsa Ctrl+Z y Enter en Windows)
     python pinescope_ia.py datos.json (lee el JSON de un archivo)

   Opciones: --provider gemini  --model gemini-2.5-flash  --key TU_KEY  --style "enfoque corto"
"""
import os, sys, json, argparse, urllib.request, urllib.error

DEFAULT_MODEL = {
    "claude": "claude-opus-4-8",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.5-flash",
    "grok":   "grok-2-latest",
    "ollama": "qwen3.5:2b",
}
ENV_KEY = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "grok":   "XAI_API_KEY",
}

SYSTEM = (
    "Eres un analista tecnico financiero experto en velas japonesas, con el metodo "
    "Tendencia + Nivel + Senal. Recibes datos NATIVOS y exactos de un indicador de "
    "TradingView (PineScope) con multiples temporalidades: tendencia por marco, "
    "estocastico (ESTADO/FUERZA), MACD (HIST/ESTADO/FUERZA), resumen intradia y swing, "
    "niveles de soporte/resistencia y una prediccion por reglas. "
    "Responde en ESPANOL, SIN EMOJIS, breve y accionable, con esta estructura exacta: "
    "1) VEREDICTO en una linea + el semaforo en texto entre corchetes: [VERDE], [AMBAR] o [ROJO]. "
    "2) Multi-marco: combina intradia (timing) y swing (direccion de fondo, que MANDA); "
    "cita el motor y la confirmacion reales. "
    "3) Momentum: 1-2 frases sobre estocastico y MACD usando los numeros reales. "
    "4) Niveles: soporte y resistencia con sus numeros; usa la prediccion por reglas como referencia. "
    "5) Plan y riesgo: entrada/invalidacion/objetivo con relacion riesgo-beneficio >= 2:1 y riesgo <= 2%. "
    "Si intradia y swing divergen, dilo y prioriza el swing. Nunca inventes niveles: usa solo los del JSON. "
    "Cierra con: 'Analisis educativo, puede fallar, no es recomendacion de inversion.'"
)


def build_prompt(data, style):
    s = "DATOS DEL ACTIVO (JSON de PineScope):\n```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```\n\n"
    s += "Analiza estos datos siguiendo tu estructura."
    if style:
        s += "\n\nInstruccion extra del usuario: " + style
    return s


def _post(url, headers, body, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise SystemExit("Error %s del proveedor:\n%s" % (e.code, detail))
    except urllib.error.URLError as e:
        raise SystemExit("No pude conectar: %s\n(Si es Ollama, asegurate de que 'ollama serve' esta corriendo.)" % e.reason)


def call_claude(key, model, sys_p, user):
    j = _post("https://api.anthropic.com/v1/messages",
              {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
              {"model": model, "max_tokens": 1200, "system": sys_p, "messages": [{"role": "user", "content": user}]})
    return "\n".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text").strip()


def call_openai_like(url, key, model, sys_p, user):
    j = _post(url, {"Authorization": "Bearer " + key, "content-type": "application/json"},
              {"model": model, "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": user}]})
    return j["choices"][0]["message"]["content"].strip()


def call_gemini(key, model, sys_p, user):
    url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s" % (model, key)
    j = _post(url, {"content-type": "application/json"},
              {"systemInstruction": {"parts": [{"text": sys_p}]}, "contents": [{"parts": [{"text": user}]}]})
    parts = j["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts).strip()


def call_ollama(base, model, sys_p, user):
    base = (base or "http://localhost:11434").rstrip("/")
    j = _post(base + "/api/generate", {"content-type": "application/json"},
              {"model": model, "prompt": sys_p + "\n\n" + user, "stream": False, "think": False,
               "keep_alive": "30m", "options": {"temperature": 0.4, "num_predict": 1024}})
    return str(j.get("response", "")).strip()


def main():
    ap = argparse.ArgumentParser(description="Analiza el JSON de PineScope con una IA.")
    ap.add_argument("file", nargs="?", help="archivo .json (o pega por teclado si se omite)")
    ap.add_argument("--provider", default=os.environ.get("AI_PROVIDER", "claude"),
                    choices=list(DEFAULT_MODEL.keys()))
    ap.add_argument("--model", default=None)
    ap.add_argument("--key", default=None)
    ap.add_argument("--style", default="")
    a = ap.parse_args()

    prov = a.provider
    model = a.model or os.environ.get("AI_MODEL") or DEFAULT_MODEL[prov]
    key = a.key or (os.environ.get(ENV_KEY[prov]) if prov in ENV_KEY else None)
    base = os.environ.get("OLLAMA_URL", "http://localhost:11434")

    if prov != "ollama" and not key:
        raise SystemExit("Falta la API key. Pon %s o usa --key." % ENV_KEY[prov])

    raw = open(a.file, "r", encoding="utf-8").read() if a.file else (
        sys.stdin.read() if not sys.stdin.isatty() else _read_pasted())
    try:
        data = json.loads(raw)
    except Exception:
        raise SystemExit("El JSON no es valido. Copia el texto completo de la alerta de TradingView.")
    data.pop("secret", None)

    user = build_prompt(data, a.style)
    sys.stderr.write("Pensando con %s (%s)...\n" % (prov, model))

    if prov == "claude":
        out = call_claude(key, model, SYSTEM, user)
    elif prov == "openai":
        out = call_openai_like("https://api.openai.com/v1/chat/completions", key, model, SYSTEM, user)
    elif prov == "grok":
        out = call_openai_like("https://api.x.ai/v1/chat/completions", key, model, SYSTEM, user)
    elif prov == "gemini":
        out = call_gemini(key, model, SYSTEM, user)
    else:
        out = call_ollama(base, model, SYSTEM, user)

    print("\n" + (out or "(sin respuesta)"))


def _read_pasted():
    print("Pega el JSON de la alerta y termina con Ctrl+Z + Enter (Windows) o Ctrl+D (Mac/Linux):")
    return sys.stdin.read()


if __name__ == "__main__":
    main()
