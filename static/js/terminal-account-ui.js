export function hasTerminalAccess(accountState) {
    return !!accountState.account?.has_access;
}

export function renderAccessGate(accountState, accessFormMode) {
    const gate = document.getElementById('access-gate');
    const title = document.getElementById('access-title');
    const copy = document.getElementById('access-copy');
    const intro = document.getElementById('access-intro');
    const auth = document.getElementById('access-auth');
    if (!gate || !title || !copy || !intro || !auth) return;

    if (accountState.loading) {
        document.body.classList.remove('gated');
        gate.classList.add('hidden');
        return;
    }

    const authenticated = !!accountState.authenticated;
    const role = accountState.account?.role || 'guest';
    const gated = !hasTerminalAccess(accountState);

    document.body.classList.toggle('gated', gated);
    gate.classList.toggle('hidden', !gated);
    intro.classList.toggle('hidden', accessFormMode !== 'intro');
    auth.classList.toggle('hidden', accessFormMode === 'intro');

    if (!gated) return;

    if (!authenticated) {
        title.textContent = 'Active ton essai gratuit 7 jours';
        copy.textContent = 'Accede au terminal complet, personnalise ton workspace et centralise news, calendrier et charting en un seul endroit.';
        return;
    }

    if (role === 'pending') {
        title.textContent = 'Confirme ton adresse email';
        copy.textContent = 'Saisis le code recu par email, puis choisis une formule Stripe pour demarrer ton essai.';
        return;
    }

    if (role === 'confirmed') {
        title.textContent = 'Choisis une formule pour demarrer ton essai';
        copy.textContent = 'Ton email est confirme. L’acces terminal s’ouvre apres le passage par Stripe.';
        return;
    }

    if (role === 'expired') {
        title.textContent = 'Ton essai est termine';
        copy.textContent = 'Reconnecte le terminal complet en passant a l’abonnement quand tu seras pret.';
        return;
    }

    title.textContent = 'Complete ton acces';
    copy.textContent = 'Ce terminal complet est reserve aux comptes en essai, abonnes ou owner.';
}

export function setAccessAuthMessage(message = '', tone = '') {
    const el = document.getElementById('access-auth-message');
    if (!el) return;
    el.textContent = message;
    el.className = `access-auth-message${tone ? ` ${tone}` : ''}`;
}

export function setAccessFormMode(mode, accountState) {
    const accessFormMode = mode === 'login' ? 'login' : mode === 'confirm' ? 'confirm' : mode === 'register' ? 'register' : 'intro';

    const kicker = document.getElementById('access-auth-kicker');
    const title = document.getElementById('access-auth-title');
    const copy = document.getElementById('access-auth-copy');
    const submit = document.getElementById('access-auth-submit');
    const switchBtn = document.getElementById('access-auth-switch');
    const password = document.getElementById('access-auth-password');
    const codeInput = document.getElementById('access-auth-code');

    if (accessFormMode === 'intro') {
        renderAccessGate(accountState, accessFormMode);
        return accessFormMode;
    }

    if (kicker) kicker.textContent = accessFormMode === 'login' ? 'CONNEXION' : accessFormMode === 'confirm' ? 'CONFIRMATION EMAIL' : 'CREATION DE COMPTE';
    if (title) title.textContent = accessFormMode === 'login' ? 'Reconnecte-toi au terminal' : accessFormMode === 'confirm' ? 'Confirme ton adresse email' : 'Active ton essai maintenant';
    if (copy) copy.textContent = accessFormMode === 'login'
        ? 'Connecte-toi pour retrouver ton workspace et tes preferences.'
        : accessFormMode === 'confirm'
        ? 'Saisis le code recu par email pour activer ton essai gratuit.'
        : 'Cree ton compte pour ouvrir le terminal complet pendant 7 jours.';
    if (submit) submit.textContent = accessFormMode === 'login' ? 'SE CONNECTER' : accessFormMode === 'confirm' ? 'VALIDER LE CODE' : 'CREER MON COMPTE';
    if (switchBtn) switchBtn.textContent = accessFormMode === 'login' ? 'CREER UN COMPTE' : "J'AI DEJA UN COMPTE";
    if (password) {
        password.style.display = accessFormMode === 'confirm' ? 'none' : '';
        password.required = accessFormMode !== 'confirm';
        password.autocomplete = accessFormMode === 'login' ? 'current-password' : 'new-password';
    }
    if (codeInput) {
        codeInput.style.display = accessFormMode === 'confirm' ? '' : 'none';
        codeInput.required = accessFormMode === 'confirm';
    }

    renderAccessGate(accountState, accessFormMode);

    const email = document.getElementById('access-auth-email');
    if (email) {
        window.setTimeout(() => email.focus(), 30);
    }

    return accessFormMode;
}

export function renderAccountState(accountState, accountMode, accessFormMode) {
    const toggle = document.getElementById('account-toggle');
    if (!toggle) return accountMode;

    if (!accountState.authenticated || !accountState.account) {
        toggle.textContent = 'CONNEXION';
        renderAccessGate(accountState, accessFormMode);
        return accountMode;
    }

    toggle.textContent = 'MON COMPTE';
    renderAccessGate(accountState, accessFormMode);
    return accountMode;
}

export function bindAccountControls({
    getAccountState,
    getAccessFormMode,
    setAccessFormModeState,
    renderAccount,
    submitAccessAuthForm,
}) {
    const toggle = document.getElementById('account-toggle');
    const startTrialBtn = document.getElementById('access-start-trial');
    const loginBtn = document.getElementById('access-login');
    const accessForm = document.getElementById('access-auth-form');
    const accessSwitchBtn = document.getElementById('access-auth-switch');
    const accessBackBtn = document.getElementById('access-back');

    if (toggle) {
        toggle.addEventListener('click', () => {
            if (getAccountState().authenticated) {
                window.location.href = '/account';
                return;
            }
            setAccessFormModeState(setAccessFormMode('login', getAccountState()));
            setAccessAuthMessage('');
        });
    }
    if (startTrialBtn) {
        startTrialBtn.addEventListener('click', () => {
            setAccessFormModeState(setAccessFormMode('register', getAccountState()));
            setAccessAuthMessage('');
        });
    }
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            setAccessFormModeState(setAccessFormMode('login', getAccountState()));
            setAccessAuthMessage('');
        });
    }
    if (accessForm) accessForm.addEventListener('submit', submitAccessAuthForm);
    if (accessSwitchBtn) {
        accessSwitchBtn.addEventListener('click', () => {
            const nextMode = getAccessFormMode() === 'login' ? 'register' : 'login';
            setAccessFormModeState(setAccessFormMode(nextMode, getAccountState()));
            setAccessAuthMessage('');
        });
    }
    if (accessBackBtn) {
        accessBackBtn.addEventListener('click', () => {
            setAccessFormModeState(setAccessFormMode('intro', getAccountState()));
            setAccessAuthMessage('');
        });
    }

    renderAccount();
    setAccessFormModeState(setAccessFormMode('intro', getAccountState()));
    renderAccessGate(getAccountState(), getAccessFormMode());
}
