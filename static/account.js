const state = {
    account: null,
};

function setText(id, value = '-') {
    const el = document.getElementById(id);
    if (el) el.textContent = value || '-';
}

function setValue(id, value = '') {
    const el = document.getElementById(id);
    if (el) el.value = value || '';
}

function setMessage(id, message = '', tone = '') {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = message;
    el.className = `account-message${tone ? ` ${tone}` : ''}`;
}

async function readJson(response) {
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.detail || 'Action impossible');
    }
    return payload;
}

function formatDate(value) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
    });
}

function shortId(value) {
    if (!value) return '-';
    if (value.length <= 18) return value;
    return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

function planLabel(account) {
    const plan = account.plan || account.role || '-';
    const labels = {
        owner: 'OWNER',
        active: 'ACTIF',
        monthly: 'MENSUEL',
        yearly: 'ANNUEL',
        lifetime: 'LIFETIME',
        trial: 'ESSAI',
    };
    return labels[plan] || String(plan).toUpperCase();
}

function accessLabel(account) {
    if (account.role === 'owner') return 'OWNER';
    if (account.status === 'past_due') return 'PAIEMENT EN RETARD';
    if (account.status === 'canceled') return 'ANNULE';
    if (account.has_access) return 'ACTIF';
    if (!account.email_confirmed) return 'EMAIL A CONFIRMER';
    if (account.status === 'confirmed') return 'PAIEMENT REQUIS';
    return String(account.status || 'INACTIF').toUpperCase();
}

function billingStateLabel(account) {
    if (account.role === 'owner') return 'Compte owner';
    if (!account.email_confirmed) return 'Email non confirme';
    if (account.stripe_customer_id && account.has_access) return 'Actif via Stripe';
    if (account.stripe_customer_id) return 'Stripe lie';
    if (account.status === 'confirmed') return 'En attente de paiement';
    return 'Non lie a Stripe';
}

function billingCopy(account) {
    if (account.stripe_customer_id && account.has_access) {
        return 'Ton abonnement est lie a Stripe. Tu peux gerer tes factures, moyens de paiement, changements de formule et annulations depuis le portail Stripe.';
    }
    if (account.email_confirmed) {
        return 'Ton email est confirme. Choisis une formule pour demarrer ton essai et lier automatiquement Stripe a ton compte XAUTERMINAL.';
    }
    return 'Confirme ton email avant de choisir une formule. Stripe gerera ensuite les moyens de paiement, factures et annulations.';
}

function fillProfile(account) {
    const profile = account.profile || {};
    setValue('profile-first-name', profile.first_name);
    setValue('profile-last-name', profile.last_name);
    setValue('profile-address-line', profile.address_line);
    setValue('profile-postal-code', profile.postal_code);
    setValue('profile-city', profile.city);
    setValue('profile-country', profile.country);
}

function updateActionStates(account) {
    const portalButton = document.getElementById('account-portal');
    const resendButton = document.getElementById('account-resend-confirmation');
    const planButtons = document.querySelectorAll('[data-account-plan]');

    if (portalButton) {
        portalButton.disabled = !account.stripe_customer_id;
        portalButton.title = account.stripe_customer_id
            ? 'Ouvrir le portail Stripe'
            : 'Un paiement Stripe doit etre lie au compte avant d ouvrir le portail';
    }

    if (resendButton) {
        resendButton.hidden = !!account.email_confirmed;
    }

    planButtons.forEach((button) => {
        button.disabled = !account.email_confirmed;
        button.title = account.email_confirmed
            ? 'Choisir cette formule via Stripe'
            : 'Confirme ton email avant de choisir une formule';
    });
}

function renderAccount(account) {
    state.account = account;

    document.getElementById('account-login-state')?.classList.add('hidden');
    document.getElementById('account-dashboard')?.classList.remove('hidden');

    const hasAccess = !!account.has_access;
    const emailConfirmed = !!account.email_confirmed;
    const statusTitle = hasAccess
        ? 'Accès terminal actif'
        : emailConfirmed
        ? 'Paiement Stripe requis'
        : 'Email à confirmer';
    const statusCopy = hasAccess
        ? 'Ton compte peut ouvrir le terminal complet. La facturation reste gérable depuis Stripe.'
        : emailConfirmed
        ? 'Ton email est confirmé. Choisis une formule pour démarrer ton essai et lier Stripe au compte.'
        : 'Confirme ton adresse email avant de choisir une formule Stripe.';

    setText('account-status-title', statusTitle);
    setText('account-status-copy', statusCopy);
    setText('account-billing-copy', billingCopy(account));
    setText('account-status-badge', accessLabel(account));
    setText('account-email', account.email);
    setText('account-plan', planLabel(account));
    setText('account-access', accessLabel(account));
    setText('account-period-end', formatDate(account.stripe_current_period_end || account.trial_ends_at));
    setText('account-billing-state', billingStateLabel(account));
    setText('account-stripe-customer', shortId(account.stripe_customer_id));
    setText('account-stripe-subscription', shortId(account.stripe_subscription_id));
    setText('account-stripe-price', shortId(account.stripe_price_id));

    fillProfile(account);
    updateActionStates(account);
}

async function fetchAccount() {
    const response = await fetch('/api/account/me', { cache: 'no-store' });
    const payload = await readJson(response);
    if (!payload.authenticated || !payload.account) {
        document.getElementById('account-login-state')?.classList.remove('hidden');
        document.getElementById('account-dashboard')?.classList.add('hidden');
        return;
    }
    renderAccount(payload.account);
}

async function saveProfile(event) {
    event.preventDefault();
    try {
        setMessage('account-message', 'Enregistrement...');
        const response = await fetch('/api/account/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                first_name: document.getElementById('profile-first-name')?.value || '',
                last_name: document.getElementById('profile-last-name')?.value || '',
                address_line: document.getElementById('profile-address-line')?.value || '',
                postal_code: document.getElementById('profile-postal-code')?.value || '',
                city: document.getElementById('profile-city')?.value || '',
                country: document.getElementById('profile-country')?.value || '',
            }),
        });
        const payload = await readJson(response);
        renderAccount(payload.account);
        setMessage('account-message', 'Profil enregistre.', 'ok');
    } catch (error) {
        setMessage('account-message', error.message || "Impossible d'enregistrer le profil.", 'err');
    }
}

