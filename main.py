"""
API FastAPI para generar y enviar reportes automáticos de diferencias en depósitos.

Este servicio:
1. Programa jobs automáticos para generar reportes diarios
2. Proporciona endpoints para obtener diferencias en depósitos
3. Genera PDFs con reportes de faltantes y sobrantes
4. Envía emails automáticos a RRHH y Administración
5. Gestiona la limpieza automática de archivos antiguos
"""

import glob
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from constants import (
    DEFAULT_DAYS_TO_KEEP, 
    DEFAULT_REPORTS_DIR, 
    LOG_FORMAT,
    MAX_DAYS_TO_KEEP,
    PDF_FILE_EXTENSION,
    TEST_PDF_PREFIX,
    DIFF_PDF_PREFIX,
    TOTALS_PDF_PREFIX,
    DETAILED_PDF_PREFIX
)
from mailer import send_email
from pdf_diff import build_diffs_pdf
from service import (
    TZ,
    download_pdf,
    fetch_all_differences_range,
    fetch_shortages_range,
    previous_day_range,
    summary_user_diff,
)
from settings import settings

# Configuración de logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Configuración de la aplicación
app = FastAPI(
    title="API Reportes de Depósitos",
    description="Sistema automático para generar y enviar reportes de diferencias en depósitos bancarios",
    version="1.0.0"
)

# Asegurar que existe el directorio de reportes
os.makedirs(DEFAULT_REPORTS_DIR, exist_ok=True)


def clean_old_reports(directory: str = DEFAULT_REPORTS_DIR, days_to_keep: int = DEFAULT_DAYS_TO_KEEP) -> dict:
    """
    Elimina archivos de reportes más antiguos que el número especificado de días.
    
    Args:
        directory: Directorio donde buscar archivos.
        days_to_keep: Número de días de archivos a mantener.
        
    Returns:
        Dict con información sobre la limpieza realizada.
    """
    try:
        if not os.path.exists(directory):
            logger.warning(f"Directorio {directory} no existe")
            return {"files_deleted": 0, "error": f"Directorio {directory} no existe"}
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        files_deleted = 0
        errors = []
        
        # Buscar todos los archivos PDF en el directorio
        pdf_files = glob.glob(os.path.join(directory, PDF_FILE_EXTENSION))
        
        for file_path in pdf_files:
            try:
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mod_time < cutoff_date:
                    os.remove(file_path)
                    files_deleted += 1
                    logger.info(f"Archivo eliminado: {os.path.basename(file_path)}")
                    
            except Exception as e:
                error_msg = f"No se pudo eliminar {file_path}: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)
        
        if files_deleted > 0:
            logger.info(f"Limpieza completada: {files_deleted} archivos eliminados")
        else:
            logger.info(f"No se encontraron archivos más antiguos que {days_to_keep} días")
            
        return {
            "files_deleted": files_deleted,
            "days_kept": days_to_keep,
            "errors": errors
        }
            
    except Exception as e:
        error_msg = f"Error durante la limpieza de archivos: {e}"
        logger.error(error_msg)
        return {"files_deleted": 0, "error": error_msg}


