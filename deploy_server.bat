@echo off
echo 🚀 Iniciando deploy de CalculadoraVIX...

REM 1. Clonar repositorio
echo 📥 Clonando repositorio...
git clone https://github.com/pcgaleano/calculadoravix.git
cd calculadoravix

REM 2. Configurar entorno Python
echo 🐍 Configurando entorno Python...
python -m venv venv
call venv\Scripts\activate

REM 3. Instalar dependencias
echo 📦 Instalando dependencias...
cd backend
pip install -r requirements.txt

REM 4. Iniciar servidor
echo 🔥 Iniciando servidor...
start "CalculadoraVIX Server" python main.py

REM 5. Esperar que inicie
echo ⏳ Esperando que el servidor inicie...
timeout /t 15 /nobreak

REM 6. Ejecutar carga inicial
echo 📊 Ejecutando carga inicial de datos...
curl -X POST "http://127.0.0.1:8000/initial-data-load"

echo ✅ Deploy completado!
echo 🌐 Servidor disponible en: http://localhost:8000
echo 📋 API docs en: http://localhost:8000/docs

pause