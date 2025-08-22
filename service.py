"""
Servicios para obtener y procesar datos de depósitos bancarios.
"""

import re
import time
from datetime import datetime, timedelta, date
from typing import Dict, Iterable, List, Tuple

import requests
from zoneinfo import ZoneInfo

from constants import DEFAULT_TIMEOUT, MAX_RETRIES, RETRY_DELAY
from settings import settings


TZ = ZoneInfo(settings.TZ)
RE_NUM = re.compile(r"\b(\d{1,4})\b")


def previous_day_range(now: datetime) -> Tuple[str, str, str]:
    """
    Calcula el rango de fechas del día anterior.
    
    Args:
        now: Fecha y hora actual.
        
    Returns:
        Tupla con (fecha_inicio_iso, fecha_fin_iso, fecha_simple_iso).
    """
    yesterday = (now.astimezone(TZ) - timedelta(days=1)).date()
    start_time = datetime(
        yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=TZ
    ).isoformat()
    end_time = datetime(
        yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=TZ
    ).isoformat()
    return start_time, end_time, yesterday.isoformat()


def daterange_inclusive(start: date, end: date) -> Iterable[date]:
    """
    Genera fechas inclusivas entre start y end.
    
    Args:
        start: Fecha de inicio.
        end: Fecha de fin.
        
    Yields:
        Cada fecha en el rango.
    """
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def parse_reparto_from_user_name(user_name: str) -> str:
    """
    Extrae el número de reparto del nombre de usuario.
    
    Ejemplos:
        '119, RTO 119' -> '119'
        'RTO 072' -> '72'
        
    Args:
        user_name: Nombre del usuario.
        
    Returns:
        Número de reparto sin ceros a la izquierda, o cadena vacía si no se encuentra.
    """
    if not user_name:
        return ""
    
    match = RE_NUM.search(user_name)
    return match.group(1).lstrip("0") if match else ""


def fetch_deposits_by_day(date_iso: str) -> Dict:
    """
    Obtiene depósitos de un día específico desde la API externa.
    
    Args:
        date_iso: Fecha en formato YYYY-MM-DD.
        
    Returns:
        Respuesta JSON de la API.
        
    Raises:
        Exception: Si falla después de todos los reintentos.
    """
    url = f"{settings.EXTERNAL_APP_URL}/api/deposits/db/by-plant"
    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url, 
                params={"date": date_iso}, 
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:  # No esperar en el último intento
                time.sleep(RETRY_DELAY)
    
    raise last_exception
def flatten_deposits_payload(payload: Dict, date_iso: str) -> List[Dict]:
    """
    Convierte la estructura jerárquica de plantas/depósitos en una lista plana.
    
    Args:
        payload: Respuesta JSON de la API con estructura anidada.
        date_iso: Fecha en formato ISO para agregar a cada registro.
        
    Returns:
        Lista de diccionarios con información de depósitos normalizada.
    """
    deposits = []
    plants = (payload or {}).get("plants", {}) or {}
    
    for plant_key, plant_data in plants.items():
        plant_deposits = plant_data.get("deposits", []) or []
        
        for deposit in plant_deposits:
            deposits.append({
                "date": date_iso,
                "plant_key": plant_key,
                "plant_name": plant_data.get("name", ""),
                "deposit_id": deposit.get("deposit_id"),
                "identifier": deposit.get("identifier"),
                "user_name": deposit.get("user_name"),
                "reparto": parse_reparto_from_user_name(deposit.get("user_name", "")),
                "total_amount": deposit.get("total_amount", 0),
                "deposit_esperado": deposit.get("deposit_esperado", 0),
                "diferencia": deposit.get("diferencia", 0),
                "estado": deposit.get("estado", ""),
                "currency_code": deposit.get("currency_code", "ARS"),
                "deposit_type": deposit.get("deposit_type", ""),
                "date_time": deposit.get("date_time", ""),
                "pos_name": deposit.get("pos_name", ""),
                "st_name": deposit.get("st_name", ""),
                "tiene_diferencia": deposit.get("tiene_diferencia", False),
            })
    
    return deposits


