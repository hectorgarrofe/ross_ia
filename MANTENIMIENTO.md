# Mantenimiento del Asistente IA RÖS'S

## 1. Arrancar el sistema

Necesitas dos cosas corriendo: Ollama (el motor de IA) y el servidor web.

```bash
# 1. Arranca Ollama (si no está corriendo ya)
brew services start ollama

# 2. Activa el entorno Python y arranca el servidor
cd ~/proyectos/IA/ross_ia
source .venv/bin/activate
python -m backend.main
```

El asistente estará disponible en **http://localhost:8000**

Para parar el servidor, pulsa `Ctrl+C` en la terminal.

---

## 2. Ampliar el conocimiento con nuevos documentos

El asistente responde basándose en los documentos que le proporcionas. Para que conozca información nueva:

### Formatos soportados
- **PDF** (.pdf)
- **Word** (.docx)
- **Texto plano** (.txt)

### Pasos

**A) Si solo AÑADES documentos nuevos** (sin modificar los existentes):

```bash
# 1. Copia tus documentos nuevos a la carpeta
cp mis-nuevos-docs/* data/documents/

# 2. Ejecuta la ingesta (añade sin borrar lo anterior)
source .venv/bin/activate
python scripts/ingest.py
```

**B) Si MODIFICAS documentos que ya estaban:**

```bash
# 1. Actualiza los ficheros en data/documents/

# 2. Ejecuta la ingesta con --reset (borra todo y recrea desde cero)
source .venv/bin/activate
python scripts/ingest.py --reset
```

> Usa `--reset` siempre que modifiques o elimines un documento existente. Sin `--reset`, los chunks del documento anterior seguirían ahí y podrían generar respuestas contradictorias.

### No hace falta reiniciar el servidor

Los cambios en los documentos se reflejan inmediatamente en las siguientes preguntas. No necesitas parar ni reiniciar el servidor FastAPI.

### Consejo para buenos resultados

- Los documentos deben estar en **texto legible** (no escaneos de imagen sin OCR).
- Usa **UTF-8** para ficheros .txt (importante para acentos y ñ).
- Cuanta más información clara y estructurada, mejor responderá la IA.

---

## 3. Cambiar el modelo de IA

El modelo determina la calidad y velocidad de las respuestas. Se configura en el fichero `.env` en la raíz del proyecto.

### Modelos disponibles

| Modelo | Tamaño | Velocidad | Calidad | Uso recomendado |
|---|---|---|---|---|
| `qwen2.5:7b` | 4.7 GB | Media | Alta | Demo, PC con buena RAM |
| `qwen2.5:3b` | 2 GB | Rápida | Buena | Produccion, PC sin GPU |

### Cambiar el modelo

1. Abre el fichero `.env` con cualquier editor:
   ```bash
   nano .env
   ```

2. Cambia la linea `ROSS_LLM_MODEL`:
   ```
   # Para el modelo potente (demo):
   ROSS_LLM_MODEL=qwen2.5:7b

   # Para el modelo ligero (produccion CPU):
   ROSS_LLM_MODEL=qwen2.5:3b
   ```

3. Reinicia el servidor (Ctrl+C y vuelve a ejecutar `python -m backend.main`).

### Probar un modelo completamente nuevo

Si quieres probar otro modelo de Ollama:

```bash
# 1. Descargalo
ollama pull nombre-del-modelo

# 2. Pruebalo directamente en terminal
ollama run nombre-del-modelo "Hola, responde en espanol"

# 3. Si te convence, ponlo en .env
ROSS_LLM_MODEL=nombre-del-modelo
```

> Puedes ver todos los modelos disponibles en https://ollama.com/library

---

## 4. Personalizar la personalidad del asistente

El comportamiento del asistente se define en el "system prompt", que esta en:

```
backend/prompts/templates.py
```

El prompt actual dice:

