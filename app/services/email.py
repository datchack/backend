from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import (
    EMAIL_CONFIRMATION_EXPIRES_HOURS,
    EMAIL_CONFIRMATION_REQUIRED,
    EMAIL_FROM_ADDRESS,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PASSWORD,
    EMAIL_SMTP_PORT,
    EMAIL_SMTP_USER,
)


def is_email_confirmation_enabled() -> bool:
    return EMAIL_CONFIRMATION_REQUIRED and bool(EMAIL_SMTP_HOST and EMAIL_SMTP_PORT and EMAIL_FROM_ADDRESS)


def send_email(to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    if not is_email_confirmation_enabled():
        raise RuntimeError("Email confirmation is not configured")

    message = EmailMessage()
    message["From"] = EMAIL_FROM_ADDRESS
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        if EMAIL_SMTP_USER and EMAIL_SMTP_PASSWORD:
            smtp.login(EMAIL_SMTP_USER, EMAIL_SMTP_PASSWORD)
        smtp.send_message(message)


def send_confirmation_email(email: str, code: str) -> None:
    subject = "Confirmation de ton adresse email XAUTERMINAL"
    text_body = (
        f"Bonjour,\n\n"
        f"Merci de t'être inscrit sur XAUTERMINAL. Pour activer ton essai gratuit de 7 jours, saisis ce code de confirmation :\n\n"
        f"{code}\n\n"
        f"Si tu n'as pas demandé cette inscription, ignore simplement ce message.\n\n"
        f"L'équipe XAUTERMINAL"
    )
    html_body = (
        f"<p>Bonjour,</p>"
        f"<p>Merci de t'être inscrit sur <strong>XAUTERMINAL</strong>. Pour activer ton essai gratuit de 7 jours, saisis ce code de confirmation :</p>"
        f"<p><strong>{code}</strong></p>"
        f"<p>Si tu n'as pas demandé cette inscription, ignore simplement ce message.</p>"
        f"<p>L'équipe XAUTERMINAL</p>"
    )
    send_email(email, subject, text_body, html_body)
