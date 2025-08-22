"""
Constantes globales para el proyecto ApiDiff.
"""

# Configuración de reportes
DEFAULT_REPORTS_DIR = "reportes"
DEFAULT_DAYS_TO_KEEP = 7
MAX_DAYS_TO_KEEP = 30

# Configuración de API
DEFAULT_TIMEOUT = 90
MAX_RETRIES = 3
RETRY_DELAY = 1.5

# Configuración de archivos
PDF_FILE_EXTENSION = "*.pdf"

# Mensajes de log
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Nombres de archivos
DIFF_PDF_PREFIX = "diferencias"
TOTALS_PDF_PREFIX = "totales"
DETAILED_PDF_PREFIX = "detallado"
TEST_PDF_PREFIX = "test_diferencias"
