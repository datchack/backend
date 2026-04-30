let landingAuthMode = 'register';
let landingLang = localStorage.getItem('xt_lang') || 'fr';
let selectedBillingPlan = null;

const LANDING_COPY = {
    fr: {
        meta_title: 'XAUTERMINAL - Terminal macro et trading professionnel',
        nav_tools: 'Outils',
        nav_markets: 'Marchés',
        nav_pricing: 'Formules',
        nav_login: 'Connexion',
        nav_terminal: 'Ouvrir le terminal',
        hero_kicker: 'TRADING TERMINAL',
        hero_copy: 'Un poste de travail macro pour suivre les news, le calendrier économique, les drivers de marché et tes charts dans une interface rapide, personnalisable et orientée décision.',
        hero_trial: "Démarrer l'essai 7 jours",
        hero_login: "J'ai déjà un compte",
        preview_volatility: 'Volatilité attendue',
        features_kicker: 'OUTILS',
        features_title: 'Tout ce qui compte avant une décision de marché.',
        feature_calendar_title: 'Calendrier économique intelligent',
        feature_calendar_copy: 'Événements classés par jour, impact, pays et données actual/forecast/previous avec lecture visuelle du résultat.',
        feature_news_title: 'News multi-source filtrées',
        feature_news_copy: 'Le feed priorise les informations récentes selon ton profil de marché: Fed, BoJ, inflation, géopolitique, indices ou crypto.',
        feature_workspace_title: 'Workspace personnalisable',
        feature_workspace_copy: 'Layouts sauvegardés, panels redimensionnables, alertes sonores, watchlist et symboles TradingView adaptés à ton trading.',
        feature_bias_copy: "Un tableau de lecture rapide pour comprendre les pressions macro dominantes avant d'entrer en position.",
        profiles_kicker: 'PROFILS DE MARCHÉ',
        profiles_title: "Un terminal qui s'adapte au marché que tu trades.",
        pricing_kicker: 'FORMULES',
        pricing_title: 'Teste le terminal, puis choisis le rythme qui te convient.',
        pricing_copy: "Chaque compte démarre avec 7 jours d'essai. Ensuite, l'accès reste simple: mensuel, annuel ou lifetime pour les premiers utilisateurs.",
        pricing_monthly_label: 'Mensuel',
        pricing_monthly_period: '/ mois',
        pricing_monthly_copy: 'Pour tester sérieusement le terminal sans engagement long.',
        pricing_yearly_label: 'Annuel',
        pricing_yearly_period: '/ an',
        pricing_yearly_copy: "L'accès complet avec un prix plus avantageux pour l'utiliser toute l'année.",
        pricing_lifetime_label: 'Lifetime',
        pricing_lifetime_period: 'une fois',
        pricing_lifetime_copy: 'Un accès à vie pensé comme offre fondateur, limité tant que le produit se construit.',
        pricing_best_value: 'Meilleur choix',
        pricing_choose: 'Choisir cette formule',
        cta_title: 'Construis ton poste de décision macro.',
        cta_copy: 'Active ton essai gratuit et teste le terminal complet avec ton propre profil de marché.',
        cta_button: 'Créer mon compte',
        auth_register_kicker: 'CRÉATION DE COMPTE',
        auth_login_kicker: 'CONNEXION',
        auth_register_title: "Démarrer l'essai 7 jours",
        auth_login_title: 'Connexion au terminal',
        auth_register_copy: 'Crée ton compte pour ouvrir le terminal complet et sauvegarder ton workspace.',
        auth_login_copy: 'Connecte-toi pour reprendre ton workspace.',
        auth_register_submit: 'Créer mon compte',
        auth_login_submit: 'Se connecter',
        auth_register_switch: "J'ai déjà un compte",
        auth_login_switch: 'Créer un compte',
        password_placeholder: 'Mot de passe (8 caractères min.)',
        auth_loading_login: 'Connexion...',
        auth_loading_register: 'Création du compte...',
        auth_no_access: 'Compte connecté, mais accès terminal indisponible.',
        auth_success: 'Accès valide. Ouverture du terminal...',
        billing_redirect: 'Redirection vers le paiement...',
        billing_error: 'Paiement indisponible',
        auth_existing_account: 'Compte déjà existant. Connecte-toi pour reprendre le paiement.',
        auth_error: 'Erreur compte',
        terms_title: 'Conditions générales d\'utilisation',
        terms_kicker: 'CGU',
        privacy_title: 'Politique de confidentialité',
        privacy_kicker: 'CONFIDENTIALITÉ',
        risk_title: 'Disclaimer trading et risques',
        risk_kicker: 'RISQUES',
        legal_updated: 'Dernière mise à jour :',
        legal_general: 'Informations générales',
        legal_editor: 'Éditeur',
        legal_business: 'Entreprise',
        legal_id: 'Identifiant',
        legal_contact: 'Contact',
        legal_address: 'Adresse',
        legal_hosting: 'Hébergement',
        legal_contact_title: 'Contact',
        legal_contact_copy: 'Pour toute question relative aux conditions d\'utilisation, à la confidentialité ou aux risques liés au trading, vous pouvez nous contacter à',
        terms_section1_title: 'Objet du service',
        terms_section1: 'XAUTERMINAL propose un terminal web d\'information macro et marché permettant de consulter des news, un calendrier économique, des graphiques, des watchlists, des widgets de prix et des outils de lecture de contexte. Le service est fourni comme outil d\'aide à l\'organisation et à l\'analyse personnelle.',
        terms_section2_title: 'Accès au service',
        terms_section2: 'L\'accès complet peut être soumis à la création d\'un compte, à une période d\'essai, à un abonnement ou à une offre lifetime. L\'utilisateur s\'engage à fournir des informations exactes et à préserver la confidentialité de ses identifiants.',
        terms_section3_title: 'Essai gratuit et abonnements',
        terms_section3: 'Les formules mensuelle et annuelle peuvent inclure un essai gratuit de 7 jours. Selon la configuration Stripe, une carte bancaire peut être demandée au démarrage de l\'essai afin de préparer le renouvellement. À l\'issue de l\'essai, l\'abonnement choisi peut démarrer automatiquement si le paiement est validé. L\'offre lifetime correspond à un paiement unique donnant accès au service tant que celui-ci est exploité.',
        terms_section4_title: 'Paiement',
        terms_section4: 'Les paiements sont traités par Stripe. XAUTERMINAL ne stocke pas les numéros de carte bancaire. Les factures, moyens de paiement, renouvellements et éventuels échecs de paiement sont gérés via Stripe et les systèmes associés.',
        terms_section5_title: 'Utilisation acceptable',
        terms_section5: 'L\'utilisateur s\'engage à ne pas perturber le service, contourner les restrictions d\'accès, partager un compte de manière abusive, extraire massivement les données ou utiliser le service à des fins illicites.',
        terms_section6_title: 'Disponibilité',
        terms_section6: 'Le service dépend de fournisseurs tiers, notamment hébergement, données de marché, flux d\'actualité, calendrier économique, graphiques et paiement. Des interruptions, retards, erreurs ou indisponibilités peuvent survenir.',
        terms_section7_title: 'Responsabilité',
        terms_section7: 'XAUTERMINAL ne garantit pas l\'exactitude, l\'exhaustivité, l\'actualité ou la continuité des données affichées. L\'utilisateur reste seul responsable de ses décisions, notamment financières, et de sa gestion du risque.',
        terms_section8_title: 'Modification du service',
        terms_section8: 'Les fonctionnalités, tarifs, offres, sources de données et conditions peuvent évoluer afin d\'améliorer le produit, corriger des erreurs ou tenir compte de contraintes techniques ou commerciales.',
        privacy_section1_title: 'Données collectées',
        privacy_section1: 'XAUTERMINAL peut collecter l\'adresse email, le mot de passe chiffré, les préférences de terminal, l\'état d\'abonnement, les identifiants Stripe nécessaires au suivi du paiement et des données techniques liées à l\'utilisation du service.',
        privacy_section2_title: 'Finalités',
        privacy_section2: 'Ces données servent à créer et sécuriser le compte, gérer l\'accès au terminal, synchroniser les préférences, traiter les abonnements, améliorer le produit et assurer le support utilisateur.',
        privacy_section3_title: 'Paiements',
        privacy_section3: 'Les données de paiement sont traitées par Stripe. XAUTERMINAL conserve uniquement les références techniques utiles au suivi du compte, comme l\'identifiant client, l\'abonnement, le prix sélectionné ou le statut de paiement.',
        privacy_section4_title: 'Cookies et sessions',
        privacy_section4: 'Le service utilise un cookie de session afin de maintenir la connexion au compte. Des préférences peuvent également être conservées localement dans le navigateur pour personnaliser l\'expérience.',
        privacy_section5_title: 'Prestataires',
        privacy_section5: 'Le service peut s\'appuyer sur des prestataires techniques comme Render pour l\'hébergement, Stripe pour le paiement, Financial Modeling Prep, Yahoo Finance, TradingView ou des flux RSS tiers pour les données et l\'affichage.',
        privacy_section6_title: 'Durée de conservation',
        privacy_section6: 'Les données de compte sont conservées tant que le compte existe ou tant que cela est nécessaire pour fournir le service, respecter des obligations légales, gérer un litige ou assurer la sécurité.',
        privacy_section7_title: 'Droits utilisateur',
        privacy_section7: 'L\'utilisateur peut demander l\'accès, la correction ou la suppression de ses données en contactant l\'adresse indiquée sur cette page. Certaines données peuvent être conservées si une obligation légale ou technique l\'impose.',
        privacy_section8_title: 'Sécurité',
        privacy_section8: 'XAUTERMINAL applique des mesures raisonnables pour protéger les comptes et les données. Aucun système n\'étant infaillible, l\'utilisateur doit choisir un mot de passe robuste et éviter de le réutiliser.',
        risk_section1_title: 'Information uniquement',
        risk_section1: 'XAUTERMINAL fournit des informations de marché, des outils de visualisation, des classements, des alertes et des lectures de contexte. Le service ne constitue pas un conseil en investissement, une recommandation personnalisée, une gestion de portefeuille, ou une incitation à acheter ou vendre un instrument financier.',
        risk_section2_title: 'Risque de perte',
        risk_section2: 'Le trading, les CFD, le Forex, les cryptomonnaies, les actions, les indices, les matières premières et autres instruments financiers comportent un risque élevé de perte. Les performances passées ne préjugent pas des performances futures.',
        risk_section3_title: 'Données tierces',
        risk_section3: 'Les prix, news, calendriers économiques, impacts, prévisions, données actual/forecast/previous et graphiques peuvent provenir de fournisseurs tiers. Ces informations peuvent être retardées, erronées, incomplètes ou indisponibles.',
        risk_section4_title: 'Bias Desk',
        risk_section4: 'Le Bias Desk et les indicateurs associés sont des outils de lecture mécanique et contextuelle. Ils ne doivent pas être interprétés comme des signaux automatiques ou comme une garantie de résultat.',
        risk_section5_title: 'Responsabilité de l\'utilisateur',
        risk_section5: 'Chaque utilisateur doit effectuer ses propres vérifications, respecter son plan de trading, adapter la taille de ses positions et ne jamais engager de capitaux qu\'il ne peut pas se permettre de perdre.',
        risk_section6_title: 'Aucune garantie',
        risk_section6: 'XAUTERMINAL ne garantit aucun gain, aucune précision parfaite des données, aucune disponibilité continue et aucune adéquation du service à une situation financière particulière.',
    },
    en: {
        meta_title: 'XAUTERMINAL - Professional macro and trading terminal',
        nav_tools: 'Tools',
        nav_markets: 'Markets',
        nav_pricing: 'Plans',
        nav_login: 'Login',
        nav_terminal: 'Open terminal',
        hero_kicker: 'TRADING TERMINAL',
        hero_copy: 'A macro workstation to track news, the economic calendar, market drivers and your charts in a fast, customizable, decision-focused interface.',
        hero_trial: 'Start 7-day trial',
        hero_login: 'I already have an account',
        preview_volatility: 'Expected volatility',
        features_kicker: 'TOOLS',
        features_title: 'Everything that matters before a market decision.',
        feature_calendar_title: 'Smart economic calendar',
        feature_calendar_copy: 'Events organized by day, impact and country, with actual/forecast/previous data and visual result reading.',
        feature_news_title: 'Filtered multi-source news',
        feature_news_copy: 'The feed prioritizes recent information for your market profile: Fed, BoJ, inflation, geopolitics, indices or crypto.',
        feature_workspace_title: 'Customizable workspace',
        feature_workspace_copy: 'Saved layouts, resizable panels, sound alerts, watchlists and TradingView symbols adapted to your trading.',
        feature_bias_copy: 'A fast reading desk to understand dominant macro pressure before taking a trade.',
        profiles_kicker: 'MARKET PROFILES',
        profiles_title: 'A terminal that adapts to the market you trade.',
        pricing_kicker: 'PLANS',
        pricing_title: 'Try the terminal, then choose the rhythm that fits you.',
        pricing_copy: 'Every account starts with a 7-day trial. After that, access stays simple: monthly, yearly or lifetime for early users.',
        pricing_monthly_label: 'Monthly',
        pricing_monthly_period: '/ month',
        pricing_monthly_copy: 'For testing the terminal seriously without a long commitment.',
        pricing_yearly_label: 'Yearly',
        pricing_yearly_period: '/ year',
        pricing_yearly_copy: 'Full access with a better price if you use it all year.',
        pricing_lifetime_label: 'Lifetime',
        pricing_lifetime_period: 'one time',
        pricing_lifetime_copy: 'Lifetime access as a founder offer, limited while the product is still being built.',
        pricing_best_value: 'Best value',
        pricing_choose: 'Choose this plan',
        cta_title: 'Build your macro decision desk.',
        cta_copy: 'Start your free trial and test the full terminal with your own market profile.',
        cta_button: 'Create my account',
        auth_register_kicker: 'ACCOUNT CREATION',
        auth_login_kicker: 'LOGIN',
        auth_register_title: 'Start your 7-day trial',
        auth_login_title: 'Login to the terminal',
        auth_register_copy: 'Create your account to open the full terminal and save your workspace.',
        auth_login_copy: 'Login to resume your workspace.',
        auth_register_submit: 'Create my account',
        auth_login_submit: 'Login',
        auth_register_switch: 'I already have an account',
        auth_login_switch: 'Create an account',
        password_placeholder: 'Password (8 characters min.)',
        auth_loading_login: 'Logging in...',
        auth_loading_register: 'Creating account...',
        auth_no_access: 'Account connected, but terminal access is unavailable.',
        auth_success: 'Access valid. Opening terminal...',
        billing_redirect: 'Redirecting to payment...',
        billing_error: 'Payment unavailable',
        auth_existing_account: 'Account already exists. Log in to resume payment.',
        auth_error: 'Account error',
        terms_title: 'Terms and Conditions',
        terms_kicker: 'TERMS',
        privacy_title: 'Privacy Policy',
        privacy_kicker: 'PRIVACY',
        risk_title: 'Trading Disclaimer and Risks',
        risk_kicker: 'RISKS',
        legal_updated: 'Last updated:',
        legal_general: 'General Information',
        legal_editor: 'Editor',
        legal_business: 'Business',
        legal_id: 'Identifier',
        legal_contact: 'Contact',
        legal_address: 'Address',
        legal_hosting: 'Hosting',
        legal_contact_title: 'Contact',
        legal_contact_copy: 'For any questions regarding terms of use, privacy, or trading risks, please contact us at',
        terms_section1_title: 'Service Purpose',
        terms_section1: 'XAUTERMINAL provides a web terminal for macro and market information, allowing users to view news, economic calendar, charts, watchlists, price widgets and context reading tools. The service is provided as a personal analysis and organization aid tool.',
        terms_section2_title: 'Service Access',
        terms_section2: 'Full access may require account creation, trial period, subscription or lifetime offer. Users agree to provide accurate information and keep their credentials confidential.',
        terms_section3_title: 'Free Trial and Subscriptions',
        terms_section3: 'Monthly and yearly plans may include a 7-day free trial. Depending on Stripe configuration, a credit card may be required at trial start to set up renewal. After the trial, the chosen subscription may start automatically if payment is validated. Lifetime offer is a single payment giving access to the service while it exists.',
        terms_section4_title: 'Payment',
        terms_section4: 'Payments are processed by Stripe. XAUTERMINAL does not store credit card numbers. Invoices, payment methods, renewals and payment failures are managed by Stripe and associated systems.',
        terms_section5_title: 'Acceptable Use',
        terms_section5: 'Users agree not to disrupt the service, bypass access restrictions, abusively share an account, mass extract data or use the service for unlawful purposes.',
        terms_section6_title: 'Availability',
        terms_section6: 'The service depends on third-party providers, including hosting, market data, news feeds, economic calendar, charts and payment. Interruptions, delays, errors or unavailability may occur.',
        terms_section7_title: 'Liability',
        terms_section7: 'XAUTERMINAL does not guarantee accuracy, completeness, timeliness or continuity of displayed data. Users are solely responsible for their decisions, including financial, and risk management.',
        terms_section8_title: 'Service Modification',
        terms_section8: 'Features, pricing, offers, data sources and conditions may change to improve the product, fix errors or address technical or commercial constraints.',
        privacy_section1_title: 'Data Collected',
        privacy_section1: 'XAUTERMINAL may collect email address, encrypted password, terminal preferences, subscription status, Stripe identifiers needed for payment tracking and technical data related to service usage.',
        privacy_section2_title: 'Purposes',
        privacy_section2: 'This data is used to create and secure accounts, manage terminal access, sync preferences, process subscriptions, improve the product and provide user support.',
        privacy_section3_title: 'Payments',
        privacy_section3: 'Payment data is processed by Stripe. XAUTERMINAL only keeps technical references useful for account tracking, such as customer ID, subscription, selected price or payment status.',
        privacy_section4_title: 'Cookies and Sessions',
        privacy_section4: 'The service uses session cookies to maintain account connection. Preferences may also be stored locally in the browser to customize experience.',
        privacy_section5_title: 'Service Providers',
        privacy_section5: 'The service may rely on technical providers like Render for hosting, Stripe for payment, Financial Modeling Prep, Yahoo Finance, TradingView or third-party RSS feeds for data and display.',
        privacy_section6_title: 'Data Retention',
        privacy_section6: 'Account data is retained as long as the account exists or as necessary to provide the service, meet legal obligations, manage disputes or ensure security.',
        privacy_section7_title: 'User Rights',
        privacy_section7: 'Users can request access, correction or deletion of their data by contacting the address listed on this page. Some data may be retained if required by law or technical necessity.',
        privacy_section8_title: 'Security',
        privacy_section8: 'XAUTERMINAL applies reasonable measures to protect accounts and data. Since no system is infallible, users should choose a strong password and avoid reuse.',
        risk_section1_title: 'Information Only',
        risk_section1: 'XAUTERMINAL provides market information, visualization tools, rankings, alerts and context reading. The service is not investment advice, personalized recommendations, portfolio management, or encouragement to buy or sell any financial instrument.',
        risk_section2_title: 'Loss Risk',
        risk_section2: 'Trading, CFDs, Forex, cryptocurrencies, stocks, indices, commodities and other financial instruments carry high loss risk. Past performance does not guarantee future results.',
        risk_section3_title: 'Third-Party Data',
        risk_section3: 'Prices, news, economic calendars, impacts, forecasts, actual/previous data and charts may come from third parties. This information may be delayed, inaccurate, incomplete or unavailable.',
        risk_section4_title: 'Bias Desk',
        risk_section4: 'The Bias Desk and associated indicators are mechanical and contextual reading tools. They should not be interpreted as automatic signals or performance guarantees.',
        risk_section5_title: 'User Responsibility',
        risk_section5: 'Each user must perform their own verification, follow their trading plan, size positions appropriately and never commit capital they cannot afford to lose.',
        risk_section6_title: 'No Warranty',
        risk_section6: 'XAUTERMINAL makes no warranty of any gain, perfect data accuracy, continuous availability or suitability for any particular financial situation.',
    },
};

