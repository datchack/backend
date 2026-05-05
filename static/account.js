const state = {
    account: null,
};

function setMessage(message = '', tone = '') {
    const el = document.getElementById('account-message');
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
    return new Date(value).toLocaleDateString('fr-FR');
}

function setValue(id, value = '') {
    const el = document.getElementById(id);
    if (el) el.value = value || '';
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

function renderAccount(account) {
    state.account = account;

    document.getElementById('account-login-state')?.classList.add('hidden');
    document.getElementById('account-dashboard')?.classList.remove('hidden');

    const role = account.role || 'guest';
    const hasAccess = !!account.has_access;
    const emailConfirmed = !!account.email_confirmed;

    const title = document.getElementById('account-status-title');
    const copy = document.getElementById('account-status-copy');
    if (title) {
        title.textContent = hasAccess
            ? 'Acces terminal actif'
            : emailConfirmed
            ? 'Email confirme, paiement requis'
            : 'Email a confirmer';
    }
    if (copy) {
        copy.textContent = hasAccess
            ? 'Ton compte peut ouvrir le terminal complet.'
            : emailConfirmed
            ? 'Choisis une formule Stripe pour demarrer ton essai et ouvrir le terminal.'
            : 'Confirme ton adresse email avant de choisir une formule Stripe.';
    }

    document.getElementById('account-email').textContent = account.email || '-';
    document.getElementById('account-plan').textContent = (account.plan || '-').toUpperCase();
    document.getElementById('account-access').textContent = hasAccess ? 'ACTIF' : role.toUpperCase();
    document.getElementById('account-trial-end').textContent = account.trial_active ? formatDate(account.trial_ends_at) : '-';

    fillProfile(account);
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
        setMessage('Enregistrement...');
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
        setMessage('Profil enregistre.', 'ok');
    } catch (error) {
        setMessage(error.message || "Impossible d'enregistrer le profil.", 'err');
    }
}

async function startCheckout(plan) {
    try {
        setMessage('Redirection vers Stripe...');
        const response = await fetch('/api/billing/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan }),
        });
        const payload = await readJson(response);
        window.location.href = payload.url;
    } catch (error) {
        setMessage(error.message || 'Paiement indisponible.', 'err');
    }
}

async function openPortal() {
    try {
        setMessage('Ouverture du portail Stripe...');
        const response = await fetch('/api/billing/portal', { method: 'POST' });
        const payload = await readJson(response);
        window.location.href = payload.url;
    } catch (error) {
        setMessage(error.message || 'Portail Stripe indisponible.', 'err');
    }
}

async function logout() {
    await fetch('/api/account/logout', { method: 'POST' });
    window.location.href = '/';
}

function bindAccountPage() {
    document.getElementById('account-profile-form')?.addEventListener('submit', saveProfile);
    document.getElementById('account-portal')?.addEventListener('click', openPortal);
    document.getElementById('account-logout')?.addEventListener('click', logout);
    document.querySelectorAll('[data-account-plan]').forEach((button) => {
        button.addEventListener('click', () => startCheckout(button.dataset.accountPlan));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    bindAccountPage();
    fetchAccount();
});