def compute_shortages(rows: List[Dict], min_amount: int) -> List[Dict]:
    """
    Filtra registros que tienen faltantes significativos.
    
    Args:
        rows: Lista de registros de depósitos.
        min_amount: Monto mínimo absoluto para considerar significativo.
        
    Returns:
        Lista de registros con faltantes >= min_amount.
    """
    shortages = []
    
    for record in rows:
        expected = record.get("deposit_esperado", 0)
        actual = record.get("total_amount", 0)
        difference = actual - expected
        
        # Solo faltantes (diferencia negativa) con monto significativo
        if difference < 0 and abs(difference) >= min_amount:
            shortage_record = record.copy()
            shortage_record["diferencia"] = difference
            shortage_record["tipo"] = "faltante"
            shortages.append(shortage_record)
    
    return shortages


def compute_all_differences(rows: List[Dict]) -> List[Dict]:
    """
    Obtiene todos los registros con diferencias (faltantes y sobrantes).
    
    Args:
        rows: Lista de registros de depósitos.
        
    Returns:
        Lista de registros con cualquier diferencia != 0.
    """
    differences = []
    
    for record in rows:
        expected = record.get("deposit_esperado", 0)
        actual = record.get("total_amount", 0)
        difference = actual - expected
        
        if difference != 0:
            diff_record = record.copy()
            diff_record["diferencia"] = difference
            diff_record["tipo"] = "faltante" if difference < 0 else "sobrante"
            differences.append(diff_record)
    
    return differences


def fetch_shortages_range(start_date: str, end_date: str, min_amount: int) -> List[Dict]:
    """
    Obtiene faltantes significativos en un rango de fechas.
    
    Args:
        start_date: Fecha de inicio en formato YYYY-MM-DD.
        end_date: Fecha de fin en formato YYYY-MM-DD.
        min_amount: Monto mínimo para considerar significativo.
        
    Returns:
        Lista de todos los faltantes en el rango de fechas.
    """
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    all_shortages = []
    
    for current_date in daterange_inclusive(start, end):
        date_str = current_date.isoformat()
        
        try:
            payload = fetch_deposits_by_day(date_str)
            flat_data = flatten_deposits_payload(payload, date_str)
            daily_shortages = compute_shortages(flat_data, min_amount)
            all_shortages.extend(daily_shortages)
        except Exception as e:
            # Log error but continue with other dates
            print(f"Error procesando fecha {date_str}: {e}")
            continue
    
    return all_shortages


def fetch_all_differences_range(start_date: str, end_date: str) -> List[Dict]:
    """
    Obtiene todas las diferencias (faltantes y sobrantes) en un rango de fechas.
    
    Args:
        start_date: Fecha de inicio en formato YYYY-MM-DD.
        end_date: Fecha de fin en formato YYYY-MM-DD.
        
    Returns:
        Lista de todas las diferencias en el rango de fechas.
    """
    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    all_differences = []
    
    for current_date in daterange_inclusive(start, end):
        date_str = current_date.isoformat()
        
        try:
            payload = fetch_deposits_by_day(date_str)
            flat_data = flatten_deposits_payload(payload, date_str)
            daily_differences = compute_all_differences(flat_data)
            all_differences.extend(daily_differences)
        except Exception as e:
            # Log error but continue with other dates
            print(f"Error procesando fecha {date_str}: {e}")
            continue
    
    return all_differences


def summary_user_diff(rows: List[Dict]) -> List[Dict]:
    """
    Crea un resumen simplificado de las diferencias.
    
    Args:
        rows: Lista de registros con diferencias.
        
    Returns:
        Lista con resumen de fecha, reparto y diferencia.
    """
    return [
        {
            "date": record["date"], 
            "reparto": record.get("reparto"), 
            "diferencia": record.get("diferencia")
        }
        for record in rows
    ]


def download_pdf(endpoint: str, date_iso: str, output_path: str) -> None:
    """
    Descarga un PDF desde un endpoint externo.
    
    Args:
        endpoint: Endpoint relativo de la API (ej: "/api/reports/pdf/total").
        date_iso: Fecha en formato YYYY-MM-DD.
        output_path: Ruta donde guardar el archivo descargado.
        
    Raises:
        Exception: Si falla la descarga.
    """
    # Convertir fecha de YYYY-MM-DD a MM-DD-YYYY para el endpoint
    date_obj = datetime.fromisoformat(date_iso).date()
    formatted_date = date_obj.strftime("%m-%d-%Y")
    
    url = f"{settings.EXTERNAL_APP_URL}{endpoint}"
    params = {"date": formatted_date}
    
    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        with open(output_path, 'wb') as file:
            file.write(response.content)
            
    except Exception as e:
        print(f"Error descargando PDF de {url}: {e}")
        # Crear archivo vacío para evitar errores posteriores
        with open(output_path, 'wb') as file:
            file.write(b'')