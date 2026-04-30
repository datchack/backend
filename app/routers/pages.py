from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response as FastAPIResponse
from fastapi.templating import Jinja2Templates

from app.core import *

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def legal_context(title: str, kicker: str, sections: list[tuple[str, str]]) -> dict:
    return {
        "title": title,
        "kicker": kicker,
        "sections": sections,
        "business_name": LEGAL_BUSINESS_NAME,
        "publisher": LEGAL_PUBLISHER_NAME,
        "email": LEGAL_CONTACT_EMAIL,
        "address": LEGAL_BUSINESS_ADDRESS,
        "business_id": LEGAL_BUSINESS_ID,
        "host": LEGAL_HOSTING_PROVIDER,
        "updated": utc_now().date().strftime("%d/%m/%Y"),
    }


@router.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("templates/landing.html")


@router.get("/terminal", response_class=HTMLResponse)
async def terminal():
    return FileResponse("templates/index.html")


@router.get("/terms")
async def terms_page(request: Request):
    context = legal_context("Conditions générales d'utilisation", "CGU", [
        ("Objet du service", "XAUTERMINAL propose un terminal web d'information macro et marché permettant de consulter des news, un calendrier économique, des graphiques, des watchlists, des widgets de prix et des outils de lecture de contexte. Le service est fourni comme outil d'aide à l'organisation et à l'analyse personnelle."),
        ("Accès au service", "L'accès complet peut être soumis à la création d'un compte, à une période d'essai, à un abonnement ou à une offre lifetime. L'utilisateur s'engage à fournir des informations exactes et à préserver la confidentialité de ses identifiants."),
        ("Essai gratuit et abonnements", "Les formules mensuelle et annuelle peuvent inclure un essai gratuit de 7 jours. Selon la configuration Stripe, une carte bancaire peut être demandée au démarrage de l'essai afin de préparer le renouvellement. À l'issue de l'essai, l'abonnement choisi peut démarrer automatiquement si le paiement est validé. L'offre lifetime correspond à un paiement unique donnant accès au service tant que celui-ci est exploité."),
        ("Paiement", "Les paiements sont traités par Stripe. XAUTERMINAL ne stocke pas les numéros de carte bancaire. Les factures, moyens de paiement, renouvellements et éventuels échecs de paiement sont gérés via Stripe et les systèmes associés."),
        ("Utilisation acceptable", "L'utilisateur s'engage à ne pas perturber le service, contourner les restrictions d'accès, partager un compte de manière abusive, extraire massivement les données ou utiliser le service à des fins illicites."),
        ("Disponibilité", "Le service dépend de fournisseurs tiers, notamment hébergement, données de marché, flux d'actualité, calendrier économique, graphiques et paiement. Des interruptions, retards, erreurs ou indisponibilités peuvent survenir."),
        ("Responsabilité", "XAUTERMINAL ne garantit pas l'exactitude, l'exhaustivité, l'actualité ou la continuité des données affichées. L'utilisateur reste seul responsable de ses décisions, notamment financières, et de sa gestion du risque."),
        ("Modification du service", "Les fonctionnalités, tarifs, offres, sources de données et conditions peuvent évoluer afin d'améliorer le produit, corriger des erreurs ou tenir compte de contraintes techniques ou commerciales."),
    ])
    return templates.TemplateResponse("legal.html", {"request": request, **context})


@router.get("/privacy")
async def privacy_page(request: Request):
    context = legal_context("Politique de confidentialité", "CONFIDENTIALITÉ", [
        ("Données collectées", "XAUTERMINAL peut collecter l'adresse email, le mot de passe chiffré, les préférences de terminal, l'état d'abonnement, les identifiants Stripe nécessaires au suivi du paiement et des données techniques liées à l'utilisation du service."),
        ("Finalités", "Ces données servent à créer et sécuriser le compte, gérer l'accès au terminal, synchroniser les préférences, traiter les abonnements, améliorer le produit et assurer le support utilisateur."),
        ("Paiements", "Les données de paiement sont traitées par Stripe. XAUTERMINAL conserve uniquement les références techniques utiles au suivi du compte, comme l'identifiant client, l'abonnement, le prix sélectionné ou le statut de paiement."),
        ("Cookies et sessions", "Le service utilise un cookie de session afin de maintenir la connexion au compte. Des préférences peuvent également être conservées localement dans le navigateur pour personnaliser l'expérience."),
        ("Prestataires", "Le service peut s'appuyer sur des prestataires techniques comme Render pour l'hébergement, Stripe pour le paiement, Financial Modeling Prep, Yahoo Finance, TradingView ou des flux RSS tiers pour les données et l'affichage."),
        ("Durée de conservation", "Les données de compte sont conservées tant que le compte existe ou tant que cela est nécessaire pour fournir le service, respecter des obligations légales, gérer un litige ou assurer la sécurité."),
        ("Droits utilisateur", "L'utilisateur peut demander l'accès, la correction ou la suppression de ses données en contactant l'adresse indiquée sur cette page. Certaines données peuvent être conservées si une obligation légale ou technique l'impose."),
        ("Sécurité", "XAUTERMINAL applique des mesures raisonnables pour protéger les comptes et les données. Aucun système n'étant infaillible, l'utilisateur doit choisir un mot de passe robuste et éviter de le réutiliser."),
    ])
    return templates.TemplateResponse("legal.html", {"request": request, **context})


@router.get("/risk-disclaimer")
async def risk_disclaimer_page(request: Request):
    context = legal_context("Disclaimer trading et risques", "RISQUES", [
        ("Information uniquement", "XAUTERMINAL fournit des informations de marché, des outils de visualisation, des classements, des alertes et des lectures de contexte. Le service ne constitue pas un conseil en investissement, une recommandation personnalisée, une gestion de portefeuille, ou une incitation à acheter ou vendre un instrument financier."),
        ("Risque de perte", "Le trading, les CFD, le Forex, les cryptomonnaies, les actions, les indices, les matières premières et autres instruments financiers comportent un risque élevé de perte. Les performances passées ne préjugent pas des performances futures."),
        ("Données tierces", "Les prix, news, calendriers économiques, impacts, prévisions, données actual/forecast/previous et graphiques peuvent provenir de fournisseurs tiers. Ces informations peuvent être retardées, erronées, incomplètes ou indisponibles."),
        ("Bias Desk", "Le Bias Desk et les indicateurs associés sont des outils de lecture mécanique et contextuelle. Ils ne doivent pas être interprétés comme des signaux automatiques ou comme une garantie de résultat."),
        ("Responsabilité de l'utilisateur", "Chaque utilisateur doit effectuer ses propres vérifications, respecter son plan de trading, adapter la taille de ses positions et ne jamais engager de capitaux qu'il ne peut pas se permettre de perdre."),
        ("Aucune garantie", "XAUTERMINAL ne garantit aucun gain, aucune précision parfaite des données, aucune disponibilité continue et aucune adéquation du service à une situation financière particulière."),
    ])
    return templates.TemplateResponse("legal.html", {"request": request, **context})


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
