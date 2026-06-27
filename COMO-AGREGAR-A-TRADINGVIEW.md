# Como agregar PineScope a TradingView

Guia paso a paso, con clics, para poner los indicadores de PineScope en tu grafico,
publicarlos para que otros los usen, y (opcional) conectarlos con una IA.

No necesitas saber programar. Solo vas a **copiar y pegar** texto.

---

## Indice

1. [Lo que necesitas](#1-lo-que-necesitas)
2. [Agregar un indicador (lo haras 3 veces)](#2-agregar-un-indicador-lo-haras-3-veces)
3. [Los 3 archivos que vas a pegar](#3-los-3-archivos-que-vas-a-pegar)
4. [Publicar tu indicador para que otros lo usen](#4-publicar-tu-indicador-para-que-otros-lo-usen)
5. [Conectar con IA: alerta con webhook hacia el AI Bridge](#5-conectar-con-ia-alerta-con-webhook-hacia-el-ai-bridge)
6. [La alternativa gratis (sin pagar TradingView)](#6-la-alternativa-gratis-sin-pagar-tradingview)
7. [Si algo no sale](#7-si-algo-no-sale)

---

## 1. Lo que necesitas

- Una **cuenta de TradingView** (sirve la gratuita para *agregar* y *publicar* indicadores).
- Un **navegador** (Chrome, Edge, etc.) en una computadora. Es mas comodo que en el celular.
- Los **3 archivos `.pine`** de este proyecto (los abres y copias su contenido).

> Para la parte de **IA con webhook** (seccion 5) normalmente hace falta un **plan de pago** de
> TradingView. Para *agregar* y *publicar* indicadores **no** hace falta pagar.

---

## 2. Agregar un indicador (lo haras 3 veces)

Vas a hacer estos mismos pasos **una vez por cada indicador** (son 3 en total).

1. **Abre TradingView** y entra a un grafico. Lo mas facil: ve a
   `tradingview.com`, inicia sesion y haz clic en **"Grafico"** (o **"Chart"**) en el menu de arriba.

2. Elige un activo cualquiera (por ejemplo escribe `AAPL` o `BTCUSD` en la barra de busqueda
   de arriba a la izquierda y pulsa Enter).

3. En la **barra de abajo** del grafico, haz clic en **"Pine Editor"**
   (en espanol puede decir **"Editor de Pine"**). Se abrira un panel de codigo en la parte inferior.

   > Si no ves esa barra: arriba a la derecha del grafico no; mira **abajo del todo**. Si sigue
   > sin aparecer, haz clic derecho en la zona inferior y activa el panel, o busca el icono de
   > Pine Editor en la barra inferior.

4. En el Pine Editor, **borra todo lo que haya** dentro (clic dentro del codigo, selecciona todo
   con **Ctrl + A** y borra con **Suprimir**).

5. Abre el archivo `.pine` correspondiente (ver la lista en la seccion 3), **selecciona todo su
   contenido** (Ctrl + A) y **copialo** (Ctrl + C).

6. Vuelve al Pine Editor de TradingView y **pega** (Ctrl + V). Debe quedar todo el codigo pegado.

7. Haz clic en el boton **"Agregar al grafico"** (en ingles **"Add to chart"**), arriba a la
   derecha del Pine Editor.

8. Listo: el indicador aparece sobre el grafico (o como panel abajo, segun el indicador).

9. **Repite los pasos 4 a 8** con los otros dos archivos. Cada uno se agrega por separado;
   puedes tener los tres a la vez en el mismo grafico.

> **Consejo:** despues de agregarlos, pasa el mouse por el nombre del indicador (arriba a la
> izquierda del grafico) y haz clic en el icono de **ajustes (la rueda dentada)** para activar
> o desactivar tablas, cambiar su posicion, etc.

---

## 3. Los 3 archivos que vas a pegar

Agrega los tres, en este orden recomendado:

| # | Indicador | Archivo a abrir y pegar | Donde aparece |
|---|---|---|---|
| 1 | **PineScope Analyst** | `finscope/pine/PineScope_Analyst.pine` | **Encima** del precio (tabla, semaforo, soportes/resistencias). |
| 2 | **PineScope Momentum** | `finscope/pine/PineScope_Momentum.pine` | **Panel inferior** (histograma MACD + RSI + tabla). |
| 3 | **PineScope Patterns** | `pine/PineScope_Patterns.pine` | **Encima** del precio (etiquetas de patrones de velas). |

Para abrir un archivo `.pine` y copiar su texto: abrelo con el Bloc de notas (Notepad) o con
cualquier editor de texto, pulsa **Ctrl + A** (seleccionar todo) y **Ctrl + C** (copiar).

---

## 4. Publicar tu indicador para que otros lo usen

Publicar significa subir el indicador a la **comunidad de TradingView** para que cualquiera lo
encuentre y lo agregue **con un solo clic**, sin tener que copiar y pegar codigo.

1. Asegurate de que el indicador esta agregado y funcionando en tu grafico (seccion 2).

2. En el **Pine Editor** (con el codigo de ese indicador a la vista), busca arriba a la derecha
   el boton **"Publicar script"** (en ingles **"Publish script"**).

3. Se abre una ventana. Rellena:
   - **Titulo:** por ejemplo `PineScope Analyst`.
   - **Descripcion:** explica que hace y como se usa (puedes copiar texto del README).
   - **Visibilidad:**
     - **Publico (Public):** lo ve y usa todo el mundo.
     - **Privado (Invite-only / Private):** solo quien tu autorices. Empieza por aqui si tienes dudas.

4. Acepta las **reglas de la Casa (House Rules)** de TradingView (es un check que debes marcar).

5. Haz clic en **"Publicar"** (**"Publish"**).

6. Ya esta: TradingView te da un **enlace** a tu script. Quien abra ese enlace vera el boton
   **"Agregar al grafico"** y lo usa al instante, sin tocar codigo.

> **Para actualizar** un script ya publicado: vuelve a abrir su codigo en el Pine Editor, pulsa
> **"Publicar script"** y elige **"Actualizar el script existente"** (**"Update existing script"**).

---

## 5. Conectar con IA: alerta con webhook hacia el AI Bridge

Esta es la parte que conecta PineScope con una **IA** (Claude / OpenAI / Gemini) para recibir
un **analisis escrito** cuando salta una senal. Recuerda la idea:

> Pine **no** puede llamar a la IA. Pine solo **dispara una alerta**; esa alerta manda los datos
> a un **servidor puente** (la carpeta `ai-bridge/`), y ese servidor le pregunta a la IA y te
> manda la respuesta (por ejemplo, a Telegram).

### Antes de empezar
- Ten el servidor de `ai-bridge/` **corriendo y accesible por una URL publica**
  (la guia para montarlo esta en **`ai-bridge/README.md`**: incluye Node/Python, ngrok y hosting gratis).
- Anota dos cosas de ese servidor: la **URL del webhook** (algo como `https://tu-app.../webhook`)
  y el **secreto** (`WEBHOOK_SECRET`).

### Crear la alerta en TradingView
1. En el grafico, asegurate de tener agregado **PineScope Analyst** (es el que emite el JSON para IA).

2. Abre sus **ajustes** (la rueda dentada junto al nombre del indicador) y activa la opcion
   **"Emitir JSON para IA"** (input del grupo *Bridge de IA*). Acepta.

3. Crea una **alerta**: haz clic en el icono del **reloj/despertador** ("Alerta" / "Alert") en la
   barra de la derecha, o pulsa **Alt + A**.

4. En **"Condicion"** (Condition), elige el indicador **PineScope Analyst** y, en el segundo
   desplegable, selecciona **"Any alert() function call"**
   (en espanol, algo como **"Cualquier llamada a la funcion alert()"**). Esto es lo que recoge el
   JSON que arma el indicador.

5. Baja hasta **"Notificaciones"** (Notifications) y activa **"Webhook URL"**. Pega ahi la
   **URL del webhook** de tu servidor (`https://tu-app.../webhook`).

6. (Opcional, pero recomendado) En el **mensaje** de la alerta puedes dejar el que genera el
   indicador, o anadir tu **secreto**. Si tu servidor espera el secreto dentro del mensaje, usa
   un JSON como este (cambia `TU_SECRETO`):

   ```json
   {
     "secret": "TU_SECRETO",
     "symbol": "{{ticker}}",
     "timeframe": "{{interval}}",
     "price": {{close}}
   }
   ```

   > Tambien puedes mandar el secreto en la propia URL (`https://tu-app.../webhook?secret=TU_SECRETO`)
   > si tu servidor lo acepta asi. Mira la seccion 7 del `ai-bridge/README.md`.

7. Pulsa **"Crear"** (Create). Desde ahora, cuando el indicador dispare la alerta, el servidor
   recibira los datos, preguntara a la IA y te enviara el analisis (por ejemplo, a Telegram).

> **Recuerda:** los **webhooks de TradingView casi siempre requieren un plan de pago**
> (a dia de hoy, plan *Essential/Pro* o superior). En el plan **gratuito** las alertas existen,
> pero **no dejan mandar webhooks**, asi que esta seccion 5 no funcionara con cuenta gratis.

---

## 6. La alternativa gratis (sin pagar TradingView)

Si no quieres pagar el plan que habilita los webhooks, tienes la **misma idea sin coste** con la
extension de Chrome **FinScope** (en la carpeta `BMW/finscope/`):

- FinScope vive **dentro del navegador**, encima del grafico de TradingView.
- **Captura el grafico** y/o los datos y **llama a la IA con vision** usando el **mismo metodo**
  (velas japonesas: Tendencia + Nivel + Senal) que el puente.
- Te muestra el analisis ahi mismo, **gratis** y con **un clic**, sin webhooks ni servidores.

**Cuando usar cada cosa:**

| Quieres... | Usa |
|---|---|
| Que el analisis te llegue **solo** (por ejemplo a Telegram) al saltar una senal | **AI Bridge** (seccion 5) — requiere plan de pago de TradingView. |
| Pedir el analisis **tu**, con un clic, mientras miras el grafico, **gratis** | **Extension FinScope** — sin webhooks, sin pagar. |

Las dos comparten la misma "cabeza" (mismos proveedores de IA y el mismo metodo), asi que el
estilo del analisis es coherente entre ambas.

---

## 7. Si algo no sale

- **No veo el Pine Editor:** mira en la **barra inferior** del grafico (no arriba). Si no aparece,
  recarga la pagina o entra desde la vista de **"Grafico"** completa, no desde un mini-grafico.

- **El boton dice "Add to chart" y no "Agregar al grafico":** es lo mismo, tu TradingView esta en
  ingles. Puedes cambiar el idioma en el menu de tu perfil (abajo a la izquierda).

- **Sale un error rojo al agregar:** revisa que pegaste **todo** el archivo (desde la primera linea
  `//@version=6` hasta el final) y que **borraste** el codigo de ejemplo que venia antes.

- **No puedo activar el Webhook URL en la alerta:** tu plan de TradingView no incluye webhooks.
  Usa la **alternativa gratis** (seccion 6) o sube de plan.

- **No me llega nada a Telegram:** el problema suele estar en el servidor `ai-bridge/`, no en
  TradingView. Revisa la seccion **"Si algo falla"** del `ai-bridge/README.md`.

---

*Analisis educativo, NO recomendacion de compra/venta. Los indicadores pueden fallar.*
