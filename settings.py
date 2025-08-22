from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    EXTERNAL_APP_URL: str = os.getenv("EXTERNAL_APP_URL", "")
    BASE_URL: str = os.getenv("BASE_URL", "")
    DIFF_ENDPOINT: str = os.getenv("DIFF_ENDPOINT", "/api/reports/differences")
    PDF_TOTALES_ENDPOINT: str = os.getenv("PDF_TOTALES_ENDPOINT", "/api/reports/pdf/total")
    PDF_DETALLADO_ENDPOINT: str = os.getenv("PDF_DETALLADO_ENDPOINT", "/api/reports/pdf/detailed")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    FROM_NAME: str = os.getenv("FROM_NAME", "Sistema")

    RH_EMAIL: str = os.getenv("RH_EMAIL", "")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")

    TZ: str = os.getenv("TZ", "America/Argentina/Buenos_Aires")
    MIN_FALTANTE: int = int(os.getenv("MIN_FALTANTE", "10000"))

settings = Settings()