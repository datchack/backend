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
        auth_error: 'Erreur compte',
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
        auth_error: 'Account error',
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
    if (title) title.textContent = t('meta_title');

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
            throw new Error(payload.detail || 'Action impossible');
        }

        if (!payload.account?.has_access) {
            setLandingMessage(t('auth_no_access'), 'err');
            return;
        }

        if (selectedBillingPlan) {
            await startBillingCheckout(selectedBillingPlan);
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
