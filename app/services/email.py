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


def branded_email_html(
    *,
    preheader: str,
    title: str,
    intro: str,
    code: str,
    cta_label: str,
    cta_url: str,
    note: str,
) -> str:
    logo_url = f"{APP_BASE_URL}/static/apple-icon-180x180.png"
    return f"""
<!doctype html>
<html>
<body style="margin:0;padding:0;background:#06080b;color:#f4f7fb;font-family:Inter,Arial,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;color:transparent;opacity:0;">{preheader}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#06080b;padding:28px 12px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#10151d;border:1px solid #222b38;border-radius:10px;overflow:hidden;">
                    <tr>
                        <td style="padding:28px 30px 18px;border-bottom:1px solid #222b38;">
                            <table role="presentation" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="vertical-align:middle;padding-right:12px;">
                                        <img src="{logo_url}" width="34" height="34" alt="XAUTERMINAL" style="display:block;border-radius:7px;">
                                    </td>
                                    <td style="vertical-align:middle;">
                                        <div style="font-size:16px;line-height:20px;font-weight:800;letter-spacing:.7px;color:#ffffff;">XAUTERMINAL</div>
                                        <div style="font-size:12px;line-height:18px;color:#8f9aad;">Macro trading terminal</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:30px;">
                            <div style="font-size:11px;line-height:16px;font-weight:800;letter-spacing:1.4px;color:#00f0b5;text-transform:uppercase;">Validation du compte</div>
                            <h1 style="margin:10px 0 14px;font-size:26px;line-height:32px;color:#ffffff;">{title}</h1>
                            <p style="margin:0 0 22px;font-size:15px;line-height:24px;color:#c8d0dd;">{intro}</p>

                            <div style="margin:24px 0;padding:20px;border:1px solid #273446;border-radius:8px;background:#0b1017;">
                                <div style="font-size:12px;line-height:16px;color:#8f9aad;text-transform:uppercase;letter-spacing:1.2px;font-weight:800;">Code de confirmation</div>
                                <div style="margin-top:10px;font-size:34px;line-height:40px;font-weight:900;letter-spacing:8px;color:#ffffff;font-family:'Courier New',monospace;">{code}</div>
                            </div>

                            <p style="margin:0 0 22px;font-size:14px;line-height:22px;color:#aab4c3;">Entre ce code sur XAUTERMINAL pour valider ton adresse email. Ensuite, tu pourras choisir ta formule Stripe et démarrer ton essai de 7 jours.</p>

                            <table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 24px;">
                                <tr>
                                    <td style="border-radius:6px;background:#00f0b5;">
                                        <a href="{cta_url}" style="display:inline-block;padding:13px 18px;color:#020508;text-decoration:none;font-size:13px;line-height:18px;font-weight:900;letter-spacing:.4px;text-transform:uppercase;">{cta_label}</a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin:0;font-size:13px;line-height:21px;color:#8f9aad;">{note}</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:18px 30px 26px;border-top:1px solid #222b38;color:#748095;font-size:12px;line-height:19px;">
                            <div>Site : <a href="{APP_BASE_URL}" style="color:#00f0b5;text-decoration:none;">{APP_BASE_URL}</a></div>
                            <div style="margin-top:6px;">XAUTERMINAL est un outil d'information et d'organisation de marché. Il ne fournit pas de conseil financier.</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
""".strip()