```
Eres el asistente virtual de RÖS'S, especializado en equipos de masaje profesional.
Tu funcion es ayudar a los usuarios respondiendo preguntas sobre los productos,
funcionalidades, mantenimiento y uso de las maquinas de masaje RÖS'S.

Reglas:
- Responde SIEMPRE en espanol.
- Basa tus respuestas UNICAMENTE en el contexto proporcionado.
- Si no encuentras la informacion en el contexto, di: "No tengo informacion
  suficiente sobre eso. Te recomiendo contactar con el equipo de RÖS'S."
- Se conciso y profesional.
- No inventes informacion que no este en el contexto.
```

Puedes editarlo para cambiar el tono, añadir instrucciones o ajustar el comportamiento. Despues de editarlo, reinicia el servidor.

---

## 5. Comprobar el estado del sistema

Abre en el navegador o ejecuta:

```bash
curl http://localhost:8000/api/health
```

Respuesta de ejemplo:
```json
{
  "status": "ok",
  "ollama": true,
  "ollama_model": "qwen2.5:7b",
  "embedding_model": "bge-m3",
  "documents_count": 1,
  "chunks_count": 8
}
```

| Campo | Significado |
|---|---|
| `status` | `ok` = todo funciona. `degraded` = Ollama no disponible |
| `ollama` | `true` si Ollama esta corriendo y responde |
| `ollama_model` | Modelo de IA configurado actualmente |
| `embedding_model` | Modelo usado para buscar en documentos |
| `documents_count` | Numero de documentos ingestados |
| `chunks_count` | Numero de fragmentos indexados (mas = mas conocimiento) |

---

## 6. Configuracion completa (.env)

Todas las variables se configuran en el fichero `.env`. Prefijo: `ROSS_`

| Variable | Por defecto | Descripcion |
|---|---|---|
| `ROSS_LLM_MODEL` | `qwen2.5:7b` | Modelo de IA para generar respuestas |
| `ROSS_EMBEDDING_MODEL` | `bge-m3` | Modelo para buscar documentos relevantes |
| `ROSS_OLLAMA_BASE_URL` | `http://localhost:11434` | URL del servidor Ollama |
| `ROSS_CHUNK_SIZE` | `512` | Tamano de los fragmentos de texto |
| `ROSS_CHUNK_OVERLAP` | `50` | Solapamiento entre fragmentos |
| `ROSS_RETRIEVAL_TOP_K` | `5` | Cuantos fragmentos usa como contexto |
| `ROSS_PORT` | `8000` | Puerto del servidor web |

> Normalmente solo necesitaras cambiar `ROSS_LLM_MODEL`. El resto de valores estan optimizados.

---

## 7. Solucion de problemas

### Ollama no arranca
```bash
# Comprueba si esta corriendo
curl http://localhost:11434/api/tags

# Si no responde, arrancalo
brew services start ollama

# Si sigue sin funcionar, reinicia el servicio
brew services restart ollama
```

### El servidor no arranca
```bash
# Asegurate de estar en el directorio correcto con el venv activado
cd ~/proyectos/IA/ross_ia
source .venv/bin/activate
python -m backend.main
```

Si da error de dependencias:
```bash
pip install -r requirements.txt
```

### Las respuestas no son buenas
- **Comprueba que hay documentos ingestados**: `curl http://localhost:8000/api/health` y mira `chunks_count`
- **Reingestia los documentos**: `python scripts/ingest.py --reset`
- **Prueba un modelo mas grande**: cambia a `qwen2.5:7b` en `.env`
- **Mejora los documentos fuente**: documentos mas claros y estructurados producen mejores respuestas

### La IA responde con informacion inventada
Esto puede pasar si los documentos no cubren la pregunta. Soluciones:
- Añade mas documentos que cubran el tema
- El system prompt ya le dice que no invente, pero puedes reforzarlo en `backend/prompts/templates.py`

### Respuestas muy lentas
- Cambia al modelo ligero: `ROSS_LLM_MODEL=qwen2.5:3b` en `.env`
- Comprueba que Ollama no este procesando otra peticion al mismo tiempo
