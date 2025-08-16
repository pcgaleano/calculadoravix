# Trading Dashboard - Guía de Instalación para Ubuntu Linux

Sistema profesional de análisis VIX_Fix para Ubuntu Linux.

## 📋 Requisitos Previos

### 1. Python 3.8+
```bash
sudo apt update
sudo apt install python3 python3-pip
python3 --version  # Verificar versión
```

### 2. Node.js 16+ y npm
```bash
# Opción 1: Desde repositorios Ubuntu
sudo apt install nodejs npm

# Opción 2: Usando NodeSource (recomendado para versión más reciente)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verificar instalación
node --version
npm --version
```

### 3. Git (si necesitas clonar el repositorio)
```bash
sudo apt install git
```

## 🚀 Instalación y Ejecución

### Método 1: Ejecución Automática (Recomendado)

1. **Dar permisos de ejecución a los scripts:**
   ```bash
   chmod +x start_all.sh start_backend.sh start_frontend.sh
   ```

2. **Ejecutar todo el sistema:**
   ```bash
   ./start_all.sh
   ```

### Método 2: Ejecución Manual

1. **Iniciar Backend (Terminal 1):**
   ```bash
   ./start_backend.sh
   ```

2. **Iniciar Frontend (Terminal 2):**
   ```bash
   ./start_frontend.sh
   ```

### Método 3: Ejecución Paso a Paso

#### Backend:
```bash
cd backend
pip3 install -r requirements.txt
python3 main.py
```

#### Frontend (nueva terminal):
```bash
cd frontend
npm install
npm start
```

## 🌐 Acceso a la Aplicación

Una vez iniciado el sistema:

- **🎨 Frontend (Interfaz Web):** http://localhost:3000
- **🔧 Backend API:** http://127.0.0.1:8000
- **📚 Documentación API:** http://127.0.0.1:8000/docs

## 🛠️ Comandos Útiles

### Detener los servicios:
```bash
# Si usaste start_all.sh, presiona Ctrl+C en esa terminal

# Para matar procesos manualmente:
pkill -f "python3 main.py"
pkill -f "npm start"
```

### Verificar que los puertos estén libres:
```bash
sudo netstat -tlnp | grep :3000  # Frontend
sudo netstat -tlnp | grep :8000  # Backend
```

### Actualizar dependencias:
```bash
# Backend
cd backend && pip3 install -r requirements.txt --upgrade

# Frontend
cd frontend && npm update
```

## 🐛 Solución de Problemas Comunes

### Error: "Permission denied"
```bash
chmod +x *.sh
```

### Error: "python3: command not found"
```bash
sudo apt install python3 python3-pip
```

### Error: "npm: command not found"
```bash
sudo apt install nodejs npm
```

### Error: Puerto en uso
```bash
# Encontrar y matar el proceso
sudo lsof -ti:3000 | xargs kill -9  # Frontend
sudo lsof -ti:8000 | xargs kill -9  # Backend
```

### Error: Dependencias faltantes de Python
```bash
cd backend
pip3 install --user -r requirements.txt
```

### Error: Permisos de npm
```bash
# Configurar npm para no requerir sudo
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

## 📦 Estructura del Proyecto

```
inversorcortoplazo/
├── backend/
│   ├── main.py              # Servidor FastAPI
│   ├── requirements.txt     # Dependencias Python
│   └── ...
├── frontend/
│   ├── src/                # Código React
│   ├── package.json        # Dependencias Node.js
│   └── ...
├── start_all.sh           # Script principal Linux
├── start_backend.sh       # Script backend Linux
├── start_frontend.sh      # Script frontend Linux
└── README_LINUX.md        # Esta guía
```

## 🔧 Configuración Avanzada

### Variables de Entorno (Opcional)

Crear archivo `.env` en la raíz:
```bash
# Backend
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000

# Frontend
REACT_APP_API_URL=http://127.0.0.1:8000
```

### Ejecución en Diferentes Puertos

Si necesitas cambiar puertos:

```bash
# Backend en puerto 8080
cd backend
uvicorn main:app --host 127.0.0.1 --port 8080

# Frontend en puerto 3001
cd frontend
PORT=3001 npm start
```

## 📈 Características del Sistema

- ✅ **API FastAPI**: Backend robusto para análisis financiero
- ✅ **React + TypeScript**: Frontend moderno y responsive
- ✅ **Análisis VIX_Fix**: Estrategia de trading avanzada
- ✅ **Dashboard en Tiempo Real**: Actualización automática
- ✅ **Multi-ticker**: Soporte para múltiples activos
- ✅ **Exportación de Datos**: Análisis completos

## 💡 Tips para Producción

### Usar PM2 para el Backend:
```bash
npm install -g pm2
cd backend
pm2 start "python3 main.py" --name trading-backend
pm2 startup
pm2 save
```

### Nginx como Proxy Reverso:
```bash
sudo apt install nginx
# Configurar /etc/nginx/sites-available/trading-dashboard
```

### Ejecutar en Background:
```bash
nohup ./start_all.sh > logs/app.log 2>&1 &
```

---

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs en la terminal
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que los puertos 3000 y 8000 estén libres
4. Revisa la sección de "Solución de Problemas"

¡Disfruta tu Trading Dashboard en Ubuntu! 🚀📈