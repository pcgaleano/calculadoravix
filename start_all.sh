#!/bin/bash

echo "🚀 Iniciando Trading Dashboard Completo..."
echo
echo "📋 Esto abrirá 2 terminales:"
echo "  1️⃣  Backend API (Python FastAPI)"
echo "  2️⃣  Frontend App (React + Tailwind)"
echo
echo "⏱️  Espera unos segundos para que todo cargue..."
echo

# Función para limpiar procesos al salir
cleanup() {
    echo
    echo "🛑 Deteniendo servicios..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    # Limpiar procesos adicionales
    pkill -f "uvicorn main:app" 2>/dev/null
    pkill -f "npm run dev" 2>/dev/null
    exit
}

# Capturar señales para limpieza
trap cleanup SIGINT SIGTERM

echo "🔥 Iniciando Backend..."
# Iniciar backend en segundo plano
cd backend && python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Esperar 5 segundos
sleep 5

echo "🎨 Iniciando Frontend..."
# Iniciar frontend en segundo plano (puerto 4000 para money.wann.com.ar)
cd frontend && PORT=4000 npm start &
FRONTEND_PID=$!
cd ..

echo
echo "✅ Todo iniciado!"
echo
echo "🌐 Accede a tu dashboard en: http://localhost:4000 o https://money.wann.com.ar"
echo "📊 API documentación en: http://127.0.0.1:8000/docs"
echo
echo "💡 Tip: Espera a que ambas terminales carguen completamente"
echo "🛑 Presiona Ctrl+C para detener todos los servicios"
echo

# Mantener el script corriendo
wait