def branded_action_email_html(
    *,
    preheader: str,
    kicker: str,
    title: str,
    intro: str,
    cta_label: str,
    cta_url: str,
    note: str,
) -> str:
    logo_url = f"{APP_BASE_URL}/static/apple-icon-180x180.png"
    return f"""
<!doctype html>
<html>
<body style="margin:0;padding:0;background:#06080b;color:#f4f7fb;font-family:Inter,Arial,sans-serif;">
    <div style="display:none;max-height:0;overflow:hidden;color:transparent;opacity:0;">{preheader}</div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#06080b;padding:28px 12px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:620px;background:#10151d;border:1px solid #222b38;border-radius:10px;overflow:hidden;">
                    <tr>
                        <td style="padding:28px 30px 18px;border-bottom:1px solid #222b38;">
                            <table role="presentation" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="vertical-align:middle;padding-right:12px;">
                                        <img src="{logo_url}" width="34" height="34" alt="XAUTERMINAL" style="display:block;border-radius:7px;">
                                    </td>
                                    <td style="vertical-align:middle;">
                                        <div style="font-size:16px;line-height:20px;font-weight:800;letter-spacing:.7px;color:#ffffff;">XAUTERMINAL</div>
                                        <div style="font-size:12px;line-height:18px;color:#8f9aad;">Macro trading terminal</div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:30px;">
                            <div style="font-size:11px;line-height:16px;font-weight:800;letter-spacing:1.4px;color:#00f0b5;text-transform:uppercase;">{kicker}</div>
                            <h1 style="margin:10px 0 14px;font-size:26px;line-height:32px;color:#ffffff;">{title}</h1>
                            <p style="margin:0 0 24px;font-size:15px;line-height:24px;color:#c8d0dd;">{intro}</p>
                            <table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 24px;">
                                <tr>
                                    <td style="border-radius:6px;background:#00f0b5;">
                                        <a href="{cta_url}" style="display:inline-block;padding:13px 18px;color:#020508;text-decoration:none;font-size:13px;line-height:18px;font-weight:900;letter-spacing:.4px;text-transform:uppercase;">{cta_label}</a>
                                    </td>
                                </tr>
                            </table>
                            <p style="margin:0;font-size:13px;line-height:21px;color:#8f9aad;">{note}</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:18px 30px 26px;border-top:1px solid #222b38;color:#748095;font-size:12px;line-height:19px;">
                            <div>Site : <a href="{APP_BASE_URL}" style="color:#00f0b5;text-decoration:none;">{APP_BASE_URL}</a></div>
                            <div style="margin-top:6px;">XAUTERMINAL est un outil d'information et d'organisation de marché. Il ne fournit pas de conseil financier.</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
""".strip()


def send_confirmation_email(email: str, code: str) -> None:
    subject = "Confirmation de ton adresse email XAUTERMINAL"
    account_url = f"{APP_BASE_URL}/account"

    text_body = (
        f"Bonjour,\n\n"
        f"Merci de t'être inscrit sur XAUTERMINAL.\n\n"
        f"Ton code de confirmation : {code}\n\n"
        f"Connecte-toi ici : {account_url}\n"
        f"Valide ton email, puis choisis ta formule Stripe pour démarrer ton essai de 7 jours.\n\n"
        f"Si tu n'as pas demandé cette inscription, ignore ce message.\n\n"
        f"L'équipe XAUTERMINAL"
    )

    html_body = branded_email_html(
        preheader="Ton code de confirmation XAUTERMINAL est prêt.",
        title="Bienvenue sur XAUTERMINAL",
        intro="Merci de t'être inscrit. Il ne reste qu'une étape pour valider ton compte et préparer ton accès au terminal.",
        code=code,
        cta_label="Valider mon compte",
        cta_url=account_url,
        note="Si tu n'as pas demandé cette inscription, tu peux ignorer cet email en toute sécurité.",
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

    html_body = branded_email_html(
        preheader="Valide ton compte XAUTERMINAL pour démarrer ton essai.",
        title="Ton accès XAUTERMINAL t'attend",
        intro="Ton compte a bien été créé, mais il reste une dernière étape avant de pouvoir choisir ta formule et démarrer ton essai de 7 jours.",
        code=code,
        cta_label="Revenir sur XAUTERMINAL",
        cta_url=account_url,
        note="Si tu n'es pas à l'origine de cette inscription, tu peux ignorer cet email.",
    )

    send_email(email, subject, text_body, html_body)


def send_password_reset_email(email: str, token: str) -> None:
    subject = "Réinitialisation de ton mot de passe XAUTERMINAL"
    reset_url = f"{APP_BASE_URL}/reset-password?token={token}"

    text_body = (
        "Bonjour,\n\n"
        "Tu as demandé à réinitialiser ton mot de passe XAUTERMINAL.\n\n"
        f"Utilise ce lien pour choisir un nouveau mot de passe : {reset_url}\n\n"
        "Ce lien expire dans 1 heure. Si tu n'es pas à l'origine de cette demande, ignore cet email.\n\n"
        "L'équipe XAUTERMINAL"
    )

    html_body = branded_action_email_html(
        preheader="Lien de réinitialisation de ton mot de passe XAUTERMINAL.",
        kicker="Sécurité du compte",
        title="Réinitialise ton mot de passe",
        intro="Tu as demandé à changer le mot de passe de ton compte XAUTERMINAL. Ce lien est valable pendant 1 heure.",
        cta_label="Changer mon mot de passe",
        cta_url=reset_url,
        note="Si tu n'es pas à l'origine de cette demande, tu peux ignorer cet email. Ton mot de passe actuel restera inchangé.",
    )

    send_email(email, subject, text_body, html_body)
