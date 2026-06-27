# Conectar PineScope con una IA (Claude, Gemini, OpenAI, Grok u Ollama)

Pine Script **no puede** llamar a una IA por si mismo. La solucion es simple y directa,
**sin Telegram y sin montar un servidor**: el indicador exporta sus datos en un JSON, y una
**herramienta local** (que ya esta en `tools/`) se los pasa a la IA que tu elijas y te muestra
el analisis. Tu pones tu propia API key (o usas Ollama gratis en tu PC).

```
PineScope_Dashboard (en TradingView)
   |  exporta un JSON con todos los datos (9 marcos, estocastico, MACD, niveles, prediccion)
   v
Tu copias ese JSON
   v
Herramienta local (tools/pinescope-ia.html  o  tools/pinescope_ia.py)
   |  se lo manda a la IA con tu API key
   v
La IA te devuelve el analisis en pantalla
```

La IA recibe los **numeros exactos** del indicador (mejor que mirar una foto). No ve la imagen
del grafico ni dibuja en TradingView; solo interpreta los datos y escribe un veredicto.

---

## Paso 1 - Sacar el JSON de TradingView

1. Agrega `PineScope_Dashboard` al grafico (ver [COMO-AGREGAR-A-TRADINGVIEW.md](../COMO-AGREGAR-A-TRADINGVIEW.md)).
2. En sus ajustes, activa el input **"Emitir IA (webhook)"**.
3. Crea una **alerta** sobre el indicador con condicion **"Any alert() function call"**.
4. Cuando la alerta salte, su mensaje es el **JSON** con todos los datos. Abrelo en el registro de
   alertas (campana, arriba a la derecha) y **copia** ese texto.

> Nota: para *copiar* el JSON del registro NO necesitas plan de pago. (El plan de pago solo hace
> falta si quisieras que TradingView lo *envie solo* a un servidor por webhook, que aqui no usamos.)

El JSON se ve asi (resumido):

```json
{"app":"PineScope","symbol":"NVDA","price":194.23,"chartTF":"240","semaforo":"ROJO",
 "tf":{ "5m":{...}, "1H":{...}, "Diario":{...} },
 "intradia":{"tendencia":"POSIBLE BAJISTA","motor":"5m","score":-1.5,"lectura":"..."},
 "swing":{"tendencia":"POSIBLE ALCISTA","motor":"1H","score":2,"lectura":"..."},
 "niveles":{"soporte":190.0,"resistencia":202.34},
 "prediccion":{"objetivoSube":202.34,"objetivoBaja":190.0}}
```

---

## Paso 2 - Elegir como conectar la IA

Tienes dos herramientas (elige UNA). Ambas son multi-proveedor: **Claude, OpenAI, Gemini, Grok y Ollama**.

### Opcion A - Pagina web (la mas facil): `tools/pinescope-ia.html`

1. Abre el archivo `tools/pinescope-ia.html` con doble clic (se abre en tu navegador).
2. Elige el **proveedor** y pega tu **API key** (se guarda solo en tu navegador).
3. Pega el **JSON** del Paso 1 y pulsa **"Analizar con IA"**.
4. El analisis aparece en la misma pagina.

Funciona directo para **Claude, OpenAI y Gemini**. Para **Ollama** y a veces **Grok**, el navegador
puede bloquear la conexion (CORS); en ese caso usa la Opcion B.

### Opcion B - Terminal (la mas robusta): `tools/pinescope_ia.py`

No necesita instalar nada (usa solo Python estandar). Sirve para **todos** los proveedores,
incluido **Ollama** local y **Grok**.

```powershell
# 1) Elige proveedor y pon tu key (una vez, en PowerShell):
$env:AI_PROVIDER="gemini"
$env:GEMINI_API_KEY="tu_key"
#   claude -> ANTHROPIC_API_KEY   openai -> OPENAI_API_KEY   grok -> XAI_API_KEY
#   ollama -> no necesita key (opcional OLLAMA_URL)

# 2) Analiza (pega el JSON y pulsa Ctrl+Z y Enter), o pasa un archivo:
python tools/pinescope_ia.py
python tools/pinescope_ia.py datos.json --provider gemini
```

---

## Donde sacar cada API key

| Proveedor | Donde | Notas |
|---|---|---|
| **Claude** | console.anthropic.com | Modelo por defecto `claude-opus-4-8`; mas barato `claude-haiku-4-5`. |
| **OpenAI** | platform.openai.com | Cambia el modelo si tu cuenta usa otro. |
| **Gemini** | aistudio.google.com | `gemini-2.5-flash` es gratis con limites. (`gemini-2.0-flash` ya no existe.) |
| **Grok (xAI)** | console.x.ai | Compatible con OpenAI. Si el navegador lo bloquea, usa la Opcion B. |
| **Ollama (local, GRATIS)** | ollama.com | Corre en tu PC; sin key. Para tu equipo va bien `qwen3.5:2b` (texto). |

### Ollama (gratis, en tu propia PC)

1. Instala Ollama y descarga un modelo:
   ```powershell
   ollama pull qwen3.5:2b
   ollama serve
   ```
2. Usa la Opcion B (terminal) con `--provider ollama`, o la pagina web iniciando Ollama con
   `OLLAMA_ORIGINS=*` para que acepte el navegador.

La 1a respuesta puede tardar ~1 minuto (carga el modelo en memoria); luego va rapido.

---

## Lo que SI y lo que NO

- **SI**: la IA recibe los datos nativos y exactos del indicador (9 marcos, momentum, niveles) y
  escribe un veredicto + plan + riesgo. Tu pones tu key (o Ollama gratis).
- **NO**: la IA no ve la imagen del grafico (eso lo hace la extension FinScope con vision), y no
  dibuja ni cambia nada en TradingView (eso lo hacen los propios indicadores PineScope).

Aviso: todo esto es analisis educativo, puede fallar y no es recomendacion de inversion.
