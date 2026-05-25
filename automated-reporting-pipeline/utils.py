"""
utils.py — Shared helpers: logging, email dispatch, formatting.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def send_email_report(label: str, attachment_path: Path):
    """
    Send the report PDF/Excel as an email attachment.
    Configure via environment variables:
        SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
        REPORT_FROM, REPORT_TO  (comma-separated for multiple recipients)
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    from_addr = os.getenv("REPORT_FROM", smtp_user)
    to_addrs  = os.getenv("REPORT_TO", "analyst@example.com").split(",")

    if not smtp_user or not smtp_pass:
        logging.getLogger(__name__).warning(
            "SMTP credentials not set — skipping email for %s report.", label
        )
        return

    msg = MIMEMultipart()
    msg["Subject"] = f"[Auto-Report] {label} Report — {attachment_path.stem}"
    msg["From"]    = from_addr
    msg["To"]      = ", ".join(to_addrs)
    msg.attach(MIMEText(f"Please find the automated {label} report attached.", "plain"))

    with open(attachment_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{attachment_path.name}"')
    msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, to_addrs, msg.as_string())


def fmt_currency(value: float) -> str:
    """Format a float as a readable currency string."""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:.2f}"