def run_daily_job(now: Optional[datetime] = None) -> dict:
    """
    Ejecuta el job diario para generar y enviar reportes.
    
    Este job:
    1. Limpia archivos antiguos
    2. Obtiene datos de diferencias del día anterior
    3. Genera PDF de diferencias
    4. Descarga PDFs externos (totales y detallado)
    5. Envía emails a RRHH y Administración
    
    Args:
        now: Fecha y hora actual (opcional, para testing).
        
    Returns:
        Dict con el resultado de la operación.
    """
    try:
        current_time = now or datetime.now(tz=TZ)
        start_date, end_date, report_date = previous_day_range(current_time)
        
        logger.info(f"=== INICIANDO JOB DIARIO PARA {report_date} ===")
        logger.info(f"Rango de datos: {start_date} -> {end_date}")

        # Paso 1: Limpiar archivos antiguos
        cleanup_result = clean_old_reports(DEFAULT_REPORTS_DIR, DEFAULT_DAYS_TO_KEEP)
        logger.info(f"Limpieza: {cleanup_result['files_deleted']} archivos eliminados")

        # Paso 2: Obtener diferencias significativas
        differences = fetch_shortages_range(start_date, end_date, settings.MIN_FALTANTE)
        logger.info(f"Encontradas {len(differences)} diferencias >= ${settings.MIN_FALTANTE:,}")

        # Paso 3: Generar PDF de diferencias
        diff_pdf_path = os.path.join(DEFAULT_REPORTS_DIR, f"{DIFF_PDF_PREFIX}_{report_date}.pdf")
        build_diffs_pdf(diff_pdf_path, report_date, differences)
        logger.info(f"PDF de diferencias generado: {diff_pdf_path}")

        # Paso 4: Descargar PDFs externos
        totals_pdf_path = os.path.join(DEFAULT_REPORTS_DIR, f"{TOTALS_PDF_PREFIX}_{report_date}.pdf")
        detailed_pdf_path = os.path.join(DEFAULT_REPORTS_DIR, f"{DETAILED_PDF_PREFIX}_{report_date}.pdf")
        
        logger.info("Descargando PDFs externos...")
        download_pdf(settings.PDF_TOTALES_ENDPOINT, report_date, totals_pdf_path)
        download_pdf(settings.PDF_DETALLADO_ENDPOINT, report_date, detailed_pdf_path)
        logger.info("PDFs externos descargados")

        # Paso 5: Enviar emails
        logger.info("Enviando emails...")
        
        # Email a RRHH (solo diferencias)
        send_email(
            subject=f"[RTO] Diferencias (≥ ${settings.MIN_FALTANTE:,}) - {report_date}".replace(",", "."),
            body_html=f"""
                <p>Buen día,</p>
                <p>Adjunto reporte de <b>faltantes</b> del {report_date} (≥ ${settings.MIN_FALTANTE:,}).</p>
                <p>Total de faltantes: <b>{len(differences)}</b></p>
                <p>Saludos,<br>{settings.FROM_NAME}</p>
            """,
            to=[settings.RH_EMAIL],
            attachments=[diff_pdf_path]
        )
        logger.info(f"Email enviado a RRHH: {settings.RH_EMAIL}")

        # Email a Administración (totales y detallado)
        send_email(
            subject=f"[RTO] Depósitos Totales y Detallado - {report_date}",
            body_html=f"""
                <p>Buen día,</p>
                <p>Adjunto reportes de depósitos del {report_date}:</p>
                <ul>
                  <li><b>{TOTALS_PDF_PREFIX}_{report_date}.pdf</b>: resumen por planta</li>
                  <li><b>{DETAILED_PDF_PREFIX}_{report_date}.pdf</b>: detalle completo</li>
                </ul>
                <p>Saludos,<br>{settings.FROM_NAME}</p>
            """,
            to=[settings.ADMIN_EMAIL],
            attachments=[totals_pdf_path, detailed_pdf_path]
        )
        logger.info(f"Email enviado a Administración: {settings.ADMIN_EMAIL}")

        logger.info("=== JOB DIARIO COMPLETADO EXITOSAMENTE ===")
        return {
            "status": "ok",
            "date": report_date,
            "differences_count": len(differences),
            "files_cleaned": cleanup_result['files_deleted'],
            "attachments": [diff_pdf_path, totals_pdf_path, detailed_pdf_path]
        }
        
    except Exception as e:
        logger.exception("=== ERROR EN JOB DIARIO ===")
        return {"status": "error", "message": str(e)}


# ───────────────────────────── Scheduler 14:06 ARG (para pruebas) ───────────────────────────
scheduler = BackgroundScheduler(timezone=settings.TZ)
scheduler.add_job(run_daily_job, CronTrigger(hour=14, minute=12))
scheduler.start()


# ───────────────────────────── Endpoints HTTP ────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "tz": settings.TZ}


@app.post("/run-now")
def run_now():
    res = run_daily_job()
    if res.get("status") == "ok":
        return JSONResponse(res, status_code=200)
    return JSONResponse(res, status_code=500)


