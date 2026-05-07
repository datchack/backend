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

PUBLIC_FOOTER = """    <footer class="landing-footer">
        <div class="footer-brand">
            <a class="landing-brand" href="/" aria-label="XAUTERMINAL">
                <img class="brand-logo" src="/static/xauterminal-logo.png" alt="" width="36" height="36">
                <span>XAUTERMINAL</span>
            </a>
            <p data-i18n="footer_tagline">Terminal macro et trading professionnel. Outil d'information, pas un conseil financier.</p>
            <a class="resource-cta" href="/#pricing" data-i18n="footer_trial">Démarrer l'essai</a>
        </div>
        <nav class="footer-grid" aria-label="Plan du site">
            <div class="footer-column">
                <h3 data-i18n="footer_product">Produit</h3>
                <a href="/#features" data-i18n="nav_tools">Outils</a>
                <a href="/#profiles" data-i18n="nav_markets">Marchés</a>
                <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
                <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_learn">Apprendre</h3>
                <a href="/guides" data-i18n="nav_guides">Guides</a>
                <a href="/ressources" data-i18n="nav_resources">Ressources</a>
                <a href="/terminal-xauusd" data-i18n="resource_terminal_short">XAU/USD</a>
                <a href="/guide/trading-or-macro" data-i18n="resource_guide_short">Guide macro</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_markets">Marchés et données</h3>
                <a href="/calendrier-economique-or" data-i18n="resource_calendar_short">Calendrier or</a>
                <a href="/news-forex-or" data-i18n="resource_news_short">News forex</a>
                <a href="/guides/dxy-taux-us-or" data-i18n="footer_dxy_rates">DXY et taux US</a>
                <a href="/guides/bias-desk-trading" data-i18n="footer_bias_desk">Bias Desk</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_account">Compte</h3>
                <a href="/account" data-i18n="nav_account">Mon compte</a>
                <a href="/support" data-i18n="nav_support">Support</a>
                <a href="/#pricing" data-i18n="footer_subscriptions">Abonnements</a>
                <a href="mailto:mdtrading@xauterminal.com" data-i18n="footer_contact">Contact</a>
            </div>
            <div class="footer-column">
                <h3 data-i18n="footer_legal">Légal</h3>
                <a href="/terms" data-i18n="terms_kicker">CGU</a>
                <a href="/privacy" data-i18n="privacy_kicker">Confidentialité</a>
                <a href="/risk-disclaimer" data-i18n="risk_footer_link">Disclaimer trading</a>
            </div>
        </nav>
        <div class="footer-risk" data-i18n="footer_risk">
            Le trading comporte un risque de perte. XAUTERMINAL fournit des informations de marché et des outils d'organisation, sans conseil financier personnalisé.
        </div>
    </footer>"""

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
    "routine_trading_xauusd": {
        "path": "/guides/routine-trading-xauusd",
        "title": "Routine trading XAU/USD: préparer une session avec méthode",
        "description": "Méthode concrète pour préparer une session XAU/USD avec calendrier économique, news macro, DXY, taux US, Bias Desk et niveaux de risque.",
        "kicker": "ROUTINE XAU/USD",
        "h1": "Routine trading XAU/USD: préparer une session sans se disperser",
        "intro": "Une routine de marché sert à réduire le bruit avant d'ouvrir un graphique. Sur XAU/USD, l'objectif est de comprendre le thème dominant de la séance: dollar, taux, inflation, Fed, stress de marché ou simple momentum technique.",
        "sections": [
            (
                "Commencer par le calendrier",
                "Avant de regarder le prix, vérifie les annonces à venir: CPI, PCE, NFP, chômage, PMI, ventes au détail, FOMC et discours de la Fed. Une statistique majeure peut rendre un setup propre beaucoup moins lisible quelques minutes plus tard.",
            ),
            (
                "Identifier le thème macro du jour",
                "Lis les news prioritaires et cherche le fil conducteur: Fed plus restrictive, dollar sous pression, rendements en hausse, stress géopolitique ou absence de catalyseur clair. Une séance sans thème dominant demande souvent plus de patience.",
            ),
            (
                "Comparer XAU/USD avec DXY et US10Y",
                "Si l'or monte pendant que DXY et les taux baissent, le mouvement est plus cohérent. Si les signaux divergent, il vaut mieux éviter de conclure trop vite. Le but est de savoir si le prix est porté ou contrarié par ses drivers principaux.",
            ),
            (
                "Utiliser le Bias Desk comme synthèse",
                "Le Bias Desk n'est pas un signal automatique. Il aide à regrouper momentum, macro, risk tone et risque événementiel. S'il affiche WAIT, cela peut simplement signifier que les conditions ne sont pas assez alignées.",
            ),
            (
                "Finir par le plan de risque",
                "Une fois le contexte compris, le graphique sert à définir le timing, l'invalidation et la taille. La meilleure lecture macro ne protège pas d'une mauvaise exécution ou d'un risque trop grand.",
            ),
        ],
        "links": [
            ("/#pricing", "Tester le terminal complet"),
            ("/calendrier-economique-or", "Lire le calendrier économique"),
            ("/news-forex-or", "Filtrer les news macro"),
        ],
        "faqs": [
            (
                "Combien de temps doit durer une routine XAU/USD ?",
                "Une routine utile peut durer quelques minutes si elle est structurée: calendrier, news, DXY, US10Y, Bias Desk puis graphique. L'important est la régularité, pas la durée.",
            ),
            (
                "Faut-il suivre toutes les news avant de trader ?",
                "Non. Il faut surtout repérer les thèmes capables de changer le dollar, les taux, la demande refuge ou la volatilité. Lire trop de sources peut créer plus de confusion que de clarté.",
            ),
        ],
    },
    "dxy_taux_or": {
        "path": "/guides/dxy-taux-us-or",
        "title": "DXY, taux US et or: comprendre les relations avec XAU/USD",
        "description": "Guide XAUTERMINAL pour comprendre comment le dollar, les rendements US, la Fed et le sentiment de risque influencent l'or et XAU/USD.",
        "kicker": "DXY ET TAUX US",
        "h1": "DXY, taux US et or: comprendre les relations avec XAU/USD",
        "intro": "L'or ne bouge pas dans le vide. Même quand le graphique semble clair, XAU/USD reste influencé par le dollar américain, les rendements obligataires, les anticipations de taux et le niveau de stress de marché.",
        "sections": [
            (
                "Pourquoi le dollar compte autant",
                "XAU/USD est coté en dollars. Un dollar fort peut rendre l'or plus cher pour les acheteurs hors dollar et peser sur le prix. Un dollar plus faible peut au contraire soutenir le métal, surtout si les autres facteurs ne s'y opposent pas.",
            ),
            (
                "Le rôle des taux US",
                "L'or ne verse pas de rendement. Quand les rendements US montent, les actifs rémunérés deviennent plus compétitifs. Quand ils baissent, l'or peut retrouver de l'attrait, notamment si le marché anticipe une Fed moins restrictive.",
            ),
            (
                "Quand DXY et taux ne racontent pas la même histoire",
                "Il arrive que le dollar monte alors que les taux baissent, ou l'inverse. Dans ce cas, la lecture devient moins directe. Le trader doit chercher quel driver domine réellement le mouvement de XAU/USD.",
            ),
            (
                "Ajouter le sentiment de risque",
                "En période de stress, l'or peut être soutenu même si certains drivers semblent défavorables. À l'inverse, une séance très risk-on peut réduire la demande refuge. C'est pour cela qu'une lecture multi-facteurs est nécessaire.",
            ),
            (
                "Comment XAUTERMINAL organise cette lecture",
                "Le terminal regroupe DXY, US10Y, news macro, calendrier économique et Bias Desk. L'idée est de vérifier rapidement si les mouvements se confirment ou se contredisent avant de prendre une décision.",
            ),
        ],
        "links": [
            ("/terminal-xauusd", "Voir l'approche XAU/USD"),
            ("/guide/trading-or-macro", "Lire le guide macro"),
            ("/#pricing", "Essayer XAUTERMINAL"),
        ],
        "faqs": [
            (
                "XAU/USD baisse-t-il toujours quand DXY monte ?",
                "Non. C'est une relation fréquente mais pas mécanique. Les taux, la Fed, le risque géopolitique et le momentum peuvent modifier ou retarder la réaction.",
            ),
            (
                "Les taux US sont-ils plus importants que le dollar ?",
                "Cela dépend du contexte. Certaines séances sont dominées par le dollar, d'autres par les rendements, la Fed ou le sentiment de risque. L'intérêt est de comparer ces forces ensemble.",
            ),
        ],
    },
    "bias_desk": {
        "path": "/guides/bias-desk-trading",
        "title": "Bias Desk trading: lire les drivers sans confondre outil et signal",
        "description": "Comprendre comment utiliser un Bias Desk pour organiser les drivers de marché sans transformer une synthèse macro en signal de trading automatique.",
        "kicker": "BIAS DESK",
        "h1": "Bias Desk trading: lire les drivers sans confondre outil et signal",
        "intro": "Un Bias Desk sert à résumer une lecture de marché: momentum, macro, risque événementiel, sentiment et drivers principaux. Il ne remplace pas une stratégie, mais il peut aider à éviter les décisions prises sur une seule information.",
        "sections": [
            (
                "Ce qu'un bias veut dire",
                "Un bias est une orientation de contexte, pas une certitude. Bullish signifie que plusieurs éléments soutiennent plutôt la hausse. Bearish signifie que les pressions baissières dominent. Neutral ou WAIT indique souvent un manque d'alignement.",
            ),
            (
                "Pourquoi les drivers sont plus utiles que le score seul",
                "Le score donne une synthèse rapide, mais les raisons sont plus importantes. Un trader doit savoir si le bias vient du dollar, des taux, du momentum, d'une news ou d'un risque événementiel.",
            ),
            (
                "Lire le risque événementiel",
                "Un contexte favorable peut devenir dangereux juste avant une annonce majeure. Si le calendrier indique un risque élevé, la bonne décision peut être d'attendre, même si le reste du marché semble aligné.",
            ),
            (
                "Utiliser le bias avec le graphique",
                "Le graphique reste indispensable pour le timing. Le bias aide à préparer le scénario; le prix aide à décider si ce scénario mérite d'être exécuté, invalidé ou simplement observé.",
            ),
            (
                "Les limites d'une synthèse automatique",
                "Aucun outil ne peut comprendre parfaitement chaque nuance de marché. Le Bias Desk doit être traité comme une aide à la lecture, avec une vérification humaine et une gestion du risque indépendante.",
            ),
        ],
        "links": [
            ("/terminal-xauusd", "Voir le terminal XAU/USD"),
            ("/guides/routine-trading-xauusd", "Construire une routine"),
            ("/risk-disclaimer", "Lire le disclaimer trading"),
        ],
        "faqs": [
            (
                "Le Bias Desk donne-t-il des signaux d'achat ou de vente ?",
                "Non. Il organise les drivers de marché. La décision d'entrer, sortir ou rester à l'écart doit venir de ta stratégie, de ton timing et de ta gestion du risque.",
            ),
            (
                "Pourquoi le Bias Desk affiche parfois WAIT ?",
                "WAIT apparaît quand les drivers sont mixtes, quand la confiance est insuffisante ou quand un risque événementiel rend la lecture trop instable.",
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

GUIDE_PAGE_ORDER = [
    "routine_trading_xauusd",
    "dxy_taux_or",
    "bias_desk",
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
        f"""                <section class="article-section-card" id="section-{index}">
                    <span>{index:02d}</span>
                    <h2 data-i18n="{prefix}_section{index}_title">{escape(title)}</h2>
                    <p data-i18n="{prefix}_section{index}_copy">{escape(copy)}</p>
                </section>"""
        for index, (title, copy) in enumerate(page["sections"], start=1)
    )
    section_nav = "\n".join(
        f"""                    <a href="#section-{index}" data-i18n="{prefix}_section{index}_title">{escape(title)}</a>"""
        for index, (title, _) in enumerate(page["sections"], start=1)
    )
    faqs = page.get("faqs", [])
    faq_html = "\n".join(
        f"""                    <article>
                <h3 data-i18n="{prefix}_faq{index}_question">{escape(question)}</h3>
                <p data-i18n="{prefix}_faq{index}_answer">{escape(answer)}</p>
                    </article>"""
        for index, (question, answer) in enumerate(faqs, start=1)
    )
    faq_section = f"""                <section class="resource-faq">
                    <div class="landing-kicker" data-i18n="seo_faq_kicker">FAQ</div>
                    <h2 data-i18n="seo_faq_title">Questions fréquentes</h2>
{faq_html}
                </section>""" if faq_html else ""
    links = "\n".join(
        f'<a class="resource-link-button" href="{escape(href, quote=True)}" data-i18n="{prefix}_link{index}">{escape(label)}</a>'
        for index, (href, label) in enumerate(page["links"], start=1)
    )
    featured_links = "\n".join(
        f"""                    <a href="{escape(href, quote=True)}" data-i18n="{prefix}_link{index}">{escape(label)}</a>"""
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
    <main class="legal-page article-page">
        <section class="article-hero">
            <div class="article-hero-copy">
                <div class="landing-kicker" data-i18n="{prefix}_kicker">{escape(page["kicker"])}</div>
                <h1 data-i18n="{prefix}_h1">{escaped_h1}</h1>
                <p data-i18n="{prefix}_intro">{escaped_intro}</p>
                <div class="landing-actions">{links}</div>
            </div>
            <aside class="article-hero-panel" aria-label="Résumé">
                <span data-i18n="article_panel_kicker">À LIRE AVEC</span>
                <strong>XAUTERMINAL</strong>
                <p data-i18n="article_panel_copy">Utilise cette ressource avec le calendrier, les news, les graphiques et le Bias Desk pour garder une lecture de marché structurée.</p>
            </aside>
        </section>
        <div class="article-layout">
            <aside class="article-sidebar" aria-label="Sommaire">
                <span data-i18n="article_summary">Sommaire</span>
                <nav>
{section_nav}
                </nav>
                <div class="article-related">
                    <strong data-i18n="article_related">Liens utiles</strong>
{featured_links}
                </div>
            </aside>
            <div class="article-content">
{sections}
{faq_section}
                <section class="legal-contact article-cta">
                    <h2 data-i18n="seo_continue_title">Continuer avec XAUTERMINAL</h2>
                    <p data-i18n="seo_continue_copy">Ces ressources sont pensées pour être utilisées ensemble: contexte macro, calendrier économique, news filtrées et charting. Pour tester l'espace complet, reviens sur la landing et démarre l'essai depuis le parcours officiel.</p>
                    <div class="landing-actions">{links}</div>
                </section>
            </div>
        </div>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


def resources_page() -> str:
    canonical = absolute_url("/ressources")
    rows = "\n".join(
        f"""        <article class="resource-row">
            <div>
                <span data-i18n="seo_{key}_kicker">{escape(SEO_CONTENT_PAGES[key]["kicker"])}</span>
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
    <main class="legal-page resource-index-page">
        <section class="article-hero resource-index-hero">
            <div class="article-hero-copy">
                <div class="landing-kicker" data-i18n="resources_kicker">RESSOURCES</div>
                <h1 data-i18n="resources_page_h1">Ressources trading macro, XAU/USD et calendrier économique</h1>
                <p data-i18n="resources_page_intro">Ces pages expliquent les concepts réellement liés à XAUTERMINAL: lecture macro de l'or, événements économiques, news Forex et organisation d'une routine de marché. Elles servent à comprendre le produit avant de l'utiliser dans le terminal.</p>
            </div>
            <aside class="article-hero-panel" aria-label="Ressources">
                <span data-i18n="resources_panel_kicker">HUB PUBLIC</span>
                <strong data-i18n="resources_panel_title">Comprendre avant d'agir</strong>
                <p data-i18n="resources_panel_copy">Chaque page relie une notion de marché à l'usage concret du terminal: news, calendrier, drivers et graphique.</p>
            </aside>
        </section>
        <section class="resource-list">
{rows}
        </section>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


def guides_page() -> str:
    canonical = absolute_url("/guides")
    rows = "\n".join(
        f"""        <article class="guide-card">
            <div class="guide-card-top">
                <span data-i18n="seo_{key}_kicker">{escape(SEO_CONTENT_PAGES[key]["kicker"])}</span>
                <a class="resource-link-button" href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="resources_page_read">Lire</a>
            </div>
            <h2><a href="{escape(SEO_CONTENT_PAGES[key]["path"], quote=True)}" data-i18n="seo_{key}_h1">{escape(SEO_CONTENT_PAGES[key]["h1"])}</a></h2>
            <p data-i18n="seo_{key}_description">{escape(SEO_CONTENT_PAGES[key]["description"])}</p>
        </article>"""
        for key in GUIDE_PAGE_ORDER
    )
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Guides trading XAUTERMINAL",
            "description": "Guides pratiques pour préparer une session XAU/USD, comprendre DXY, les taux US, les news macro et le Bias Desk.",
            "url": canonical,
            "hasPart": [
                {
                    "@type": "Article",
                    "headline": SEO_CONTENT_PAGES[key]["h1"],
                    "description": SEO_CONTENT_PAGES[key]["description"],
                    "url": absolute_url(SEO_CONTENT_PAGES[key]["path"]),
                }
                for key in GUIDE_PAGE_ORDER
            ],
        },
        ensure_ascii=False,
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="guides_page_title">Guides trading XAU/USD, macro et Bias Desk - XAUTERMINAL</title>
    <meta name="description" content="Guides XAUTERMINAL pour préparer une session XAU/USD, comprendre DXY, les taux US, les news macro et utiliser un Bias Desk." data-i18n-content="guides_page_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="Guides trading XAU/USD, macro et Bias Desk" data-i18n-content="guides_page_title">
    <meta property="og:description" content="Guides pratiques pour mieux préparer une session de trading avec le terminal XAUTERMINAL." data-i18n-content="guides_page_description">
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
            <a href="/ressources" data-i18n="nav_resources">Ressources</a>
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/terminal" data-i18n="nav_terminal">Ouvrir le terminal</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>
    <main class="legal-page guide-index-page">
        <section class="article-hero resource-index-hero">
            <div class="article-hero-copy">
                <div class="landing-kicker" data-i18n="guides_page_kicker">GUIDES TRADING</div>
                <h1 data-i18n="guides_page_h1">Guides trading XAU/USD, macro et Bias Desk</h1>
                <p data-i18n="guides_page_intro">Ces guides servent à construire une routine claire autour du terminal: préparer une session, lire DXY et les taux US, filtrer les news et utiliser le Bias Desk sans le confondre avec un signal automatique.</p>
            </div>
            <aside class="article-hero-panel" aria-label="Guides">
                <span data-i18n="guides_panel_kicker">ROUTINE</span>
                <strong data-i18n="guides_panel_title">Passer du bruit au plan</strong>
                <p data-i18n="guides_panel_copy">Les guides sont pensés comme des points d'entrée rapides avant d'ouvrir le terminal et d'observer les drivers réels.</p>
            </aside>
        </section>
        <section class="guide-grid">
{rows}
        </section>
        <section class="legal-contact">
            <h2 data-i18n="guides_page_next_title">Utiliser les guides avec le terminal</h2>
            <p data-i18n="guides_page_next_copy">Commence par comprendre la routine, puis ouvre le terminal pour vérifier le calendrier, les news, le graphique et les drivers en conditions réelles.</p>
            <div class="landing-actions">
                <a class="resource-cta" href="/#pricing" data-i18n="guides_page_trial">Tester XAUTERMINAL</a>
                <a class="resource-link-button" href="/ressources" data-i18n="guides_page_resources">Voir toutes les ressources</a>
            </div>
        </section>
    </main>
{PUBLIC_FOOTER}
    <script src="/static/landing.js"></script>
</body>
</html>"""


def support_page() -> str:
    canonical = absolute_url("/support")
    email = LEGAL_CONTACT_EMAIL
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "ContactPage",
            "name": "Support XAUTERMINAL",
            "description": "Aide XAUTERMINAL pour les comptes, codes email, paiements Stripe, abonnements, accès au terminal et sécurité.",
            "url": canonical,
            "publisher": {
                "@type": "Organization",
                "name": LEGAL_BUSINESS_NAME,
                "url": APP_BASE_URL,
                "logo": absolute_url("/static/icon-192x192.png"),
                "contactPoint": {
                    "@type": "ContactPoint",
                    "email": email,
                    "contactType": "customer support",
                    "availableLanguage": ["fr", "en"],
                },
            },
        },
        ensure_ascii=False,
    )
    cards = [
        ("support_card_code_title", "support_card_code_copy"),
        ("support_card_paid_title", "support_card_paid_copy"),
        ("support_card_password_title", "support_card_password_copy"),
        ("support_card_subscription_title", "support_card_subscription_copy"),
        ("support_card_terminal_title", "support_card_terminal_copy"),
        ("support_card_security_title", "support_card_security_copy"),
    ]
    card_html = "\n".join(
        f"""            <article class="support-card">
                <h2 data-i18n="{title_key}">{title_key}</h2>
                <p data-i18n="{copy_key}">{copy_key}</p>
            </article>"""
        for title_key, copy_key in cards
    )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-i18n="support_title">Support XAUTERMINAL</title>
    <meta name="description" content="Aide XAUTERMINAL pour les comptes, codes email, paiements Stripe, abonnements, accès au terminal et sécurité." data-i18n-content="support_description">
    <link rel="canonical" href="{canonical}">
    <meta name="robots" content="index,follow">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="XAUTERMINAL">
    <meta property="og:title" content="Support XAUTERMINAL" data-i18n-content="support_title">
    <meta property="og:description" content="Aide XAUTERMINAL pour les comptes, codes email, paiements Stripe, abonnements, accès au terminal et sécurité." data-i18n-content="support_description">
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
        <nav class="landing-nav-actions" aria-label="Navigation support">
            <a href="/#pricing" data-i18n="nav_pricing">Formules</a>
            <a href="/account" data-i18n="nav_account">Mon compte</a>
            <a href="/ressources" data-i18n="nav_resources">Ressources</a>
            <button type="button" class="landing-lang" data-lang-toggle>EN</button>
        </nav>
    </header>

    <main class="legal-page support-page">
        <div class="landing-kicker" data-i18n="support_kicker">SUPPORT</div>
        <h1 data-i18n="support_h1">Aide et support XAUTERMINAL</h1>
        <p data-i18n="support_intro">Retrouve les réponses aux situations les plus fréquentes: validation email, accès au terminal, paiement Stripe, abonnement, mot de passe et sécurité du compte.</p>

        <section class="support-quick-actions" aria-label="Actions rapides">
            <a class="resource-cta" href="/account" data-i18n="support_action_account">Ouvrir mon compte</a>
            <a class="resource-link-button" href="/#pricing" data-i18n="support_action_plans">Voir les formules</a>
            <a class="resource-link-button" href="/reset-password" data-i18n="support_action_password">Réinitialiser mon mot de passe</a>
        </section>

        <section class="support-grid" aria-label="Questions fréquentes">
{card_html}
        </section>

        <section class="support-process">
            <h2 data-i18n="support_process_title">Avant de contacter le support</h2>
            <ol>
                <li data-i18n="support_process_1">Vérifie que ton email est bien confirmé avec le dernier code reçu.</li>
                <li data-i18n="support_process_2">Si tu as payé, reconnecte-toi puis ouvre ton espace Mon compte pour relancer la synchronisation automatique.</li>
                <li data-i18n="support_process_3">Si l'accès reste bloqué, contacte le support avec ton email de compte et, si possible, l'heure du paiement Stripe.</li>
            </ol>
        </section>

        <section class="legal-contact">
            <h2 data-i18n="support_contact_title">Contacter XAUTERMINAL</h2>
            <p><span data-i18n="support_contact_copy">Pour une demande compte, paiement ou accès terminal, écris-nous à</span> <a href="mailto:{email}">{email}</a>.</p>
        </section>
    </main>

    <footer class="landing-footer">
        <div>
            <strong>XAUTERMINAL</strong>
            <span data-i18n="footer_tagline">Terminal macro et trading professionnel. Outil d'information, pas un conseil financier.</span>
        </div>
        <nav aria-label="Support et documents">
            <a href="/support" data-i18n="nav_support">Support</a>
            <a href="/ressources" data-i18n="nav_resources">Ressources</a>
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
            <a href="/support" data-i18n="nav_support">Support</a>
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


@router.head("/")
async def index_head():
    return FastAPIResponse(status_code=200)


@router.get("/terminal", response_class=HTMLResponse)
async def terminal():
    return FileResponse("templates/index.html", headers={"X-Robots-Tag": "noindex, follow"})


@router.head("/terminal")
async def terminal_head():
    return FastAPIResponse(status_code=200, headers={"X-Robots-Tag": "noindex, follow"})


@router.get("/account", response_class=HTMLResponse)
async def account_page():
    return FileResponse("templates/account.html")


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page():
    return FileResponse("templates/reset_password.html")


@router.get("/ressources", response_class=HTMLResponse)
async def resources_index_page():
    return HTMLResponse(resources_page())


@router.get("/guides", response_class=HTMLResponse)
async def guides_index_page():
    return HTMLResponse(guides_page())


@router.get("/support", response_class=HTMLResponse)
async def support_index_page():
    return HTMLResponse(support_page())


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


@router.get("/guides/routine-trading-xauusd", response_class=HTMLResponse)
async def routine_trading_xauusd_page():
    return HTMLResponse(content_page("routine_trading_xauusd"))


@router.get("/guides/dxy-taux-us-or", response_class=HTMLResponse)
async def dxy_taux_us_or_page():
    return HTMLResponse(content_page("dxy_taux_or"))


@router.get("/guides/bias-desk-trading", response_class=HTMLResponse)
async def bias_desk_trading_page():
    return HTMLResponse(content_page("bias_desk"))


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
        ("/support", "weekly", "0.7"),
        ("/ressources", "weekly", "0.8"),
        ("/guides", "weekly", "0.8"),
        ("/terminal-xauusd", "weekly", "0.8"),
        ("/calendrier-economique-or", "weekly", "0.8"),
        ("/news-forex-or", "weekly", "0.8"),
        ("/guide/trading-or-macro", "weekly", "0.8"),
        ("/guides/routine-trading-xauusd", "weekly", "0.8"),
        ("/guides/dxy-taux-us-or", "weekly", "0.8"),
        ("/guides/bias-desk-trading", "weekly", "0.8"),
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


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.head("/healthz")
async def healthz_head():
    return FastAPIResponse(status_code=200)


@router.get("/db-test")
def db_test(request: Request):
    require_owner(request)
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()

        return {"database": "ok", "result": result[0]}
    except Exception:
        return {"database": "error"}
