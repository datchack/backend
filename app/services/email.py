from __future__ import annotations

import os
import resend

from app.config import EMAIL_CONFIRMATION_REQUIRED, EMAIL_FROM_ADDRESS

resend.api_key = os.getenv("re_i1pW2uyQ_CEdxGREP7eph5AeGGRAmvuuN")


def is_email_confirmation_enabled() -> bool:
    return EMAIL_CONFIRMATION_REQUIRED and bool(
        resend.api_key and EMAIL_FROM_ADDRESS
    )


def send_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    if not is_email_confirmation_enabled():
        print("EMAIL désactivé ou Resend mal configuré", flush=True)
        return

    try:
        print("Envoi email via Resend...", flush=True)

        resend.Emails.send({
            "from": EMAIL_FROM_ADDRESS,
            "to": [to_email],
            "subject": subject,
            "html": html_body if html_body else f"<pre>{text_body}</pre>",
            "text": text_body,
        })

        print("✅ Email envoyé via Resend", flush=True)

    except Exception as e:
        print("❌ ERREUR RESEND:", repr(e), flush=True)
        return


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