@app.post("/api/test-pdf")
def test_pdf_generation():
    """
    Endpoint para probar solo la generación del PDF de diferencias
    """
    try:
        now = datetime.now(TZ)
        desde, hasta, fecha_iso = previous_day_range(now)
        
        logging.info(f"Probando generación PDF para fecha: {fecha_iso}")
        
        # Obtener diferencias
        diffs = fetch_shortages_range(desde, hasta, settings.MIN_FALTANTE)
        logging.info(f"Encontrados {len(diffs)} faltantes >= ${settings.MIN_FALTANTE:,}")
        
        # Crear directorio si no existe
        OUT_DIR = "reportes"
        os.makedirs(OUT_DIR, exist_ok=True)
        
        # Generar PDF
        diffs_pdf_path = os.path.join(OUT_DIR, f"test_diferencias_{fecha_iso}.pdf")
        build_diffs_pdf(diffs_pdf_path, fecha_iso, diffs)
        
        return {
            "status": "ok",
            "fecha": fecha_iso,
            "total_diferencias": len(diffs),
            "pdf_path": diffs_pdf_path,
            "muestra_datos": diffs[:3] if len(diffs) > 0 else []  # Primeros 3 registros para ver estructura
        }
        
    except Exception as e:
        logging.exception("Error generando PDF de prueba")
        return {"status": "error", "message": str(e)}


@app.post("/api/clean-reports")
def clean_reports_endpoint(days_to_keep: Optional[int] = Query(7, ge=1, le=30, description="Días de reportes a mantener")):
    """
    Limpia archivos de reportes más antiguos que el número especificado de días.
    Por defecto mantiene los últimos 7 días.
    """
    try:
        clean_old_reports("reportes", days_to_keep)
        return {
            "status": "ok",
            "message": f"Limpieza completada. Archivos más antiguos que {days_to_keep} días han sido eliminados.",
            "days_kept": days_to_keep
        }
    except Exception as e:
        logging.exception("Error durante la limpieza manual")
        return {"status": "error", "message": str(e)}


@app.get("/api/differences")
def api_differences(
    desde: str = Query(..., description="YYYY-MM-DD"),
    hasta: str = Query(..., description="YYYY-MM-DD")
):
    """
    Devuelve TODAS las diferencias (faltantes Y sobrantes) entre fechas, día por día, aplanado.
    Muestra tanto diferencias positivas (sobrantes) como negativas (faltantes).
    """
    try:
        logging.info(f"Obteniendo diferencias desde {desde} hasta {hasta}")
        rows = fetch_all_differences_range(desde, hasta)
        logging.info(f"Se encontraron {len(rows)} diferencias")
        
        # Estadísticas para el resumen
        faltantes = [r for r in rows if r.get("tipo") == "faltante"]
        sobrantes = [r for r in rows if r.get("tipo") == "sobrante"]
        total_faltante = sum(abs(r.get("diferencia", 0)) for r in faltantes)
        total_sobrante = sum(r.get("diferencia", 0) for r in sobrantes)
        
        return {
            "status": "ok", 
            "desde": desde, 
            "hasta": hasta,
            "estadisticas": {
                "total_diferencias": len(rows),
                "total_faltantes": len(faltantes),
                "total_sobrantes": len(sobrantes),
                "monto_faltante": total_faltante,
                "monto_sobrante": total_sobrante
            },
            "items": rows
        }
    except Exception as e:
        logging.exception(f"Error en api_differences: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/differences/summary")
def api_differences_summary(
    desde: str = Query(..., description="YYYY-MM-DD"),
    hasta: str = Query(..., description="YYYY-MM-DD")
):
    """
    Devuelve resumen de TODAS las diferencias: (date, reparto, diferencia, tipo).
    Incluye tanto faltantes como sobrantes.
    """
    rows = fetch_all_differences_range(desde, hasta)
    brief = [
        {
            "date": r["date"], 
            "reparto": r.get("reparto"), 
            "diferencia": r.get("diferencia"),
            "tipo": r.get("tipo"),
            "user_name": r.get("user_name")
        }
        for r in rows
    ]
    
    # Estadísticas para el resumen
    faltantes = [r for r in brief if r.get("tipo") == "faltante"]
    sobrantes = [r for r in brief if r.get("tipo") == "sobrante"]
    
    return {
        "status": "ok", 
        "desde": desde, 
        "hasta": hasta,
        "estadisticas": {
            "total_diferencias": len(brief),
            "total_faltantes": len(faltantes),
            "total_sobrantes": len(sobrantes)
        },
        "items": brief
    }

