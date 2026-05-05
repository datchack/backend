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

export function setAccountMessage(message = '', tone = '') {
    const messageEl = document.getElementById('account-message');
    if (!messageEl) return;
    messageEl.textContent = message;
    messageEl.className = `account-message${tone ? ` ${tone}` : ''}`;
}

export function setAccountMode(mode) {
    const accountMode = mode === 'login' ? 'login' : 'register';

    const titleEl = document.getElementById('account-title');
    const submitEl = document.getElementById('account-submit');
    const switchEl = document.getElementById('account-switch');
    const passwordEl = document.getElementById('account-password');

    if (titleEl) titleEl.textContent = accountMode === 'login' ? 'CONNEXION' : 'ESPACE COMPTE';
    if (submitEl) submitEl.textContent = accountMode === 'login' ? 'SE CONNECTER' : 'CREER MON COMPTE';
    if (switchEl) switchEl.textContent = accountMode === 'login' ? 'CREER UN COMPTE' : "J'AI DEJA UN COMPTE";
    if (passwordEl) passwordEl.autocomplete = accountMode === 'login' ? 'current-password' : 'new-password';

    return accountMode;
}

export function renderAccountState(accountState, accountMode, accessFormMode) {
    const toggle = document.getElementById('account-toggle');
    const trial = document.getElementById('account-trial');
    const summary = document.getElementById('account-summary');
    const form = document.getElementById('account-form');
    const userBlock = document.getElementById('account-user');
    const emailValue = document.getElementById('account-email-value');
    const planValue = document.getElementById('account-plan-value');
    const expiryValue = document.getElementById('account-expiry-value');
    const adminToggle = document.getElementById('account-admin-toggle');

    if (!toggle || !trial || !summary || !form || !userBlock) return accountMode;

    if (!accountState.authenticated || !accountState.account) {
        toggle.textContent = 'ACCOUNT';
        trial.textContent = 'TRIAL 7J';
        summary.textContent = "Connecte-toi pour sauvegarder ton terminal et demarrer un essai 7 jours.";
        form.classList.remove('hidden');
        userBlock.classList.add('hidden');
        if (adminToggle) adminToggle.classList.add('hidden');
        const nextAccountMode = setAccountMode(accountMode);
        renderAccessGate(accountState, accessFormMode);
        return nextAccountMode;
    }

    const { account } = accountState;
    toggle.textContent = 'MY ACCOUNT';
    trial.textContent = account.role === 'owner'
        ? 'OWNER'
        : account.role === 'trial' ? `TRIAL ${account.trial_days_left}J` : (account.plan || 'PLAN').toUpperCase();
    summary.textContent = account.role === 'owner'
        ? 'Acces createur actif a vie. Le terminal complet reste ouvert sans limitation.'
        : account.role === 'trial'
        ? `Essai actif jusqu'au ${new Date(account.trial_ends_at).toLocaleDateString('fr-FR')}. Tes preferences sont synchronisees.`
        : 'Compte actif. Structure abonnement prete a etre branchee.';
    form.classList.add('hidden');
    userBlock.classList.remove('hidden');
    if (emailValue) emailValue.textContent = account.email;
    if (planValue) planValue.textContent = account.role === 'owner' ? 'OWNER' : String(account.plan || 'trial').toUpperCase();
    if (expiryValue) {
        expiryValue.textContent = account.role === 'owner'
            ? 'LIFETIME'
            : account.role === 'trial' ? new Date(account.trial_ends_at).toLocaleDateString('fr-FR') : 'ACCES ACTIF';
    }
    if (adminToggle) adminToggle.classList.toggle('hidden', account.role !== 'owner');
    renderAccessGate(accountState, accessFormMode);
    return accountMode;
}

export function toggleAccountPanel(accountState, forceOpen = null, heroOpen = false) {
    const panel = document.getElementById('account-panel');
    if (!panel) return;

    const shouldOpen = forceOpen === null ? panel.classList.contains('hidden') : forceOpen;
    panel.classList.toggle('hidden', !shouldOpen);
    panel.classList.toggle('hero-open', shouldOpen && heroOpen);

    if (shouldOpen) {
        const emailEl = document.getElementById('account-email');
        if (emailEl && !accountState.authenticated) {
            window.setTimeout(() => emailEl.focus(), 30);
        }
    }
}

export function bindAccountControls({
    getAccountState,
    getAccountMode,
    setAccountModeState,
    getAccessFormMode,
    setAccessFormModeState,
    renderAccount,
    submitAccountForm,
    submitAccessAuthForm,
    logoutAccount,
    openBillingPortal,
    syncPreferences,
}) {
    const toggle = document.getElementById('account-toggle');
    const form = document.getElementById('account-form');
    const switchBtn = document.getElementById('account-switch');
    const logoutBtn = document.getElementById('account-logout');
    const syncBtn = document.getElementById('account-sync');
    const billingBtn = document.getElementById('account-billing-portal');
    const adminToggle = document.getElementById('account-admin-toggle');
    const panel = document.getElementById('account-panel');
    const startTrialBtn = document.getElementById('access-start-trial');
    const loginBtn = document.getElementById('access-login');
    const accessForm = document.getElementById('access-auth-form');
    const accessSwitchBtn = document.getElementById('access-auth-switch');
    const accessBackBtn = document.getElementById('access-back');

    if (toggle) {
        toggle.addEventListener('click', () => {
            toggleAccountPanel(getAccountState(), null, false);
            renderAccount();
        });
    }
    if (form) form.addEventListener('submit', submitAccountForm);
    if (switchBtn) {
        switchBtn.addEventListener('click', () => {
            setAccountModeState(setAccountMode(getAccountMode() === 'login' ? 'register' : 'login'));
            setAccountMessage('');
        });
    }
    if (logoutBtn) logoutBtn.addEventListener('click', logoutAccount);
    if (billingBtn) billingBtn.addEventListener('click', openBillingPortal);
    if (syncBtn) {
        syncBtn.addEventListener('click', async () => {
            await syncPreferences();
            setAccountMessage('Preferences synchronisees.', 'ok');
        });
    }
    if (adminToggle) {
        adminToggle.addEventListener('click', () => {
            window.location.href = '/admin';
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

    document.addEventListener('click', (event) => {
        if (!panel || panel.classList.contains('hidden')) return;
        const slot = document.querySelector('.account-slot');
        if (slot && !slot.contains(event.target)) {
            toggleAccountPanel(getAccountState(), false, false);
        }
    });

    renderAccount();
    setAccountModeState(setAccountMode(getAccountMode()));
    setAccessFormModeState(setAccessFormMode('intro', getAccountState()));
    renderAccessGate(getAccountState(), getAccessFormMode());
}
