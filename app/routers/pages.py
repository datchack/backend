from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response as FastAPIResponse

from app.core import *

router = APIRouter()

LEGAL_PAGE_META = {
    "terms_title": {
        "title": "Conditions générales d'utilisation",
        "kicker": "CGU",
        "description": "Conditions générales d'utilisation de XAUTERMINAL, accès au service, abonnements, paiement et responsabilités.",
    },
    "privacy_title": {
        "title": "Politique de confidentialité",
        "kicker": "CONFIDENTIALITÉ",
        "description": "Politique de confidentialité de XAUTERMINAL concernant les données de compte, sessions, paiements et prestataires.",
    },
    "risk_title": {
        "title": "Disclaimer trading et risques",
        "kicker": "RISQUES",
        "description": "Avertissement sur les risques liés au trading, aux données de marché et à l'utilisation des outils XAUTERMINAL.",
    },
}


def legal_page(title_key: str, kicker_key: str, sections: list[tuple[str, str]]) -> str:
    meta = LEGAL_PAGE_META[title_key]
    business_name = LEGAL_BUSINESS_NAME
    email = LEGAL_CONTACT_EMAIL
    updated = utc_now().date().strftime("%d/%m/%Y")
    section_html = "\n".join(
        f'<section><h2 data-i18n="{section_title_key}">{section_title_key}</h2><p data-i18n="{section_content_key}">{section_content_key}</p></section>'
        for section_title_key, section_content_key in sections
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="{title_key}">{meta["title"]} - {business_name}</title>
    <meta name="description" content="{meta["description"]}">
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="{business_name}">
            <span class="brand-mark"></span>
            <span>{business_name}</span>
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page">
        <div class="landing-kicker" data-i18n="{kicker_key}">{meta["kicker"]}</div>
        <h1 data-i18n="{title_key}">{meta["title"]}</h1>
        <p class="legal-updated"><span data-i18n="legal_updated">Dernière mise à jour :</span> {updated}</p>
        <section>
            <h2 data-i18n="legal_general">Informations générales</h2>
            <p>
                <span data-i18n="legal_editor">Éditeur</span> : {LEGAL_PUBLISHER_NAME}<br>
                <span data-i18n="legal_business">Entreprise</span> : {business_name}<br>
                <span data-i18n="legal_id">Identifiant</span> : {LEGAL_BUSINESS_ID}<br>
                <span data-i18n="legal_contact">Contact</span> : <a href="mailto:{email}">{email}</a><br>
                <span data-i18n="legal_address">Adresse</span> : {LEGAL_BUSINESS_ADDRESS}<br>
                <span data-i18n="legal_hosting">Hébergement</span> : {LEGAL_HOSTING_PROVIDER}
            </p>
        </section>
        {section_html}
        <section class="legal-contact">
            <h2 data-i18n="legal_contact_title">Contact</h2>
            <p><span data-i18n="legal_contact_copy">Pour toute question relative aux conditions d'utilisation, à la confidentialité ou aux risques liés au trading, vous pouvez nous contacter à</span> <a href="mailto:{email}">{email}</a>.</p>
        </section>
    </main>
    <footer class="landing-footer">
        <div>
            <strong>{business_name}</strong>
            <span>Terminal macro et trading professionnel.</span>
        </div>
        <nav aria-label="Documents légaux">
            <a href="/terms">CGU</a>
            <a href="/privacy">Confidentialité</a>
            <a href="/risk-disclaimer">Disclaimer trading</a>
        </nav>
    </footer>
    <script src="/static/landing.js"></script>
</body>
</html>"""


@router.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/landing.html")


@router.get("/terminal", response_class=HTMLResponse)
async def terminal():
    return FileResponse("templates/index.html")


@router.get("/terms", response_class=HTMLResponse)
async def terms_page():
    return HTMLResponse(legal_page("terms_title", "terms_kicker", [
        ("terms_section1_title", "terms_section1"),
        ("terms_section2_title", "terms_section2"),
        ("terms_section3_title", "terms_section3"),
        ("terms_section4_title", "terms_section4"),
        ("terms_section5_title", "terms_section5"),
        ("terms_section6_title", "terms_section6"),
        ("terms_section7_title", "terms_section7"),
        ("terms_section8_title", "terms_section8"),
    ]))


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    return HTMLResponse(legal_page("privacy_title", "privacy_kicker", [
        ("privacy_section1_title", "privacy_section1"),
        ("privacy_section2_title", "privacy_section2"),
        ("privacy_section3_title", "privacy_section3"),
        ("privacy_section4_title", "privacy_section4"),
        ("privacy_section5_title", "privacy_section5"),
        ("privacy_section6_title", "privacy_section6"),
        ("privacy_section7_title", "privacy_section7"),
        ("privacy_section8_title", "privacy_section8"),
    ]))


@router.get("/risk-disclaimer", response_class=HTMLResponse)
async def risk_disclaimer_page():
    return HTMLResponse(legal_page("risk_title", "risk_kicker", [
        ("risk_section1_title", "risk_section1"),
        ("risk_section2_title", "risk_section2"),
        ("risk_section3_title", "risk_section3"),
        ("risk_section4_title", "risk_section4"),
        ("risk_section5_title", "risk_section5"),
        ("risk_section6_title", "risk_section6"),
    ]))


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    return """User-agent: *
Allow: /

Sitemap: https://xauterminal.com/sitemap.xml
"""


@router.get("/sitemap.xml")
async def sitemap_xml():
    today = utc_now().date().isoformat()
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://xauterminal.com/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://xauterminal.com/terminal</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://xauterminal.com/terms</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://xauterminal.com/privacy</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>https://xauterminal.com/risk-disclaimer</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
"""
    return FastAPIResponse(content=xml, media_type="application/xml")


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    require_owner(request)
    return FileResponse("templates/admin.html")


@router.get("/db-test")
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()

        return {"database": "ok", "result": result[0]}
    except Exception as e:
        return {"database": "error", "message": str(e)}
