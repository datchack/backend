import json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response as FastAPIResponse

from app.config import (
    APP_BASE_URL,
    LEGAL_BUSINESS_ADDRESS,
    LEGAL_BUSINESS_ID,
    LEGAL_BUSINESS_NAME,
    LEGAL_CONTACT_EMAIL,
    LEGAL_HOSTING_PROVIDER,
    LEGAL_PUBLISHER_NAME,
)
from app.services.accounts import get_db_connection, require_owner, utc_now

router = APIRouter()


def absolute_url(path: str = "/") -> str:
    suffix = path if path.startswith("/") else f"/{path}"
    return f"{APP_BASE_URL}{suffix}"


FAVICON_LINKS = """    <link rel="icon" href="/static/favicon.ico" sizes="any">
    <link rel="icon" type="image/png" sizes="48x48" href="/static/favicon-48x48.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">
    <link rel="apple-touch-icon" href="/static/apple-icon-180x180.png">
    <link rel="manifest" href="/static/manifest.json">"""

BRAND_MARKUP = """<img class="brand-logo" src="/static/xauterminal-logo.png" alt="" width="36" height="36">
            <span>XAUTERMINAL</span>"""

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

SEO_CONTENT_PAGES = {
    "terminal_xauusd": {
        "path": "/terminal-xauusd",
        "title": "Terminal XAU/USD pour suivre l'or, le dollar et les taux",
        "description": "Comprendre comment XAUTERMINAL aide à suivre XAU/USD avec charting, news macro, calendrier économique, DXY, taux US et drivers de marché.",
        "kicker": "XAU/USD",
        "h1": "Terminal XAU/USD: suivre l'or avec une lecture macro claire",
        "intro": "XAU/USD réagit souvent à plusieurs forces en même temps: dollar américain, taux US, inflation, discours de la Fed, stress géopolitique et momentum court terme. XAUTERMINAL rassemble ces informations dans une interface pensée pour préparer une décision, pas pour remplacer une stratégie.",
        "sections": [
            (
                "Pourquoi XAU/USD demande une lecture multi-facteurs",
                "L'or peut monter parce que le dollar baisse, parce que les rendements réels se détendent, parce qu'un risque géopolitique soutient la demande refuge ou simplement parce que le momentum technique domine la séance. Regarder uniquement le graphique peut donc laisser une partie importante du contexte de côté.",
            ),
            (
                "Ce que le terminal centralise pour l'or",
                "Le profil XAU/USD regroupe le charting TradingView, les news liées à la Fed, au dollar, aux taux, à l'inflation et à la géopolitique, le calendrier économique US, une watchlist orientée or et un Bias Desk qui synthétise les drivers principaux.",
            ),
            (
                "Comment utiliser cette page dans une routine",
                "Avant une session, vérifie les événements US à venir, lis les news prioritaires, observe DXY et US10Y, puis compare ce contexte avec le mouvement de XAU/USD. L'objectif est d'éviter d'entrer sans savoir quel facteur domine le marché.",
            ),
            (
                "Limite importante",
                "Le terminal ne fournit pas de conseil financier ni de signal garanti. Il sert à structurer l'information et à gagner du temps dans l'analyse. La décision, le risque et la gestion de position restent sous ta responsabilité.",
            ),
            (
                "Routine simple avant une session XAU/USD",
                "Une routine efficace commence par les événements macro du jour, puis les thèmes dominants: inflation, Fed, dollar, rendements, risque géopolitique et sentiment global. Ensuite seulement, le graphique permet de vérifier si le prix confirme ou contredit ce contexte.",
            ),
            (
                "Pourquoi XAUTERMINAL existe",
                "L'objectif n'est pas d'ajouter un écran de plus, mais de réduire les allers-retours entre calendrier, news, watchlist, graphique et notes de contexte. Une lecture plus organisée aide à éviter les décisions prises uniquement sous pression ou sur une seule information.",
            ),
        ],
        "links": [
            ("/#pricing", "Démarrer l'essai XAUTERMINAL"),
            ("/calendrier-economique-or", "Lire le calendrier économique pour l'or"),
            ("/guide/trading-or-macro", "Comprendre la lecture macro de l'or"),
        ],
        "faqs": [
            (
                "XAUTERMINAL est-il seulement fait pour XAU/USD ?",
                "Non. XAU/USD est le marché central du projet, mais le terminal propose aussi des profils Forex, indices et crypto pour adapter les news, la watchlist et le contexte.",
            ),
            (
                "Le terminal remplace-t-il une stratégie de trading ?",
                "Non. Il sert à organiser l'information et à préparer une décision. La stratégie, le timing, le risque et l'exécution restent sous la responsabilité de l'utilisateur.",
            ),
        ],
    },
    "calendrier_or": {
        "path": "/calendrier-economique-or",
        "title": "Calendrier économique pour trader l'or: CPI, NFP, Fed et taux US",
        "description": "Guide pratique pour lire le calendrier économique quand on suit l'or et XAU/USD: inflation, NFP, Fed, taux US, dollar et volatilité.",
        "kicker": "CALENDRIER ÉCONOMIQUE",
        "h1": "Calendrier économique pour l'or: les événements à surveiller sur XAU/USD",
        "intro": "Sur XAU/USD, certaines statistiques peuvent changer brutalement la lecture du marché. L'inflation, l'emploi américain, les décisions de la Fed et les publications liées à la croissance influencent le dollar, les taux et donc l'or.",
        "sections": [
            (
                "Les publications qui comptent le plus",
                "Les traders sur l'or surveillent notamment le CPI, le PCE, les NFP, le chômage, les ventes au détail, les PMI, les décisions FOMC et les discours de membres de la Fed. Ces événements peuvent modifier les anticipations de taux et déclencher une forte volatilité.",
            ),
            (
                "Actual, forecast, previous: quoi comparer ?",
                "Une publication se lit rarement seule. Il faut comparer le chiffre publié au consensus et au chiffre précédent. Un résultat supérieur aux attentes peut soutenir le dollar ou les taux selon le contexte, ce qui peut peser sur l'or. L'inverse peut soutenir XAU/USD.",
            ),
            (
                "Pourquoi le timing est important",
                "Les minutes avant et après une publication importante sont souvent instables. Le terminal met en avant les événements à fort impact et les blocs de release pour éviter de découvrir trop tard qu'une statistique majeure arrive.",
            ),
            (
                "Utiliser le calendrier avec le reste du contexte",
                "Un calendrier seul ne suffit pas. Il faut le croiser avec les news, DXY, US10Y, le niveau de volatilité et le comportement du prix. C'est cette combinaison que XAUTERMINAL cherche à rendre plus lisible.",
            ),
            (
                "Préparer les annonces plutôt que les subir",
                "L'intérêt d'un calendrier n'est pas seulement de connaître l'heure d'une annonce. Il permet de décider à l'avance si l'on évite une zone de volatilité, si l'on attend la réaction du marché ou si l'on adapte son plan de risque.",
            ),
            (
                "Les annonces ne se lisent pas toutes pareil",
                "Une même surprise peut avoir un effet différent selon le contexte. Un CPI supérieur aux attentes ne produit pas toujours la même réaction si le marché anticipe déjà une Fed restrictive ou si le dollar est en correction depuis plusieurs séances.",
            ),
        ],
        "links": [
            ("/#pricing", "Tester le terminal complet"),
            ("/terminal-xauusd", "Suivre XAU/USD dans le terminal"),
            ("/news-forex-or", "Comprendre les news macro pour l'or"),
        ],
        "faqs": [
            (
                "Quels événements économiques influencent le plus l'or ?",
                "Les publications américaines comme CPI, PCE, NFP, chômage, PMI, ventes au détail, décisions FOMC et discours de la Fed sont souvent centrales car elles influencent le dollar et les taux.",
            ),
            (
                "Faut-il trader pendant les annonces ?",
                "Pas nécessairement. Beaucoup de traders préfèrent attendre que la volatilité initiale se calme. Le calendrier sert d'abord à connaître le risque événementiel avant de prendre une décision.",
            ),
        ],
    },
    "news_forex_or": {
        "path": "/news-forex-or",
        "title": "News Forex et or: filtrer les informations utiles pour XAU/USD",
        "description": "Comment filtrer les news forex, dollar, Fed, inflation, géopolitique et taux US pour mieux comprendre les mouvements de l'or et de XAU/USD.",
        "kicker": "NEWS MACRO",
        "h1": "News Forex et or: filtrer le bruit pour comprendre XAU/USD",
        "intro": "Les news de marché arrivent vite et dans tous les sens. Pour l'or, l'enjeu n'est pas de tout lire, mais d'identifier ce qui peut réellement changer le dollar, les taux, l'appétit pour le risque ou la demande refuge.",
        "sections": [
            (
                "Les familles de news à prioriser",
                "Pour XAU/USD, les catégories les plus utiles sont souvent la Fed, l'inflation, l'emploi américain, les rendements obligataires, le dollar, la géopolitique, les banques centrales et les surprises de données macro.",
            ),
            (
                "Pourquoi une news peut être importante sans bouger le marché",
                "Une information peut être vraie mais déjà intégrée par les prix. Le terminal aide à distinguer les news récentes, les sujets officiels, les informations répétées par plusieurs sources et les éléments potentiellement market moving.",
            ),
            (
                "Croiser les news avec DXY et US10Y",
                "Une news hawkish sur la Fed peut soutenir le dollar et les rendements, ce qui met souvent l'or sous pression. Une news dovish ou un stress géopolitique peut produire l'effet inverse. La watchlist permet de vérifier rapidement cette cohérence.",
            ),
            (
                "Créer une routine plus calme",
                "L'objectif n'est pas de réagir à chaque headline. Une bonne routine consiste à lire les priorités, repérer le thème dominant, vérifier si le prix confirme, puis attendre un setup compatible avec son propre plan.",
            ),
            (
                "Différencier information et décision",
                "Une headline peut expliquer un mouvement sans offrir une opportunité exploitable. XAUTERMINAL aide à classer l'information, mais la décision doit venir d'un plan cohérent entre contexte, prix, risque et horizon de temps.",
            ),
            (
                "Pourquoi le bruit coûte cher",
                "Trop de sources ouvertes en même temps peuvent pousser à surinterpréter chaque variation. Un flux mieux organisé permet de se concentrer sur les thèmes réellement capables de modifier le dollar, les taux ou la demande refuge.",
            ),
        ],
        "links": [
            ("/#pricing", "Essayer XAUTERMINAL"),
            ("/calendrier-economique-or", "Comparer avec le calendrier économique"),
            ("/guide/trading-or-macro", "Construire une lecture macro"),
        ],
        "faqs": [
            (
                "Quelles news suivre pour XAU/USD ?",
                "Les news liées à la Fed, à l'inflation, à l'emploi américain, au dollar, aux rendements obligataires, à la géopolitique et au sentiment de risque sont souvent les plus utiles.",
            ),
            (
                "Une news importante fait-elle toujours bouger l'or ?",
                "Non. Si l'information est déjà intégrée par les prix ou si un autre thème domine le marché, la réaction peut être faible, retardée ou opposée à l'intuition initiale.",
            ),
        ],
    },
    "guide_trading_or_macro": {
        "path": "/guide/trading-or-macro",
        "title": "Guide macro pour trader l'or: dollar, taux, inflation et Fed",
        "description": "Guide pédagogique pour comprendre les principaux drivers macro de l'or: DXY, taux US, inflation, Fed, stress de marché et momentum.",
        "kicker": "GUIDE MACRO",
        "h1": "Guide macro pour trader l'or: dollar, taux, inflation et Fed",
        "intro": "Trader l'or sans contexte macro peut devenir confus: le même mouvement de prix peut venir d'un dollar faible, d'une baisse des rendements, d'une surprise d'inflation ou d'un stress de marché. Ce guide résume les drivers à suivre avant d'utiliser le terminal.",
        "sections": [
            (
                "Dollar américain et or",
                "XAU/USD est coté en dollars. Quand le dollar se renforce fortement, l'or peut devenir plus difficile à acheter pour les autres devises, ce qui pèse souvent sur le prix. Quand le dollar se détend, XAU/USD peut respirer davantage.",
            ),
            (
                "Taux US et rendement réel",
                "L'or ne verse pas de rendement. Quand les taux et les rendements réels montent, les actifs rémunérés deviennent plus attractifs. Quand ils baissent, l'or peut redevenir plus compétitif, surtout si l'inflation ou le risque restent présents.",
            ),
            (
                "Fed, inflation et emploi",
                "La Fed influence les anticipations de taux. Les chiffres d'inflation et d'emploi modifient ces anticipations. C'est pour cela que CPI, PCE, NFP et FOMC sont souvent des moments clés pour XAU/USD.",
            ),
            (
                "Momentum et confirmation",
                "Le contexte macro donne une direction probable, mais le prix doit confirmer. Le Bias Desk et les drivers du terminal servent à organiser cette lecture: macro, momentum, risque événementiel et watchlist.",
            ),
            (
                "Construire un scénario plutôt qu'une prédiction",
                "Une lecture macro utile ne cherche pas à deviner parfaitement le futur. Elle prépare plusieurs scénarios: dollar fort, détente des taux, surprise inflation, stress de marché ou absence de catalyseur clair.",
            ),
            (
                "Relier macro et exécution",
                "Le contexte aide à savoir où concentrer son attention, mais il ne suffit pas pour entrer en position. L'exécution demande un plan, un niveau d'invalidation, une taille adaptée et une acceptation claire du risque.",
            ),
        ],
        "links": [
            ("/#pricing", "Tester XAUTERMINAL"),
            ("/terminal-xauusd", "Voir l'approche XAU/USD"),
            ("/news-forex-or", "Lire les news macro utiles"),
        ],
        "faqs": [
            (
                "Quels sont les grands drivers macro de l'or ?",
                "Les plus importants sont souvent le dollar américain, les taux US, les rendements réels, l'inflation, la Fed, la géopolitique, le stress de marché et le momentum du prix.",
            ),
            (
                "La macro suffit-elle pour trader l'or ?",
                "Non. La macro donne un cadre de lecture, mais le prix, la volatilité, la liquidité, le timing et la gestion du risque restent indispensables.",
            ),
        ],
    },
}