async function savePassword(event) {
    event.preventDefault();
    try {
        const currentPassword = document.getElementById('password-current')?.value || '';
        const newPassword = document.getElementById('password-new')?.value || '';
        setMessage('account-password-message', 'Mise a jour...');
        const response = await fetch('/api/account/password', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });
        await readJson(response);
        document.getElementById('account-password-form')?.reset();
        setMessage('account-password-message', 'Mot de passe mis a jour.', 'ok');
    } catch (error) {
        setMessage('account-password-message', error.message || 'Mot de passe non modifie.', 'err');
    }
}

async function startCheckout(plan) {
    try {
        setMessage('account-message', 'Redirection vers Stripe...');
        const response = await fetch('/api/billing/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan, return_path: '/account' }),
        });
        const payload = await readJson(response);
        window.location.href = payload.url;
    } catch (error) {
        setMessage('account-message', error.message || 'Paiement indisponible.', 'err');
    }
}

async function openPortal() {
    try {
        setMessage('account-message', 'Ouverture du portail Stripe...');
        const response = await fetch('/api/billing/portal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ return_path: '/account' }),
        });
        const payload = await readJson(response);
        window.location.href = payload.url;
    } catch (error) {
        setMessage('account-message', error.message || 'Portail Stripe indisponible.', 'err');
    }
}

async function resendConfirmation() {
    if (!state.account?.email) return;
    try {
        setMessage('account-message', 'Envoi du code...');
        const response = await fetch('/api/account/resend-confirmation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: state.account.email }),
        });
        await readJson(response);
        setMessage('account-message', 'Code de confirmation renvoye par email.', 'ok');
    } catch (error) {
        setMessage('account-message', error.message || 'Code non envoye.', 'err');
    }
}

async function syncBillingReturn() {
    const params = new URLSearchParams(window.location.search);
    const status = params.get('billing');
    const sessionId = params.get('session_id');
    if (status === 'canceled') {
        setMessage('account-message', 'Paiement annule. Tu peux choisir une formule quand tu veux.', 'err');
        window.history.replaceState({}, '', window.location.pathname);
        return;
    }
    if (status !== 'success' || !sessionId) return;

    try {
        setMessage('account-message', 'Validation du paiement Stripe...');
        const response = await fetch('/api/billing/sync-checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
        });
        await readJson(response);
        setMessage('account-message', 'Paiement valide. Ton accès est activé.', 'ok');
    } catch (error) {
        setMessage('account-message', error.message || 'Paiement reçu, synchronisation en attente.', 'err');
    } finally {
        window.history.replaceState({}, '', window.location.pathname);
    }
}

async function logout() {
    await fetch('/api/account/logout', { method: 'POST' });
    window.location.href = '/';
}

function bindAccountPage() {
    document.getElementById('account-profile-form')?.addEventListener('submit', saveProfile);
    document.getElementById('account-password-form')?.addEventListener('submit', savePassword);
    document.getElementById('account-portal')?.addEventListener('click', openPortal);
    document.getElementById('account-resend-confirmation')?.addEventListener('click', resendConfirmation);
    document.getElementById('account-logout')?.addEventListener('click', logout);
    document.querySelectorAll('[data-account-plan]').forEach((button) => {
        button.addEventListener('click', () => startCheckout(button.dataset.accountPlan));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    bindAccountPage();
    (async () => {
        await syncBillingReturn();
        await fetchAccount();
    })().catch(() => {
        document.getElementById('account-login-state')?.classList.remove('hidden');
        document.getElementById('account-dashboard')?.classList.add('hidden');
    });
});
