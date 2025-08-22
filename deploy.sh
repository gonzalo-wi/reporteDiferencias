#!/bin/bash

# Script de deployment para producción
set -e

echo "🚀 Iniciando deployment de API-Diff..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Verificar que existe Docker
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose no está instalado"
    exit 1
fi

# Verificar que existe .env
if [ ! -f .env ]; then
    error "Archivo .env no encontrado"
    echo "Crea el archivo .env basado en .env.example"
    exit 1
fi

# Crear directorios necesarios
log "Creando directorios necesarios..."
mkdir -p reportes images logs

# Backup de la versión anterior (si existe)
if [ "$(docker ps -q -f name=api-diff-prod)" ]; then
    log "Creando backup de la versión anterior..."
    docker-compose down
fi

# Construir nueva imagen
log "Construyendo nueva imagen Docker..."
docker-compose build --no-cache

# Iniciar servicios
log "Iniciando servicios..."
docker-compose up -d

# Esperar a que el servicio esté listo
log "Esperando a que el servicio esté listo..."
sleep 10

# Verificar salud del servicio
log "Verificando salud del servicio..."
if curl -f http://localhost:8009/health &> /dev/null; then
    log "✅ Deployment exitoso! El servicio está corriendo en http://localhost:8009"
    log "📊 Documentación disponible en: http://localhost:8009/docs"
else
    error "❌ El servicio no responde correctamente"
    echo "Logs del contenedor:"
    docker-compose logs api-diff
    exit 1
fi

# Mostrar información útil
log "🔧 Comandos útiles:"
echo "  - Ver logs: docker-compose logs -f api-diff"
echo "  - Parar servicio: docker-compose down"
echo "  - Reiniciar: docker-compose restart"
echo "  - Estado: docker-compose ps"

log "🎉 Deployment completado!"
