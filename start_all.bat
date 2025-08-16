@echo off
echo 🚀 Iniciando Trading Dashboard Completo...
echo.
echo 📋 Esto abrirá 2 ventanas:
echo   1️⃣  Backend API (Python FastAPI)
echo   2️⃣  Frontend App (React + Tailwind)
echo.
echo ⏱️  Espera unos segundos para que todo cargue...
echo.

echo 🔥 Iniciando Backend...
start "Trading Dashboard - Backend" cmd /c "start_backend.bat"

timeout /t 5 /nobreak >nul

echo 🎨 Iniciando Frontend...
start "Trading Dashboard - Frontend" cmd /c "start_frontend.bat"

echo.
echo ✅ Todo iniciado!
echo.
echo 🌐 Accede a tu dashboard en: http://localhost:3000
echo 📊 API documentación en: http://127.0.0.1:8000/docs
echo.
echo 💡 Tip: Espera a que ambas ventanas carguen completamente
echo.
pause