RESOURCE_PAGE_ORDER = [
    "terminal_xauusd",
    "calendrier_or",
    "news_forex_or",
    "guide_trading_or_macro",
]


def content_page(page_key: str) -> str:
    page = SEO_CONTENT_PAGES[page_key]
    prefix = f"seo_{page_key}"
    canonical = absolute_url(page["path"])
    escaped_title = escape(page["title"], quote=True)
    escaped_description = escape(page["description"], quote=True)
    escaped_h1 = escape(page["h1"])
    escaped_intro = escape(page["intro"])
    sections = "\n".join(
        f"""        <section>
            <h2 data-i18n="{prefix}_section{index}_title">{escape(title)}</h2>
            <p data-i18n="{prefix}_section{index}_copy">{escape(copy)}</p>
        </section>"""
        for index, (title, copy) in enumerate(page["sections"], start=1)
    )
    faqs = page.get("faqs", [])
    faq_html = "\n".join(
        f"""            <article>
                <h3 data-i18n="{prefix}_faq{index}_question">{escape(question)}</h3>
                <p data-i18n="{prefix}_faq{index}_answer">{escape(answer)}</p>
            </article>"""
        for index, (question, answer) in enumerate(faqs, start=1)
    )
    faq_section = f"""        <section class="resource-faq">
            <div class="landing-kicker" data-i18n="seo_faq_kicker">FAQ</div>
            <h2 data-i18n="seo_faq_title">Questions fréquentes</h2>
{faq_html}
        </section>""" if faq_html else ""
    links = "\n".join(
        f'<a class="resource-link-button" href="{escape(href, quote=True)}" data-i18n="{prefix}_link{index}">{escape(label)}</a>'
        for index, (href, label) in enumerate(page["links"], start=1)
    )
    related_links = ", ".join(label for _, label in page["links"])
    structured_graph = [
        {
            "@type": "Article",
            "headline": page["h1"],
            "description": page["description"],
            "url": canonical,
            "author": {
                "@type": "Person",
                "name": LEGAL_PUBLISHER_NAME,
            },
            "publisher": {
                "@type": "Organization",
                "name": LEGAL_BUSINESS_NAME,
                "url": APP_BASE_URL,
                "logo": absolute_url("/static/icon-192x192.png"),
            },
            "mainEntityOfPage": canonical,
            "inLanguage": "fr-FR",
            "about": related_links,
        }
    ]
    if faqs:
        structured_graph.append(
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": answer,
                        },
                    }
                    for question, answer in faqs
                ],
            }
        )
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": structured_graph,
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="{prefix}_title">{escaped_title}</title>
    <meta name="description" content="{escaped_description}" data-i18n-content="{prefix}_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="{escaped_title}" data-i18n-content="{prefix}_title">
    <meta property="og:description" content="{escaped_description}" data-i18n-content="{prefix}_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/#features" data-i18n="nav_tools">Outils</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page">
        <div class="landing-kicker" data-i18n="{prefix}_kicker">{escape(page["kicker"])}</div>
        <h1 data-i18n="{prefix}_h1">{escaped_h1}</h1>
        <p data-i18n="{prefix}_intro">{escaped_intro}</p>
{sections}
{faq_section}
        <section class="legal-contact">
            <h2 data-i18n="seo_continue_title">Continuer avec XAUTERMINAL</h2>
            <p data-i18n="seo_continue_copy">Ces ressources sont pensées pour être utilisées ensemble: contexte macro, calendrier économique, news filtrées et charting. Pour tester l'espace complet, reviens sur la landing et démarre l'essai depuis le parcours officiel.</p>
            <div class="landing-actions">{links}</div>
        </section>
    </main>
    <footer class="landing-footer">
        <div>
            <strong>XAUTERMINAL</strong>
            <span data-i18n="footer_tagline">Terminal macro et trading professionnel. Outil d'information, pas un conseil financier.</span>
        </div>
        <nav aria-label="Ressources">
            <a href="/terminal-xauusd" data-i18n="resource_terminal_short">XAU/USD</a>
            <a href="/calendrier-economique-or" data-i18n="resource_calendar_short">Calendrier or</a>
            <a href="/news-forex-or" data-i18n="resource_news_short">News forex</a>
            <a href="/guide/trading-or-macro" data-i18n="resource_guide_short">Guide macro</a>
        </nav>
    </footer>
    <script src="/static/landing.js"></script>
