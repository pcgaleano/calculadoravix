#!/bin/bash

echo "🚀 Creando Frontend CalculadoraVIX..."

# Ir al directorio del proyecto
cd /sitiosweb/money.wann.com.ar/calculadoravix/

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "📦 Instalando Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Crear proyecto React
echo "⚛️ Creando proyecto React..."
npx create-react-app frontend
cd frontend

# Instalar dependencias adicionales
echo "📦 Instalando dependencias..."
npm install axios recharts react-router-dom @headlessui/react @heroicons/react

# Crear estructura de directorios
echo "📁 Creando estructura..."
mkdir -p src/components src/pages src/services src/styles

# Variables de entorno
echo "⚙️ Configurando variables de entorno..."
cat > .env << 'EOF'
REACT_APP_API_URL=https://money.wann.com.ar
REACT_APP_SITE_NAME=CalculadoraVIX
REACT_APP_SITE_DESCRIPTION=Calculadora Williams VIX Fix gratuita para encontrar mínimos del mercado
EOF

echo "✅ Frontend base creado!"
echo "📂 Directorio: /sitiosweb/money.wann.com.ar/calculadoravix/frontend"
echo "🔧 Próximo paso: Crear componentes"