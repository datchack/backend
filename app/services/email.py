from __future__ import annotations

import os

try:
    import resend
except ImportError:  # pragma: no cover
    resend = None

from app.config import APP_BASE_URL, EMAIL_CONFIRMATION_REQUIRED, EMAIL_FROM_ADDRESS


RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
if resend is not None:
    resend.api_key = RESEND_API_KEY or None


def is_email_confirmation_enabled() -> bool:
    return EMAIL_CONFIRMATION_REQUIRED and bool(resend and resend.api_key and EMAIL_FROM_ADDRESS)


def send_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> None:
    if not EMAIL_CONFIRMATION_REQUIRED:
        return
    if resend is None or not resend.api_key or not EMAIL_FROM_ADDRESS:
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


def send_activation_reminder_email(email: str, code: str) -> None:
    subject = "Valide ton compte XAUTERMINAL et active ton essai de 7 jours"
    account_url = f"{APP_BASE_URL}/account"

    text_body = (
        "Bonjour,\n\n"
        "Ton compte XAUTERMINAL a bien ete cree, mais il reste une derniere etape "
        "avant de pouvoir choisir ta formule et demarrer ton essai de 7 jours.\n\n"
        f"Ton code de confirmation : {code}\n\n"
        f"Connecte-toi ici : {account_url}\n"
        "Saisis ce code, puis choisis ton abonnement Stripe pour activer l'acces au terminal.\n\n"
        "Si tu n'es pas a l'origine de cette inscription, tu peux ignorer cet email.\n\n"
        "L'equipe XAUTERMINAL"
    )

    html_body = (
        "<p>Bonjour,</p>"
        "<p>Ton compte <strong>XAUTERMINAL</strong> a bien été créé, mais il reste une dernière étape "
        "avant de pouvoir choisir ta formule et démarrer ton essai de 7 jours.</p>"
        "<p>Ton code de confirmation :</p>"
        f"<p style='font-size:24px;letter-spacing:4px'><strong>{code}</strong></p>"
        f"<p><a href='{account_url}' style='display:inline-block;padding:12px 18px;border-radius:6px;background:#00f0b5;color:#020508;text-decoration:none;font-weight:700'>Accéder à mon compte</a></p>"
        "<p>Connecte-toi, saisis ce code, puis choisis ton abonnement Stripe pour activer l'accès au terminal.</p>"
        "<p>Si tu n'es pas à l'origine de cette inscription, tu peux ignorer cet email.</p>"
        "<p>L'équipe XAUTERMINAL</p>"
    )

    send_email(email, subject, text_body, html_body)