function t(key) {
    return LANDING_COPY[landingLang]?.[key] || LANDING_COPY.fr[key] || key;
}

function applyLandingLanguage() {
    document.documentElement.lang = landingLang;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
        el.placeholder = t(el.dataset.i18nPlaceholder);
    });

    const title = document.querySelector('title');
    if (title) {
        const titleKey = title.dataset.i18n || 'meta_title';
        title.textContent = titleKey === 'meta_title' ? t('meta_title') : `${t(titleKey)} - XAUTERMINAL`;
    }

    const toggle = document.querySelector('[data-lang-toggle]');
    if (toggle) toggle.textContent = landingLang === 'fr' ? 'EN' : 'FR';

    setLandingAuthMode(landingAuthMode);
}

function setLandingMessage(message = '', tone = '') {
    const el = document.getElementById('landing-auth-message');
    if (!el) return;
    el.textContent = message;
    el.className = `landing-auth-message${tone ? ` ${tone}` : ''}`;
}

function setLandingAuthMode(mode) {
    landingAuthMode = mode === 'login' ? 'login' : 'register';

    const kicker = document.getElementById('landing-auth-kicker');
    const title = document.getElementById('landing-auth-title');
    const copy = document.getElementById('landing-auth-copy');
    const submit = document.getElementById('landing-auth-submit');
    const switchBtn = document.getElementById('landing-auth-switch');
    const password = document.getElementById('landing-auth-password');

    if (kicker) kicker.textContent = landingAuthMode === 'login' ? t('auth_login_kicker') : t('auth_register_kicker');
    if (title) title.textContent = landingAuthMode === 'login' ? t('auth_login_title') : t('auth_register_title');
    if (copy) copy.textContent = landingAuthMode === 'login'
        ? t('auth_login_copy')
        : t('auth_register_copy');
    if (submit) submit.textContent = landingAuthMode === 'login' ? t('auth_login_submit') : t('auth_register_submit');
    if (switchBtn) switchBtn.textContent = landingAuthMode === 'login' ? t('auth_login_switch') : t('auth_register_switch');
    if (password) password.autocomplete = landingAuthMode === 'login' ? 'current-password' : 'new-password';
}