</body>
</html>"""


def resources_page() -> str:
    canonical = absolute_url("/ressources")
    rows = "\n".join(
        f"""        <article class="resource-row">
            <div>
                <h2><a href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="seo_{key}_h1">{escape(SEO_CONTENT_PAGES[key]["h1"])}</a></h2>
                <p data-i18n="seo_{key}_description">{escape(SEO_CONTENT_PAGES[key]["description"])}</p>
            </div>
            <a class="resource-cta" href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="resources_page_read">Lire</a>
        </article>"""
        for key in RESOURCE_PAGE_ORDER
    )
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Ressources XAUTERMINAL",
            "description": "Guides publics pour comprendre XAU/USD, les news macro, le calendrier économique et les drivers de l'or.",
            "url": canonical,
            "hasPart": [
                {
                    "@type": "Article",
                    "headline": SEO_CONTENT_PAGES[key]["h1"],
                    "url": absolute_url(SEO_CONTENT_PAGES[key]["path"]),
                }
                for key in RESOURCE_PAGE_ORDER
            ],
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="resources_page_title">Ressources trading macro, XAU/USD et calendrier économique - XAUTERMINAL</title>
    <meta name="description" content="Guides XAUTERMINAL pour comprendre XAU/USD, le calendrier économique de l'or, les news Forex et les principaux drivers macro." data-i18n-content="resources_page_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="Ressources trading macro, XAU/USD et calendrier économique" data-i18n-content="resources_page_title">
    <meta property="og:description" content="Guides publics pour mieux lire l'or, les news macro, le calendrier économique et les drivers de marché." data-i18n-content="resources_page_description">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
    <script type="application/ld+json">{structured_data}</script>
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
            {BRAND_MARKUP}
        </a>
        <nav class="landing-nav-actions" aria-label="Navigation principale">
            <a href="/#features" data-i18n="nav_tools">Outils</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page">
        <div class="landing-kicker" data-i18n="resources_kicker">RESSOURCES</div>
        <h1 data-i18n="resources_page_h1">Ressources trading macro, XAU/USD et calendrier économique</h1>
        <p data-i18n="resources_page_intro">Ces pages expliquent les concepts réellement liés à XAUTERMINAL: lecture macro de l'or, événements économiques, news Forex et organisation d'une routine de marché. Elles servent à comprendre le produit avant de l'utiliser dans le terminal.</p>
        <section class="resource-list">
{rows}
        </section>
    </main>
    <footer class="landing-footer">
        <div>
            <strong>XAUTERMINAL</strong>
            <span data-i18n="footer_tagline">Terminal macro et trading professionnel. Outil d'information, pas un conseil financier.</span>
        </div>
        <nav aria-label="Documents légaux">
            <a href="/terms" data-i18n="terms_kicker">CGU</a>
            <a href="/privacy" data-i18n="privacy_kicker">Confidentialité</a>
            <a href="/risk-disclaimer" data-i18n="risk_footer_link">Disclaimer trading</a>
        </nav>
    </footer>
    <script src="/static/landing.js"></script>
</body>
</html>"""


