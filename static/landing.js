let landingAuthMode = 'register';

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

    if (kicker) kicker.textContent = landingAuthMode === 'login' ? 'CONNEXION' : 'CREATION DE COMPTE';
    if (title) title.textContent = landingAuthMode === 'login' ? 'Connexion au terminal' : "Demarrer l'essai 7 jours";
    if (copy) copy.textContent = landingAuthMode === 'login'
        ? 'Connecte-toi pour reprendre ton workspace.'
        : 'Cree ton compte pour ouvrir le terminal complet et sauvegarder ton workspace.';
    if (submit) submit.textContent = landingAuthMode === 'login' ? 'Se connecter' : 'Creer mon compte';
    if (switchBtn) switchBtn.textContent = landingAuthMode === 'login' ? 'Creer un compte' : "J'ai deja un compte";
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
        setLandingMessage(landingAuthMode === 'login' ? 'Connexion...' : 'Creation du compte...');
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
            setLandingMessage('Compte connecte, mais acces terminal indisponible.', 'err');
            return;
        }

        setLandingMessage('Acces valide. Ouverture du terminal...', 'ok');
        window.location.href = '/terminal';
    } catch (error) {
        setLandingMessage(error.message || 'Erreur compte', 'err');
    }
}

function bindLanding() {
    document.querySelectorAll('[data-auth-mode]').forEach((button) => {
        button.addEventListener('click', () => openLandingAuth(button.dataset.authMode));
    });

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
    bindLanding();
    fetchLandingAccount();
});
