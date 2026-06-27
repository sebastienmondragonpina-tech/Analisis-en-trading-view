# Como agregar PineScope Pro a TradingView

Guia paso a paso, **con clics**, para poner los indicadores de PineScope Pro en tu grafico,
publicarlos para que otros los usen, y (opcional) conectarlos con una **IA** mediante una
**alerta con webhook**.

No necesitas saber programar. Casi todo es **copiar y pegar**.

---

## Indice

1. [Lo que necesitas](#1-lo-que-necesitas)
2. [Agregar un indicador (lo haras 4 veces)](#2-agregar-un-indicador-lo-haras-4-veces)
3. [Los 4 archivos que vas a pegar](#3-los-4-archivos-que-vas-a-pegar)
4. [Ajustes utiles despues de agregar](#4-ajustes-utiles-despues-de-agregar)
5. [Publicar tu indicador para que otros lo usen](#5-publicar-tu-indicador-para-que-otros-lo-usen)
6. [Conectar con IA: alerta con webhook hacia el AI Bridge](#6-conectar-con-ia-alerta-con-webhook-hacia-el-ai-bridge)
7. [La alternativa gratis (sin pagar TradingView)](#7-la-alternativa-gratis-sin-pagar-tradingview)
8. [Si algo no sale](#8-si-algo-no-sale)

---

## 1. Lo que necesitas

- Una **cuenta de TradingView** (la gratuita sirve para *agregar* y *publicar* indicadores).
- Un **navegador** (Chrome, Edge, etc.) en una computadora. Es mas comodo que en el celular.
- Los **4 archivos `.pine`** de este proyecto (los abres y copias su contenido).

> Para la parte de **IA con webhook** (seccion 6) normalmente hace falta un **plan de pago** de
> TradingView. Para *agregar* y *publicar* indicadores **no** hace falta pagar.

---

## 2. Agregar un indicador (lo haras 4 veces)

Vas a repetir estos mismos pasos **una vez por cada indicador** (son 4 en total).

1. **Abre TradingView** y entra a un grafico. Lo mas facil: ve a `tradingview.com`, inicia sesion
   y haz clic en **"Grafico"** (o **"Chart"**) en el menu de arriba.

2. Elige un activo cualquiera (por ejemplo escribe `NVDA`, `AAPL` o `BTCUSD` en la barra de busqueda
   de arriba a la izquierda y pulsa Enter).

3. En la **barra de abajo** del grafico, haz clic en **"Pine Editor"** (en espanol puede decir
   **"Editor de Pine"**). Se abrira un panel de codigo en la parte inferior.

   > Si no ves esa barra: no mires arriba a la derecha; mira **abajo del todo**. Si sigue sin
   > aparecer, recarga la pagina o busca el icono del Pine Editor en la barra inferior.

4. En el Pine Editor, **borra todo lo que haya** dentro (haz clic dentro del codigo, selecciona todo
   con **Ctrl + A** y borra con **Suprimir / Delete**).

5. Abre el archivo `.pine` correspondiente (ver la lista en la seccion 3), **selecciona todo su
   contenido** (Ctrl + A) y **copialo** (Ctrl + C). Para abrirlo basta el Bloc de notas (Notepad) o
   cualquier editor de texto.

6. Vuelve al Pine Editor de TradingView y **pega** (Ctrl + V). Debe quedar **todo** el codigo
   pegado, desde la primera linea `//@version=6` hasta el final.

7. Haz clic en el boton **"Agregar al grafico"** (en ingles **"Add to chart"**), arriba a la derecha
   del Pine Editor.

8. Listo: el indicador aparece **sobre el grafico** (Dashboard y Patterns) o como **panel abajo**
   (Stochastic y MACD), segun el indicador.

9. **Repite los pasos 4 a 8** con los otros archivos. Cada indicador se agrega por separado; puedes
   tener los cuatro a la vez en el mismo grafico.

> **Orden recomendado:** empieza por el **Dashboard** (es el "cerebro" y el unico que emite el JSON
> para IA), luego **Stochastic**, **MACD** y **Patterns**.

---

## 3. Los 4 archivos que vas a pegar

| # | Indicador | Archivo a abrir y pegar | Donde aparece |
|---|---|---|---|
| 1 | **Dashboard** | `pine/PineScope_Dashboard.pine` | **Encima** del precio (matriz por marco, resumen tactico, semaforo, S/R, prediccion). |
| 2 | **Stochastic** | `pine/PineScope_Stochastic.pine` | **Panel inferior** (%K/%D + zonas 20/80 + tabla TF/ESTADO/FUERZA). |
| 3 | **MACD** | `pine/PineScope_MACD.pine` | **Panel inferior** (histograma 4 colores + lineas + tabla TF/HIST/ESTADO/FUERZA). |
| 4 | **Patterns** | `pine/PineScope_Patterns.pine` | **Encima** del precio (etiquetas de patrones de velas con filtro de contexto). |

Para abrir un archivo `.pine` y copiar su texto: abrelo con el Bloc de notas (Notepad) o cualquier
editor de texto, pulsa **Ctrl + A** (seleccionar todo) y **Ctrl + C** (copiar).

---

## 4. Ajustes utiles despues de agregar

Despues de agregar cada indicador, pasa el mouse por su **nombre** (arriba a la izquierda del
grafico) y haz clic en la **rueda dentada (ajustes)**. Ahi puedes:

- **Activar/desactivar** las tablas (la matriz, el resumen tactico, el semaforo, S/R, prediccion).
- **Mover las tablas** de posicion (arriba/abajo, izquierda/derecha) para que no tapen el precio.
- Cambiar longitudes (RSI, EMAs, MACD, estocastico, ATR) y umbrales del semaforo y la tendencia.
- En el **Dashboard**, activar **"Emitir IA (webhook)"** y poner tu **secreto** (seccion 6).

> Consejo: si las tablas se montan unas con otras, dales posiciones distintas (por ejemplo el
> Dashboard arriba-derecha y su resumen tactico abajo-derecha).

---

## 5. Publicar tu indicador para que otros lo usen

Publicar significa subir el indicador a la **comunidad de TradingView** para que cualquiera lo
encuentre y lo agregue **con un solo clic**, sin copiar y pegar codigo.

1. Asegurate de que el indicador esta agregado y funcionando en tu grafico (seccion 2).

2. En el **Pine Editor** (con el codigo de ese indicador a la vista), busca arriba a la derecha el
   boton **"Publicar script"** (en ingles **"Publish script"**).

3. Se abre una ventana. Rellena:
   - **Titulo:** por ejemplo `PineScope Pro — Dashboard`.
   - **Descripcion:** explica que hace y como se usa (puedes copiar texto del README).
   - **Visibilidad:**
     - **Publico (Public):** lo ve y usa todo el mundo.
     - **Privado (Invite-only / Private):** solo quien tu autorices. Empieza por aqui si tienes dudas.

4. Acepta las **reglas de la Casa (House Rules)** de TradingView (es un check que debes marcar).

5. Haz clic en **"Publicar"** (**"Publish"**).

6. Ya esta: TradingView te da un **enlace** a tu script. Quien lo abra vera el boton **"Agregar al
   grafico"** y lo usa al instante, sin tocar codigo.

> **Para actualizar** un script ya publicado: vuelve a abrir su codigo en el Pine Editor, pulsa
> **"Publicar script"** y elige **"Actualizar el script existente"** (**"Update existing script"**).

---

## 6. Conectar con IA: alerta con webhook hacia el AI Bridge

Esta es la parte que conecta PineScope Pro con una **IA** (Claude / OpenAI / Gemini) para recibir
un **analisis escrito** cuando se cierra cada vela. Recuerda la idea:

> Pine **no** puede llamar a la IA. El **Dashboard** solo **dispara una alerta** con un **JSON v2.0**
> que lleva **todos los datos calculados**; esa alerta manda el JSON a un **servidor puente** (la
> carpeta `ai-bridge/`), y ese servidor le pregunta a la IA y te manda la respuesta (por ejemplo, a
> Telegram). El detalle de que lleva el JSON y como se usa esta en
> [docs/ANALISIS-Y-IA.md](docs/ANALISIS-Y-IA.md).

### Antes de empezar
- Ten el servidor de `ai-bridge/` **corriendo y accesible por una URL publica** (la guia para
  montarlo esta en **[ai-bridge/README.md](ai-bridge/README.md)**: incluye Node/Python, ngrok y
  hosting gratis tipo Render/Railway).
- Anota dos cosas de ese servidor: la **URL del webhook** (algo como `https://tu-app.../webhook`) y
  el **secreto** (`WEBHOOK_SECRET`).

### Crear la alerta en TradingView
1. En el grafico, asegurate de tener agregado el **Dashboard** (es el unico que emite el JSON para IA).

2. Abre sus **ajustes** (la rueda dentada junto al nombre del indicador), activa la opcion
   **"Emitir IA (webhook)"** y pon en el input **"Secreto webhook"** exactamente el mismo secreto que
   tu `WEBHOOK_SECRET` del servidor. Acepta.

3. Crea una **alerta**: haz clic en el icono del **reloj/despertador** ("Alerta" / "Alert") en la
   barra de la derecha, o pulsa **Alt + A**.

4. En **"Condicion"** (Condition), elige el indicador **PineScope Pro — Dashboard** y, en el segundo
   desplegable, selecciona **"Any alert() function call"** (en espanol, algo como **"Cualquier
   llamada a la funcion alert()"**). Esto recoge el JSON que arma el indicador.

5. Baja hasta **"Notificaciones"** (Notifications) y activa **"Webhook URL"**. Pega ahi la **URL del
   webhook** de tu servidor (`https://tu-app.../webhook`).

6. **No necesitas escribir el mensaje a mano.** El Dashboard ya construye el JSON v2.0 completo (con
   el `secret` dentro). Deja el mensaje de la alerta tal como viene del indicador.

7. Pulsa **"Crear"** (Create). Desde ahora, al cierre de cada vela el indicador dispara la alerta, el
   servidor recibe los datos, pregunta a la IA y te envia el analisis (por ejemplo, a Telegram).

> **Recuerda (importante):** los **webhooks de TradingView casi siempre requieren un plan de pago**
> (a dia de hoy, plan *Essential/Pro* o superior). En el plan **gratuito** las alertas existen, pero
> **no dejan mandar webhooks**, asi que esta seccion 6 **no funcionara con cuenta gratis**.

---

## 7. La alternativa gratis (sin pagar TradingView)

Si no quieres pagar el plan que habilita los webhooks, tienes la **misma idea sin coste** con la
extension de Chrome **FinScope** (en la carpeta `BMW/finscope/`):

- FinScope vive **dentro del navegador**, encima del grafico de TradingView.
- **Captura el grafico como imagen** y/o los datos y **llama a la IA con vision** usando el **mismo
  metodo** (velas japonesas: Tendencia + Nivel + Senal) que el puente.
- Te muestra el analisis ahi mismo, **gratis** y con **un clic**, sin webhooks ni servidores.

**Cuando usar cada cosa:**

| Quieres... | Usa |
|---|---|
| Que el analisis te llegue **solo** (por ejemplo a Telegram) al cierre de cada vela | **AI Bridge** (seccion 6) — requiere plan de pago de TradingView. La IA recibe los **datos nativos exactos**. |
| Pedir el analisis **tu**, con un clic, mientras miras el grafico, **gratis** | **Extension FinScope** — sin webhooks, sin pagar. La IA recibe la **imagen** del grafico. |

Las dos comparten la misma "cabeza" (mismos proveedores de IA y el mismo metodo), asi que el estilo
del analisis es coherente entre ambas.

---

## 8. Si algo no sale

- **No veo el Pine Editor:** mira en la **barra inferior** del grafico (no arriba). Si no aparece,
  recarga la pagina o entra desde la vista de **"Grafico"** completa, no desde un mini-grafico.

- **El boton dice "Add to chart" y no "Agregar al grafico":** es lo mismo, tu TradingView esta en
  ingles. Puedes cambiar el idioma desde el menu de tu perfil (abajo a la izquierda).

- **Sale un error rojo al agregar:** revisa que pegaste **todo** el archivo (desde `//@version=6`
  hasta el final) y que **borraste** el codigo de ejemplo que venia antes.

- **Las tablas tapan el precio o se solapan:** abre los ajustes (rueda dentada) y cambia la
  **posicion** de cada tabla (seccion 4).

- **No puedo activar el Webhook URL en la alerta:** tu plan de TradingView no incluye webhooks. Usa
  la **alternativa gratis** (seccion 7) o sube de plan.

- **No me llega nada a Telegram:** el problema suele estar en el servidor `ai-bridge/`, no en
  TradingView. Revisa la seccion **"Si algo falla"** del [ai-bridge/README.md](ai-bridge/README.md)
  y comprueba que el **secreto** de la alerta coincide con `WEBHOOK_SECRET`.

---

*Analisis educativo, NO recomendacion de compra/venta. Los indicadores y la IA pueden fallar.*