function openLandingAuth(mode = 'register') {
    const modal = document.getElementById('landing-auth');
    const email = document.getElementById('landing-auth-email');
    if (!modal) return;

    setLandingAuthMode(mode);
    setLandingMessage('');
    modal.classList.remove('hidden');
    window.setTimeout(() => email?.focus(), 30);
}

function closeLandingAuth() {
    const modal = document.getElementById('landing-auth');
    if (modal) modal.classList.add('hidden');
}

async function fetchLandingAccount() {
    try {
        const response = await fetch('/api/account/me', { cache: 'no-store' });
        const payload = await response.json();
        const terminalLink = document.getElementById('landing-terminal-link');
        if (terminalLink && payload.authenticated && payload.account?.has_access) {
            terminalLink.classList.remove('hidden');
        }
    } catch (error) {
        console.error(error);
    }
}

async function submitLandingAuth(event) {
    event.preventDefault();

    const emailEl = document.getElementById('landing-auth-email');
    const passwordEl = document.getElementById('landing-auth-password');
    if (!emailEl || !passwordEl) return;

    const email = emailEl.value.trim().toLowerCase();
    const password = passwordEl.value;
    if (!email || !password) return;

    try {
        setLandingMessage(landingAuthMode === 'login' ? t('auth_loading_login') : t('auth_loading_register'));
        const response = await fetch(`/api/account/${landingAuthMode}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        const payload = await response.json();
        if (!response.ok) {
            if (response.status === 409 && landingAuthMode === 'register') {
                setLandingAuthMode('login');
                setLandingMessage(payload.detail || t('auth_existing_account'), 'err');
                return;
            }
            throw new Error(payload.detail || 'Action impossible');
        }

        if (selectedBillingPlan) {
            await startBillingCheckout(selectedBillingPlan);
            return;
        }

        if (!payload.account?.has_access) {
            setLandingMessage(t('auth_no_access'), 'err');
            return;
        }

        setLandingMessage(t('auth_success'), 'ok');
        window.location.href = '/terminal';
    } catch (error) {
        setLandingMessage(error.message || t('auth_error'), 'err');
    }
}

async function startBillingCheckout(plan) {
    try {
        setLandingMessage(t('billing_redirect'));
        const response = await fetch('/api/billing/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || t('billing_error'));
        }
        window.location.href = payload.url;
    } catch (error) {
        setLandingMessage(error.message || t('billing_error'), 'err');
    }
}

async function handleBillingPlan(plan) {
    selectedBillingPlan = plan;
    try {
        const response = await fetch('/api/account/me', { cache: 'no-store' });
        const payload = await response.json();
        if (payload.authenticated) {
            await startBillingCheckout(plan);
            return;
        }
    } catch (error) {
        console.error(error);
    }
    openLandingAuth('register');
}

function bindLanding() {
    document.querySelectorAll('[data-pricing-scroll]').forEach((button) => {
        button.addEventListener('click', () => {
            selectedBillingPlan = null;
            document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    document.querySelectorAll('[data-auth-mode]').forEach((button) => {
        button.addEventListener('click', () => {
            selectedBillingPlan = null;
            openLandingAuth(button.dataset.authMode);
        });
    });

    document.querySelectorAll('[data-billing-plan]').forEach((button) => {
        button.addEventListener('click', () => handleBillingPlan(button.dataset.billingPlan));
    });

    const langToggle = document.querySelector('[data-lang-toggle]');
    if (langToggle) {
        langToggle.addEventListener('click', () => {
            landingLang = landingLang === 'fr' ? 'en' : 'fr';
            localStorage.setItem('xt_lang', landingLang);
            applyLandingLanguage();
        });
    }

    const close = document.getElementById('landing-auth-close');
    if (close) close.addEventListener('click', closeLandingAuth);

    const switchBtn = document.getElementById('landing-auth-switch');
    if (switchBtn) {
        switchBtn.addEventListener('click', () => {
            setLandingAuthMode(landingAuthMode === 'login' ? 'register' : 'login');
            setLandingMessage('');
        });
    }

    const form = document.getElementById('landing-auth-form');
    if (form) form.addEventListener('submit', submitLandingAuth);

    const modal = document.getElementById('landing-auth');
    if (modal) {
        modal.addEventListener('click', (event) => {
            if (event.target === modal) closeLandingAuth();
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    applyLandingLanguage();
    bindLanding();
    fetchLandingAccount();
});
