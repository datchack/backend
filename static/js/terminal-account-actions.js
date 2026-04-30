import { fetchAccount, logoutAccountSession, submitAccountAuth } from './terminal-account-api.js';
import { setAccessAuthMessage, setAccountMessage } from './terminal-account-ui.js';

function readCredentials(emailId, passwordId) {
    const emailEl = document.getElementById(emailId);
    const passwordEl = document.getElementById(passwordId);
    if (!emailEl || !passwordEl) return null;

    const email = emailEl.value.trim().toLowerCase();
    const password = passwordEl.value;
    if (!email || !password) return null;

    return { email, password, emailEl, passwordEl };
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

export async function submitAccountForm(event, {
    getAccountMode,
    setAccountState,
    renderAccountState,
    syncPreferences,
    hasTerminalAccess,
    bootTerminalApp,
    renderAccessGate,
    toggleAccountPanel,
}) {
    event.preventDefault();

    const credentials = readCredentials('account-email', 'account-password');
    if (!credentials) return;
    const { email, password, emailEl, passwordEl } = credentials;
    const accountMode = getAccountMode();

    try {
        setAccountMessage('Connexion en cours...');
        const payload = await submitAccountAuth(accountMode, email, password);

        setAccountState({ ...payload, loading: false });
        renderAccountState();
        setAccountMessage(accountMode === 'login' ? 'Connexion reussie.' : 'Compte cree. Essai 7 jours active.', 'ok');
        await syncPreferences();
        emailEl.value = '';
        passwordEl.value = '';
        if (hasTerminalAccess()) {
            bootTerminalApp();
            renderAccessGate();
            toggleAccountPanel(false, false);
        }
    } catch (error) {
        setAccountMessage(error.message || 'Erreur compte', 'err');
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

    const credentials = readCredentials('access-auth-email', 'access-auth-password');
    if (!credentials) return;
    const { email, password, emailEl, passwordEl } = credentials;
    const accessFormMode = getAccessFormMode();

    try {
        setAccessAuthMessage(accessFormMode === 'login' ? 'Connexion en cours...' : 'Creation du compte...');
        const endpoint = accessFormMode === 'login' ? 'login' : 'register';
        const payload = await submitAccountAuth(endpoint, email, password);

        setAccountState({ ...payload, loading: false });
        renderAccountState();
        setAccessAuthMessage(accessFormMode === 'login' ? 'Connexion reussie.' : 'Compte cree. Essai active.', 'ok');
        await syncPreferences();
        emailEl.value = '';
        passwordEl.value = '';
        if (hasTerminalAccess()) {
            bootTerminalApp();
            setAccessFormMode('intro');
            renderAccessGate();
        }
    } catch (error) {
        setAccessAuthMessage(error.message || 'Erreur compte', 'err');
    }
}

export async function logoutAccount() {
    try {
        await logoutAccountSession();
        window.location.href = '/';
    } catch (error) {
        setAccountMessage('Impossible de fermer la session.', 'err');
    }
}
