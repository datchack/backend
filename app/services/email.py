from __future__ import annotations

import os

import resend

from app.config import EMAIL_CONFIRMATION_REQUIRED, EMAIL_FROM_ADDRESS


RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
resend.api_key = RESEND_API_KEY or None


def is_email_confirmation_enabled() -> bool:
    return EMAIL_CONFIRMATION_REQUIRED and bool(resend.api_key and EMAIL_FROM_ADDRESS)


def send_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    if not EMAIL_CONFIRMATION_REQUIRED:
        return
    if not resend.api_key or not EMAIL_FROM_ADDRESS:
        raise RuntimeError(
            "Email confirmation is enabled but RESEND_API_KEY or EMAIL_FROM_ADDRESS is missing."
        )

    print("Envoi email via Resend...", flush=True)
    resend.Emails.send(
        {
            "from": EMAIL_FROM_ADDRESS,
            "to": [to_email],
            "subject": subject,
            "html": html_body if html_body else f"<pre>{text_body}</pre>",
            "text": text_body,
        }
    )
    print("✅ Email envoyé via Resend", flush=True)


def send_confirmation_email(email: str, code: str) -> None:
    subject = "Confirmation de ton adresse email XAUTERMINAL"

    text_body = (
        f"Bonjour,\n\n"
        f"Merci de t'être inscrit sur XAUTERMINAL.\n\n"
        f"Ton code de confirmation :\n\n"
        f"{code}\n\n"
        f"Si tu n'as pas demandé cette inscription, ignore ce message.\n\n"
        f"L'équipe XAUTERMINAL"
    )

    html_body = (
        f"<p>Bonjour,</p>"
        f"<p>Merci de t'être inscrit sur <strong>XAUTERMINAL</strong>.</p>"
        f"<p>Ton code de confirmation :</p>"
        f"<p style='font-size:20px'><strong>{code}</strong></p>"
        f"<p>Si tu n'as pas demandé cette inscription, ignore ce message.</p>"
        f"<p>L'équipe XAUTERMINAL</p>"
    )

    send_email(email, subject, text_body, html_body)
