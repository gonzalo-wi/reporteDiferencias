@echo off
REM Script de deployment para Windows
echo 🚀 Iniciando deployment de API-Diff...

REM Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no está instalado
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose no está instalado
    pause
    exit /b 1
)

REM Verificar .env
if not exist .env (
    echo ❌ Archivo .env no encontrado
    echo Crea el archivo .env basado en la configuración necesaria
    pause
    exit /b 1
)

REM Crear directorios
echo 📁 Creando directorios necesarios...
if not exist reportes mkdir reportes
if not exist images mkdir images
if not exist logs mkdir logs

REM Parar versión anterior
echo 🛑 Parando versión anterior...
docker-compose down

REM Construir nueva imagen
echo 🔨 Construyendo nueva imagen...
docker-compose build --no-cache

REM Iniciar servicios
echo ▶️ Iniciando servicios...
docker-compose up -d

REM Esperar a que esté listo
echo ⏳ Esperando a que el servicio esté listo...
timeout /t 10

REM Verificar salud
echo 🔍 Verificando salud del servicio...
curl -f http://localhost:8009/health >nul 2>&1
if errorlevel 1 (
    echo ❌ El servicio no responde correctamente
    echo Logs del contenedor:
    docker-compose logs api-diff
    pause
    exit /b 1
)

echo ✅ Deployment exitoso!
echo 📊 Servicio disponible en: http://localhost:8009
echo 📖 Documentación en: http://localhost:8009/docs
echo.
echo 🔧 Comandos útiles:
echo   - Ver logs: docker-compose logs -f api-diff
echo   - Parar: docker-compose down
echo   - Reiniciar: docker-compose restart
echo   - Estado: docker-compose ps
echo.
echo 🎉 Deployment completado!
pause
