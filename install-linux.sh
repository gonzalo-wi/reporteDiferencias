#!/bin/bash

# Script de instalación para servidor Linux (sin Docker)
set -e

echo "🚀 Instalando API-Diff en servidor Linux..."

# Variables
APP_DIR="/opt/api-diff"
APP_USER="api-diff"
PYTHON_VERSION="3.11"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    error "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# Actualizar sistema
log "Actualizando sistema..."
apt update && apt upgrade -y

# Instalar dependencias
log "Instalando dependencias..."
apt install -y python3.11 python3.11-venv python3-pip nginx curl git supervisor

# Crear usuario de aplicación
log "Creando usuario de aplicación..."
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir $APP_DIR --create-home $APP_USER
fi

# Crear directorio de aplicación
log "Preparando directorio de aplicación..."
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# Cambiar al usuario de aplicación para instalar
log "Instalando aplicación..."
sudo -u $APP_USER bash << EOF
cd $APP_DIR

# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate

# Copiar archivos de la aplicación aquí
# (esto se hace manualmente o via git clone)

# Instalar dependencias Python
pip install --upgrade pip
pip install uvicorn[standard] fastapi

# Crear directorios necesarios
mkdir -p reportes images logs
EOF

# Copiar archivo de servicio systemd
log "Configurando servicio systemd..."
cp api-diff.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable api-diff

# Configurar nginx (opcional)
log "Configurando nginx..."
cat > /etc/nginx/sites-available/api-diff << 'EOF'
server {
    listen 80;
    server_name tu-servidor.com;
    
    location / {
        proxy_pass http://127.0.0.1:8009;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Habilitar sitio nginx
ln -sf /etc/nginx/sites-available/api-diff /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

log "✅ Instalación completada!"
log "📋 Próximos pasos:"
echo "1. Copiar código de la aplicación a $APP_DIR"
echo "2. Configurar archivo .env en $APP_DIR"
echo "3. Instalar dependencias: sudo -u $APP_USER $APP_DIR/.venv/bin/pip install -r $APP_DIR/requirements.txt"
echo "4. Iniciar servicio: sudo systemctl start api-diff"
echo "5. Ver logs: sudo journalctl -u api-diff -f"

log "🔧 Comandos útiles:"
echo "  - Iniciar: sudo systemctl start api-diff"
echo "  - Parar: sudo systemctl stop api-diff"
echo "  - Reiniciar: sudo systemctl restart api-diff"
echo "  - Estado: sudo systemctl status api-diff"
echo "  - Logs: sudo journalctl -u api-diff -f"
