@echo off
echo 🚀 Iniciando Trading Dashboard Backend...
echo.

cd backend

echo 📦 Instalando dependencias...
pip install -r requirements.txt

echo.
echo 🔥 Iniciando servidor FastAPI...
echo 🌐 API disponible en: http://127.0.0.1:8000
echo 📊 Documentación API: http://127.0.0.1:8000/docs
echo.
echo ⭐ Para detener el servidor presiona Ctrl+C
echo.

python main.py