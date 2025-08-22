import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formataddr
from email.mime.text import MIMEText
from email import encoders
from typing import List, Optional
from settings import settings

def send_email(subject: str, body_html: str, to: List[str], attachments: Optional[List[str]] = None):
    msg = MIMEMultipart()
    msg["From"] = formataddr((settings.FROM_NAME, settings.FROM_EMAIL))
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject

    msg.attach(MIMEText(body_html, "html", "utf-8"))

    for path in attachments or []:
        part = MIMEBase("application", "octet-stream")
        with open(path, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{path.split("/")[-1]}"')
        msg.attach(part)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.sendmail(settings.FROM_EMAIL, to, msg.as_string())