#!/bin/bash
set -e

echo "========================================="
echo "  RÖS'S IA - Setup"
echo "========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 1. Install Ollama
echo ""
echo -e "${YELLOW}[1/5] Comprobando Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo "Instalando Ollama..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install ollama
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
else
    echo -e "${GREEN}Ollama ya instalado: $(ollama --version)${NC}"
fi

# 2. Start Ollama if not running
echo ""
echo -e "${YELLOW}[2/5] Iniciando Ollama...${NC}"
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Arrancando servidor Ollama..."
    ollama serve &
    sleep 3
else
    echo -e "${GREEN}Ollama ya está corriendo${NC}"
fi

# 3. Pull models
echo ""
echo -e "${YELLOW}[3/5] Descargando modelos...${NC}"

echo "Descargando Qwen 2.5 7B (LLM principal)..."
ollama pull qwen2.5:7b

echo "Descargando Qwen 2.5 3B (LLM ligero para CPU)..."
ollama pull qwen2.5:3b

echo "Descargando BGE-M3 (embeddings multilingüe)..."
ollama pull bge-m3

# 4. Python virtual environment
echo ""
echo -e "${YELLOW}[4/5] Configurando entorno Python...${NC}"
if [ ! -d ".venv" ]; then
    # Python 3.12 requerido (3.14 no es compatible con ChromaDB aún)
    PYTHON_BIN=""
    if command -v python3.12 &> /dev/null; then
        PYTHON_BIN="python3.12"
    elif [ -f "/opt/homebrew/bin/python3.12" ]; then
        PYTHON_BIN="/opt/homebrew/bin/python3.12"
    else
        echo "Python 3.12 no encontrado. Instálalo con: brew install python@3.12"
        echo "Intentando con python3..."
        PYTHON_BIN="python3"
    fi
    $PYTHON_BIN -m venv .venv
    echo "Entorno virtual creado en .venv/ con $($PYTHON_BIN --version)"
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}Dependencias Python instaladas${NC}"

# 5. Create .env from example if not exists
echo ""
echo -e "${YELLOW}[5/5] Configuración...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ".env creado desde .env.example"
else
    echo -e "${GREEN}.env ya existe${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}  Setup completado!${NC}"
echo "========================================="
echo ""
echo "Próximos pasos:"
echo "  1. Coloca tus documentos en data/documents/"
echo "  2. Ejecuta: source .venv/bin/activate"
echo "  3. Ingesta documentos: python scripts/ingest.py"
echo "  4. Inicia el servidor: python -m backend.main"
echo "  5. Abre http://localhost:8000"