def legal_page(title_key: str, kicker_key: str, sections: list[tuple[str, str]]) -> str:
    meta = LEGAL_PAGE_META[title_key]
    business_name = LEGAL_BUSINESS_NAME
    email = LEGAL_CONTACT_EMAIL
    updated = utc_now().date().strftime("%d/%m/%Y")
    page_path = {
        "terms_title": "/terms",
        "privacy_title": "/privacy",
        "risk_title": "/risk-disclaimer",
    }[title_key]
    canonical = absolute_url(page_path)
    page_title = f'{meta["title"]} - {business_name}'
    escaped_description = escape(meta["description"], quote=True)
    section_html = "\n".join(
        f'<section><h2 data-i18n="{section_title_key}">{section_title_key}</h2><p data-i18n="{section_content_key}">{section_content_key}</p></section>'
        for section_title_key, section_content_key in sections
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="{title_key}">{page_title}</title>
    <meta name="description" content="{escaped_description}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="{business_name}">
    <meta property="og:title" content="{page_title}">
    <meta property="og:description" content="{escaped_description}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{absolute_url('/static/icon-192x192.png')}">
    <meta name="twitter:card" content="summary">
{FAVICON_LINKS}
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body class="legal-body">
    <header class="landing-nav">
        <a class="landing-brand" href="/" aria-label="{business_name}">
            {BRAND_MARKUP}
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
            <span data-i18n="footer_tagline">Terminal macro et trading professionnel. Outil d'information, pas un conseil financier.</span>
        </div>
        <nav aria-label="Documents légaux">
            <a href="/terms" data-i18n="terms_kicker">CGU</a>
            <a href="/privacy" data-i18n="privacy_kicker">Confidentialité</a>
            <a href="/risk-disclaimer" data-i18n="risk_footer_link">Disclaimer trading</a>
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
    return FileResponse("templates/index.html", headers={"X-Robots-Tag": "noindex, follow"})


@router.get("/account", response_class=HTMLResponse)
async def account_page():
    return FileResponse("templates/account.html")


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page():
    return FileResponse("templates/reset_password.html")


@router.get("/ressources", response_class=HTMLResponse)
async def resources_index_page():
    return HTMLResponse(resources_page())


@router.get("/terminal-xauusd", response_class=HTMLResponse)
async def terminal_xauusd_page():
    return HTMLResponse(content_page("terminal_xauusd"))


@router.get("/calendrier-economique-or", response_class=HTMLResponse)
async def calendrier_economique_or_page():
    return HTMLResponse(content_page("calendrier_or"))


@router.get("/news-forex-or", response_class=HTMLResponse)
async def news_forex_or_page():
    return HTMLResponse(content_page("news_forex_or"))


@router.get("/guide/trading-or-macro", response_class=HTMLResponse)
async def guide_trading_or_macro_page():
    return HTMLResponse(content_page("guide_trading_or_macro"))


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
    return f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /db-test
Disallow: /api/
Disallow: /ws/

Sitemap: {absolute_url('/sitemap.xml')}
"""


@router.get("/sitemap.xml")
async def sitemap_xml():
    today = utc_now().date().isoformat()
    urls = [
        ("/", "daily", "1.0"),
        ("/ressources", "weekly", "0.8"),
        ("/terminal-xauusd", "weekly", "0.8"),
        ("/calendrier-economique-or", "weekly", "0.8"),
        ("/news-forex-or", "weekly", "0.8"),
        ("/guide/trading-or-macro", "weekly", "0.8"),
        ("/terms", "monthly", "0.5"),
        ("/privacy", "monthly", "0.5"),
        ("/risk-disclaimer", "monthly", "0.5"),
    ]
    items = "\n".join(
        f"""  <url>
    <loc>{absolute_url(path)}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
        for path, changefreq, priority in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
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
