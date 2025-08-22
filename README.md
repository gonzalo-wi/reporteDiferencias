# API Reportes de Diferencias

Sistema automático para generar y enviar reportes de diferencias en depósitos bancarios.

## 🚀 Características

- ✅ **Reportes automáticos** diarios a las 8:00 AM
- ✅ **Generación de PDFs** con diferencias de depósitos
- ✅ **Envío automático de emails** a RRHH y Administración
- ✅ **API REST** para consultar diferencias
- ✅ **Limpieza automática** de archivos antiguos
- ✅ **Documentación interactiva** con Swagger UI

## 📋 Requisitos

### Para Docker (Recomendado)
- Docker 20.10+
- Docker Compose 2.0+

### Para instalación directa
- Python 3.11+
- Linux/Windows Server
- Nginx (recomendado)

## 🐳 Deployment con Docker (Recomendado)

### 1. Preparar configuración
```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar configuración
nano .env
```

### 2. Ejecutar deployment
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh

# Windows
deploy.bat
```

### 3. Verificar instalación
- Servicio: http://192.168.0.250:8009/health
- Documentación: http://192.168.0.250:8009/docs

## 🖥️ Deployment en Servidor Linux

### 1. Instalación automática
```bash
# Ejecutar como root
sudo chmod +x install-linux.sh
sudo ./install-linux.sh
```

### 2. Configuración manual
```bash
# Ir al directorio de aplicación
cd /opt/api-diff

# Copiar código
git clone [tu-repositorio] .

# Configurar entorno
cp .env.example .env
nano .env

# Instalar dependencias
sudo -u api-diff .venv/bin/pip install -r requirements.txt

# Iniciar servicio
sudo systemctl start api-diff
```

## ⚙️ Configuración

### Variables de entorno principales (.env)
```bash
# API Externa
EXTERNAL_APP_URL=http://192.168.0.250:8001

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@empresa.com
SMTP_PASS=password-de-aplicacion

# Destinatarios
RH_EMAIL=rrhh@empresa.com
ADMIN_EMAIL=admin@empresa.com

# Regional
TZ=America/Argentina/Buenos_Aires
MIN_FALTANTE=10000
```

## 📖 API Endpoints

### Salud del servicio
```http
GET /health
```

### Obtener diferencias
```http
GET /api/differences?desde=2025-08-20&hasta=2025-08-22
```

### Resumen de diferencias
```http
GET /api/differences/summary?desde=2025-08-20&hasta=2025-08-22
```

### Ejecutar job manualmente
```http
POST /run-now
```

### Generar PDF de prueba
```http
POST /api/test-pdf
```

### Limpiar archivos antiguos
```http
POST /api/clean-reports?days_to_keep=7
```

## 🔧 Administración

### Con Docker
```bash
# Ver logs
docker-compose logs -f api-diff

# Reiniciar
docker-compose restart

# Parar
docker-compose down

# Estado
docker-compose ps
```

### Con systemd (Linux)
```bash
# Ver logs
sudo journalctl -u api-diff -f

# Reiniciar
sudo systemctl restart api-diff

# Estado
sudo systemctl status api-diff
```

## 📁 Estructura del proyecto

```
api-diff/
├── main.py              # Aplicación principal FastAPI
├── service.py           # Servicios de datos
├── pdf_diff.py          # Generación de PDFs
├── mailer.py            # Envío de emails
├── settings.py          # Configuración
├── constants.py         # Constantes
├── requirements.txt     # Dependencias Python
├── Dockerfile           # Imagen Docker
├── docker-compose.yml   # Orquestación Docker
├── deploy.sh           # Script de deployment Linux
├── deploy.bat          # Script de deployment Windows
├── install-linux.sh    # Instalación en servidor Linux
├── api-diff.service    # Servicio systemd
├── .env.example        # Configuración de ejemplo
└── reportes/           # Directorio de PDFs generados
```

## 🕐 Programación automática

El sistema está configurado para ejecutarse automáticamente todos los días a las **8:00 AM** (zona horaria configurada en `TZ`).

### Cambiar horario
Editar en `main.py`:
```python
scheduler.add_job(run_daily_job, CronTrigger(hour=8, minute=0))
```

## 📧 Emails automáticos

### RRHH
- **Contenido**: PDF con faltantes ≥ $10,000
- **Frecuencia**: Diaria
- **Archivo**: `diferencias_YYYY-MM-DD.pdf`

### Administración
- **Contenido**: PDFs de totales y detallado
- **Frecuencia**: Diaria
- **Archivos**: 
  - `totales_YYYY-MM-DD.pdf`
  - `detallado_YYYY-MM-DD.pdf`

## 🗑️ Limpieza automática

El sistema elimina automáticamente archivos PDF más antiguos que 7 días para evitar acumulación de espacio en disco.

## 🔍 Monitoreo

### Health Check
```bash
curl -f http://192.168.0.250:8009/health
```

### Logs en tiempo real
```bash
# Docker
docker-compose logs -f api-diff

# systemd
sudo journalctl -u api-diff -f
```

## 🛠️ Desarrollo

### Ejecutar localmente
```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
uvicorn main:app --reload --port 8009
```

### Documentación interactiva
http://192.168.0.250:8009/docs

## 🚨 Troubleshooting

### El servicio no inicia
1. Verificar configuración en `.env`
2. Revisar logs: `docker-compose logs api-diff`
3. Verificar conectividad a la API externa

### No se envían emails
1. Verificar credenciales SMTP
2. Revisar configuración de firewall
3. Verificar que el servidor SMTP permite conexiones

### Error de conexión a API externa
1. Verificar `EXTERNAL_APP_URL` en `.env`
2. Verificar conectividad de red
3. Revisar si el servidor externo está funcionando

## 📞 Soporte

Para reportar problemas o solicitar mejoras, contactar al equipo de desarrollo.

---

**Versión**: 1.0.0  
**Última actualización**: Agosto 2025
