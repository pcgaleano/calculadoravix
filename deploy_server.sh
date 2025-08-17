#!/bin/bash

echo "🚀 Iniciando deploy de CalculadoraVIX..."

# 1. Clonar repositorio
echo "📥 Clonando repositorio..."
git clone https://github.com/pcgaleano/calculadoravix.git
cd calculadoravix

# 2. Configurar entorno Python
echo "🐍 Configurando entorno Python..."
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
echo "📦 Instalando dependencias..."
cd backend
pip install -r requirements.txt

# 4. Iniciar servidor en background
echo "🔥 Iniciando servidor..."
nohup python main.py > server.log 2>&1 &
SERVER_PID=$!
echo "Servidor iniciado con PID: $SERVER_PID"

# 5. Esperar que inicie
echo "⏳ Esperando que el servidor inicie..."
sleep 15

# 6. Ejecutar carga inicial
echo "📊 Ejecutando carga inicial de datos..."
curl -X POST "http://127.0.0.1:8000/initial-data-load"

echo "✅ Deploy completado!"
echo "🌐 Servidor disponible en: http://tu-servidor:8000"
echo "📋 API docs en: http://tu-servidor:8000/docs"
echo "📝 Logs en: server.log"