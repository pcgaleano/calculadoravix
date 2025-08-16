#!/bin/bash

echo "🔍 Verificando dependencias del Trading Dashboard..."
echo

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para check
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "✅ $1: ${GREEN}$(command -v $1)${NC}"
        if [ "$1" = "python3" ]; then
            echo -e "   Versión: ${GREEN}$(python3 --version)${NC}"
        elif [ "$1" = "node" ]; then
            echo -e "   Versión: ${GREEN}$(node --version)${NC}"
        elif [ "$1" = "npm" ]; then
            echo -e "   Versión: ${GREEN}$(npm --version)${NC}"
        fi
        return 0
    else
        echo -e "❌ $1: ${RED}No encontrado${NC}"
        return 1
    fi
}

# Verificar comandos básicos
echo "📋 Dependencias del Sistema:"
check_command python3
PYTHON_OK=$?

check_command pip3
PIP_OK=$?

check_command node
NODE_OK=$?

check_command npm
NPM_OK=$?

echo

# Verificar puertos
echo "🌐 Verificando puertos:"
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "❌ Puerto 3000: ${RED}En uso${NC}"
    lsof -i :3000
else
    echo -e "✅ Puerto 3000: ${GREEN}Libre${NC}"
fi

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "❌ Puerto 8000: ${RED}En uso${NC}"
    lsof -i :8000
else
    echo -e "✅ Puerto 8000: ${GREEN}Libre${NC}"
fi

echo

# Verificar dependencias Python
echo "🐍 Verificando dependencias Python:"
if [ $PYTHON_OK -eq 0 ] && [ $PIP_OK -eq 0 ]; then
    cd backend 2>/dev/null
    if [ -f "requirements.txt" ]; then
        echo "📦 Instalando/Verificando dependencias Python..."
        pip3 install -r requirements.txt --quiet
        echo -e "✅ Dependencias Python: ${GREEN}Instaladas${NC}"
    else
        echo -e "❌ ${RED}requirements.txt no encontrado${NC}"
    fi
    cd ..
else
    echo -e "❌ ${RED}Python3 o pip3 no disponible${NC}"
fi

echo

# Verificar dependencias Node.js
echo "📦 Verificando dependencias Node.js:"
if [ $NODE_OK -eq 0 ] && [ $NPM_OK -eq 0 ]; then
    cd frontend 2>/dev/null
    if [ -f "package.json" ]; then
        echo "📦 Verificando dependencias Node.js..."
        if [ -d "node_modules" ]; then
            echo -e "✅ node_modules: ${GREEN}Existe${NC}"
        else
            echo -e "⚠️  node_modules: ${YELLOW}No existe, ejecuta 'npm install'${NC}"
        fi
    else
        echo -e "❌ ${RED}package.json no encontrado${NC}"
    fi
    cd ..
else
    echo -e "❌ ${RED}Node.js o npm no disponible${NC}"
fi

echo

# Verificar permisos de scripts
echo "🔐 Verificando permisos de scripts:"
for script in start_all.sh start_backend.sh start_frontend.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "✅ $script: ${GREEN}Ejecutable${NC}"
        else
            echo -e "⚠️  $script: ${YELLOW}Sin permisos de ejecución${NC}"
            echo "   Ejecuta: chmod +x $script"
        fi
    else
        echo -e "❌ $script: ${RED}No encontrado${NC}"
    fi
done

echo

# Resumen final
echo "📊 Resumen:"
if [ $PYTHON_OK -eq 0 ] && [ $PIP_OK -eq 0 ] && [ $NODE_OK -eq 0 ] && [ $NPM_OK -eq 0 ]; then
    echo -e "✅ ${GREEN}¡Todo listo para ejecutar el Trading Dashboard!${NC}"
    echo
    echo "🚀 Para iniciar:"
    echo "   ./start_all.sh"
    echo
    echo "🌐 URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend:  http://127.0.0.1:8000"
    echo "   API Docs: http://127.0.0.1:8000/docs"
else
    echo -e "❌ ${RED}Faltan dependencias. Revisa los errores arriba.${NC}"
    echo
    echo "📋 Comandos de instalación rápida:"
    echo "   sudo apt update"
    echo "   sudo apt install python3 python3-pip nodejs npm"
    echo "   chmod +x *.sh"
fi

echo