# Requisitos para instalar RÖS IA en Windows

## 1. Requisitos de hardware

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| RAM | 8 GB | 16 GB |
| Disco libre | 12 GB | 20 GB |
| CPU | x64 (Intel/AMD moderno) | Intel i5 / AMD Ryzen 5 o superior |
| GPU | No necesaria | Opcional (NVIDIA acelera las respuestas) |
| Sistema operativo | Windows 10 (64 bits) | Windows 10/11 (64 bits) |

> **Nota:** Con 8 GB de RAM se recomienda usar el modelo ligero (`qwen2.5:3b`). Con 16 GB se puede usar el modelo completo (`qwen2.5:7b`) que da respuestas de mayor calidad.

---

## 2. Software necesario

Solo se necesitan **dos programas** (ambos gratuitos):

### A) Python 3.12

- **Descargar desde:** https://www.python.org/downloads/
- **Version:** 3.12.x (NO instalar 3.13 o superior)
- **Durante la instalacion:** Marcar la casilla **"Add Python to PATH"**

### B) Ollama

- **Descargar desde:** https://ollama.com/download/windows
- Instalar normalmente (siguiente, siguiente, finalizar)
- Ollama se ejecuta como servicio en segundo plano automaticamente

### C) Navegador web

- Chrome, Firefox, Edge o cualquier navegador moderno

---

## 3. Espacio en disco necesario

| Elemento | Tamano aproximado |
|----------|-------------------|
| Proyecto (codigo fuente) | ~50 MB |
| Entorno virtual Python (.venv) | ~400 MB |
| Modelo qwen2.5:7b (LLM principal) | 4.7 GB |
| Modelo bge-m3 (embeddings) | 1.2 GB |
| Modelo qwen2.5:3b (LLM ligero, opcional) | 2 GB |
| **Total aproximado** | **~8-10 GB** |

---

## 4. Guia de instalacion paso a paso

### Paso 1: Instalar Python 3.12

1. Ir a https://www.python.org/downloads/
2. Descargar Python 3.12.x (la version mas reciente de 3.12)
3. Ejecutar el instalador
4. **IMPORTANTE:** Marcar "Add Python to PATH" antes de instalar
5. Hacer clic en "Install Now"

### Paso 2: Instalar Ollama

1. Ir a https://ollama.com/download/windows
2. Descargar el instalador de Windows
3. Ejecutar el instalador y seguir los pasos
4. Ollama se iniciara automaticamente como servicio

### Paso 3: Copiar el proyecto

Copiar la carpeta `ross_ia` a una ruta corta, por ejemplo:
```
C:\ross_ia
```
> **Importante:** Evitar rutas muy largas o con espacios. Cuanto mas cerca de `C:\`, mejor.

### Paso 4: Abrir terminal (CMD o PowerShell)

1. Pulsar `Windows + R`
2. Escribir `cmd` y pulsar Enter
3. Navegar a la carpeta del proyecto:
```cmd
cd C:\ross_ia
```

### Paso 5: Crear entorno virtual de Python

```cmd
python -m venv .venv
```

### Paso 6: Activar el entorno virtual

```cmd
.venv\Scripts\activate
```

Deberia aparecer `(.venv)` al inicio de la linea del terminal.

### Paso 7: Instalar dependencias de Python

```cmd
pip install -r requirements.txt
```

Esperar a que termine (puede tardar unos minutos).

### Paso 8: Descargar los modelos de IA

Esto se hace **una sola vez** y requiere conexion a internet. Puede tardar entre 20 y 45 minutos dependiendo de la velocidad de internet.

```cmd
ollama pull qwen2.5:7b
ollama pull bge-m3
```

> **Si la maquina tiene poca RAM (8 GB o menos):** Usar el modelo ligero en su lugar:
> ```cmd
> ollama pull qwen2.5:3b
> ```
> Y editar el archivo `.env` cambiando `ROSS_LLM_MODEL=qwen2.5:7b` por `ROSS_LLM_MODEL=qwen2.5:3b`

### Paso 9: Colocar los documentos

Copiar los archivos PDF, Word (.docx) o texto (.txt) que el chatbot debe conocer dentro de la carpeta:
```
C:\ross_ia\data\documents\
```

### Paso 10: Ingestar los documentos

Este paso procesa los documentos y los prepara para que el chatbot pueda buscar en ellos:

```cmd
python scripts/ingest.py
```

> Si se anaden nuevos documentos mas adelante, ejecutar de nuevo este comando. Para reiniciar completamente la base de datos de documentos, usar: `python scripts/ingest.py --reset`

### Paso 11: Arrancar el servidor

```cmd
python -m backend.main
```

Deberia aparecer un mensaje como:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Paso 12: Abrir el chatbot

Abrir el navegador web y entrar a:
```
http://localhost:8000
```

El chatbot ya esta listo para usar.

---

## 5. Como arrancar el chatbot cada dia

Cada vez que se reinicie la maquina o se quiera iniciar el chatbot:

```cmd
cd C:\ross_ia
.venv\Scripts\activate
python -m backend.main
```

Luego abrir el navegador en `http://localhost:8000`.

> Ollama se inicia automaticamente con Windows, no hace falta arrancarlo manualmente.

---

## 6. Verificar que todo funciona

Con el servidor arrancado, abrir en el navegador:
```
http://localhost:8000/api/health
```

Deberia mostrar algo como:
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

Si `ollama` aparece como `false`, significa que el servicio de Ollama no esta corriendo.

---

## 7. Resolucion de problemas

### "python" no se reconoce como comando
- Python no se anadio al PATH durante la instalacion
- Reinstalar Python marcando la casilla "Add Python to PATH"

### Ollama no responde / `ollama: false` en el health check
- Buscar "Ollama" en el menu Inicio y ejecutarlo
- Si el antivirus lo bloquea, anadirlo como excepcion

### Los caracteres especiales (tildes, n) se ven mal en el terminal
- Ejecutar este comando antes de arrancar el servidor:
```cmd
chcp 65001
```

### El servidor no arranca / error de modulo no encontrado
- Verificar que el entorno virtual esta activado (debe verse `(.venv)` en el terminal)
- Ejecutar `pip install -r requirements.txt` de nuevo

### Respuestas muy lentas
- Con 8 GB de RAM, usar el modelo ligero (`qwen2.5:3b`)
- Cerrar otras aplicaciones que consuman mucha memoria

### El chatbot no encuentra informacion en los documentos
- Verificar que los documentos estan en `data\documents\`
- Ejecutar `python scripts/ingest.py` despues de anadir documentos nuevos

---

## 8. Informacion adicional

- **Todo funciona en local:** Una vez instalado, no se necesita conexion a internet
- **Privacidad total:** Ningun dato sale de la maquina, todo el procesamiento de IA es local
- **Formatos de documentos soportados:** PDF, Word (.docx), texto (.txt)
- **Puerto del servidor:** 8000 (configurable en el archivo `.env`)
