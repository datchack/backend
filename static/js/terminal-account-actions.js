import { confirmAccountEmail, fetchAccount, submitAccountAuth } from './terminal-account-api.js';
import { setAccessAuthMessage } from './terminal-account-ui.js';

function readCredentials(emailId, passwordId) {
    const emailEl = document.getElementById(emailId);
    const passwordEl = document.getElementById(passwordId);
    if (!emailEl || !passwordEl) return null;

    const email = emailEl.value.trim().toLowerCase();
    const password = passwordEl.value;
    if (!email || !password) return null;

    return { email, password, emailEl, passwordEl };
}

function readEmail(emailId) {
    const emailEl = document.getElementById(emailId);
    if (!emailEl) return null;

    const email = emailEl.value.trim().toLowerCase();
    if (!email) return null;

    return { email, emailEl };
}

export async function fetchAccountState({
    setAccountState,
    getAccountState,
    applyLoadedPrefs,
    renderAccountState,
    hasTerminalAccess,
    bootTerminalApp,
}) {
    try {
        const payload = await fetchAccount();
        setAccountState({ ...payload, loading: false });
        const accountState = getAccountState();
        if (accountState.authenticated && accountState.account?.prefs) {
            applyLoadedPrefs(accountState.account.prefs);
        }
        renderAccountState();
        if (hasTerminalAccess()) {
            bootTerminalApp();
        }
    } catch (error) {
        console.error(error);
        setAccountState({ authenticated: false, account: null, loading: false });
        renderAccountState();
    }
}

export async function submitAccessAuthForm(event, {
    getAccessFormMode,
    setAccessFormMode,
    setAccountState,
    renderAccountState,
    syncPreferences,
    hasTerminalAccess,
    bootTerminalApp,
    renderAccessGate,
}) {
    event.preventDefault();

    const accessFormMode = getAccessFormMode();
    const identity = accessFormMode === 'confirm'
        ? readEmail('access-auth-email')
        : readCredentials('access-auth-email', 'access-auth-password');
    if (!identity) return;
    const { email, emailEl } = identity;
    const password = 'password' in identity ? identity.password : '';
    const passwordEl = 'passwordEl' in identity ? identity.passwordEl : null;
    const codeEl = document.getElementById('access-auth-code');
    const code = codeEl ? codeEl.value.trim() : '';

    try {
        let payload;
        if (accessFormMode === 'confirm') {
            setAccessAuthMessage('Confirmation du code en cours...');
            payload = await confirmAccountEmail(email, code);
        } else {
            setAccessAuthMessage(accessFormMode === 'login' ? 'Connexion en cours...' : 'Creation du compte...');
            const endpoint = accessFormMode === 'login' ? 'login' : 'register';
            payload = await submitAccountAuth(endpoint, email, password);
        }

        setAccountState({ ...payload, loading: false });
        renderAccountState();
        setAccessAuthMessage(
            accessFormMode === 'login'
                ? 'Connexion reussie.'
                : accessFormMode === 'confirm'
                ? 'Email confirme. Choisis une formule Stripe pour demarrer ton essai.'
                : 'Compte cree. Un code de confirmation a ete envoye.',
            'ok',
        );
        await syncPreferences();
        emailEl.value = '';
        if (passwordEl) passwordEl.value = '';
        if (codeEl) codeEl.value = '';

        if (payload?.pending) {
            setAccessFormMode('confirm');
            renderAccessGate();
            return;
        }

        if (hasTerminalAccess()) {
            bootTerminalApp();
            setAccessFormMode('intro');
            renderAccessGate();
        }
    } catch (error) {
        setAccessAuthMessage(error.message || 'Erreur compte', 'err');
    }
}
