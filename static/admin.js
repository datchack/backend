let adminUsers = [];
let searchQuery = '';
let statusFilter = 'all';
let adminLang = localStorage.getItem('xt_lang') || 'fr';

const ADMIN_COPY = {
    fr: {
        meta_title: 'ADMIN - XAUTERMINAL',
        kicker: 'OWNER CONTROL',
        title: 'Administration',
        refresh: 'REFRESH',
        metric_total: 'TOTAL',
        metric_active: 'ACTIFS',
        metric_trial: 'ESSAIS',
        metric_pending: 'EN ATTENTE',
        metric_expired: 'EXPIRÉS',
        users_kicker: 'USERS',
        users_title: 'Comptes terminal',
        resend_activation: 'Relancer validations',
        search_placeholder: 'Rechercher un email',
        filter_title: 'Filtrer par statut',
        filter_all: 'TOUS',
        loading: 'Chargement...',
        status: 'Statut',
        role: 'Rôle',
        expiration: 'Expiration',
        created: 'Création',
        actions: 'Actions',
        empty: 'Aucun compte trouvé.',
        access_active: 'ACCÈS ACTIF',
        expired: 'EXPIRÉ',
        loading_accounts: 'Chargement des comptes...',
        admin_unavailable: 'Accès admin indisponible',
        synced: 'compte(s) synchronisé(s).',
        admin_error: 'Erreur admin',
        updating: 'Mise à jour du compte...',
        action_error: 'Action impossible',
        account_updated: 'Compte mis à jour.',
        resend_confirm: 'Envoyer un email de validation aux comptes non confirmés éligibles ?',
        resend_running: 'Envoi des relances de validation...',
        resend_done: 'relance(s) envoyée(s).',
        resend_none: 'Aucun compte éligible à relancer.',
        resend_error: 'Relance impossible',
    },
    en: {
        meta_title: 'ADMIN - XAUTERMINAL',
        kicker: 'OWNER CONTROL',
        title: 'Administration',
        refresh: 'REFRESH',
        metric_total: 'TOTAL',
        metric_active: 'ACTIVE',
        metric_trial: 'TRIAL',
        metric_pending: 'PENDING',
        metric_expired: 'EXPIRED',
        users_kicker: 'USERS',
        users_title: 'Terminal accounts',
        resend_activation: 'Send reminders',
        search_placeholder: 'Search email',
        filter_title: 'Filter by status',
        filter_all: 'ALL',
        loading: 'Loading...',
        status: 'Status',
        role: 'Role',
        expiration: 'Expiration',
        created: 'Created',
        actions: 'Actions',
        empty: 'No account found.',
        access_active: 'ACCESS ACTIVE',
        expired: 'EXPIRED',
        loading_accounts: 'Loading accounts...',
        admin_unavailable: 'Admin access unavailable',
        synced: 'account(s) synced.',
        admin_error: 'Admin error',
        updating: 'Updating account...',
        action_error: 'Action impossible',
        account_updated: 'Account updated.',
        resend_confirm: 'Send a validation email to eligible unconfirmed accounts?',
        resend_running: 'Sending validation reminders...',
        resend_done: 'reminder(s) sent.',
        resend_none: 'No eligible account to remind.',
        resend_error: 'Unable to send reminders',
    },
};

function t(key) {
    return ADMIN_COPY[adminLang]?.[key] || ADMIN_COPY.fr[key] || key;
}

function applyAdminLanguage() {
    document.documentElement.lang = adminLang;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
        el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    document.querySelectorAll('[data-i18n-title]').forEach((el) => {
        el.title = t(el.dataset.i18nTitle);
    });
    const title = document.querySelector('title');
    if (title?.dataset.i18n) title.textContent = t(title.dataset.i18n);
    const toggle = document.querySelector('[data-admin-lang-toggle]');
    if (toggle) toggle.textContent = adminLang === 'fr' ? 'EN' : 'FR';
    renderUsers();
}

function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    }[char]));
}

function formatDate(value, lifetime = false) {
    if (lifetime) return 'LIFETIME';
    if (!value) return '-';
    return new Date(value).toLocaleDateString(adminLang === 'fr' ? 'fr-FR' : 'en-US');
}

function formatAccessEnd(user) {
    if (user.role === 'owner') return 'LIFETIME';
    if (user.role === 'member') return t('access_active');
    if (user.role === 'trial') return formatDate(user.trial_ends_at);
    return t('expired');
}

function setAdminMessage(message, tone = '') {
    const el = document.getElementById('admin-message');
    if (!el) return;
    el.textContent = message;
    el.className = `admin-message${tone ? ` ${tone}` : ''}`;
}

function getFilteredUsers() {
    const query = searchQuery.trim().toLowerCase();
    return adminUsers.filter((user) => {
        const role = String(user.role || '').toLowerCase();
        const status = String(user.status || '').toLowerCase();
        const plan = String(user.plan || '').toLowerCase();
        const matchesQuery = !query || String(user.email || '').toLowerCase().includes(query);
        const matchesFilter = statusFilter === 'all'
            || role === statusFilter
            || status === statusFilter
            || plan === statusFilter;
        return matchesQuery && matchesFilter;
    });
}

function renderMetrics() {
    const total = adminUsers.length;
    const active = adminUsers.filter((user) => user.has_access && user.role !== 'trial').length;
    const trial = adminUsers.filter((user) => user.role === 'trial').length;
    const pending = adminUsers.filter((user) => user.status === 'pending').length;
    const expired = adminUsers.filter((user) => !user.has_access).length;

    document.getElementById('metric-total').textContent = total;
    document.getElementById('metric-active').textContent = active;
    document.getElementById('metric-trial').textContent = trial;
    document.getElementById('metric-pending').textContent = pending;
    document.getElementById('metric-expired').textContent = expired;
}

function renderUsers() {
    const body = document.getElementById('admin-users-body');
    if (!body) return;

    const users = getFilteredUsers();
    if (!users.length) {
        body.innerHTML = `<tr><td colspan="6" class="admin-empty">${t('empty')}</td></tr>`;
        return;
    }

    body.innerHTML = users.map((user) => {
        const role = String(user.role || user.plan || '-').toUpperCase();
        const status = String(user.status || '-').toUpperCase();
        const accessClass = user.has_access ? 'ok' : 'err';
        const ownerLocked = user.role === 'owner';
        const actions = ownerLocked
            ? '<button type="button" class="panel-btn" disabled>OWNER</button>'
            : user.status === 'pending'
            ? '<button type="button" class="panel-btn" data-admin-action="confirm">CONFIRM</button>'
            : `
                <button type="button" class="panel-btn" data-admin-action="active">ACTIVE</button>
                <button type="button" class="panel-btn" data-admin-action="trial">TRIAL</button>
                <button type="button" class="panel-btn" data-admin-action="expire">EXPIRE</button>
                <button type="button" class="panel-btn" data-admin-action="owner">OWNER</button>
            `;
        return `
            <tr data-user-id="${user.id}">
                <td>
                    <strong>${escapeHtml(user.email)}</strong>
                    <span>#${user.id}</span>
                </td>
                <td>${role}</td>
                <td><span class="${accessClass}">${status}</span></td>
                <td>${formatAccessEnd(user)}</td>
                <td>${formatDate(user.created_at)}</td>
                <td>
                    <div class="admin-row-actions${ownerLocked ? ' owner-locked' : ''}">${actions}</div>
                </td>
            </tr>
        `;
    }).join('');
}

async function fetchAdminUsers() {
    try {
        setAdminMessage(t('loading_accounts'));
        const response = await fetch('/api/admin/users', { cache: 'no-store' });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || t('admin_unavailable'));
        }

        adminUsers = payload.users || [];
        renderMetrics();
        renderUsers();
        setAdminMessage(`${adminUsers.length} ${t('synced')}`, 'ok');
    } catch (error) {
        setAdminMessage(error.message || t('admin_error'), 'err');
    }
}

async function updateUserAccess(userId, action) {
    try {
        setAdminMessage(t('updating'));
        const response = await fetch(`/api/admin/users/${userId}/access`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || t('action_error'));
        }

        adminUsers = adminUsers.map((user) => user.id === payload.user.id ? payload.user : user);
        renderMetrics();
        renderUsers();
        setAdminMessage(t('account_updated'), 'ok');
    } catch (error) {
        setAdminMessage(error.message || t('admin_error'), 'err');
    }
}

async function resendActivationReminders(button) {
    if (!window.confirm(t('resend_confirm'))) return;
    try {
        if (button) button.disabled = true;
        setAdminMessage(t('resend_running'));
        const response = await fetch('/api/admin/users/resend-activation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 50 }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || t('resend_error'));
        }

        adminUsers = payload.users || adminUsers;
        renderMetrics();
        renderUsers();
        const sent = Number(payload.sent_count || 0);
        setAdminMessage(sent ? `${sent} ${t('resend_done')}` : t('resend_none'), sent ? 'ok' : '');
    } catch (error) {
        setAdminMessage(error.message || t('resend_error'), 'err');
    } finally {
        if (button) button.disabled = false;
    }
}

function bindAdmin() {
    const refresh = document.getElementById('admin-refresh');
    const resendActivation = document.getElementById('admin-resend-activation');
    const search = document.getElementById('admin-search');
    const filter = document.getElementById('admin-status-filter');
    const body = document.getElementById('admin-users-body');
    const langToggle = document.querySelector('[data-admin-lang-toggle]');

    if (refresh) refresh.addEventListener('click', fetchAdminUsers);
    if (resendActivation) {
        resendActivation.addEventListener('click', () => resendActivationReminders(resendActivation));
    }
    if (search) {
        search.addEventListener('input', () => {
            searchQuery = search.value;
            renderUsers();
        });
    }
    if (filter) {
        filter.addEventListener('change', () => {
            statusFilter = filter.value;
            renderUsers();
        });
    }
    if (langToggle) {
        langToggle.addEventListener('click', () => {
            adminLang = adminLang === 'fr' ? 'en' : 'fr';
            localStorage.setItem('xt_lang', adminLang);
            applyAdminLanguage();
            if (adminUsers.length) setAdminMessage(`${adminUsers.length} ${t('synced')}`, 'ok');
        });
    }
    if (body) {
        body.addEventListener('click', (event) => {
            const button = event.target.closest('[data-admin-action]');
            const row = event.target.closest('[data-user-id]');
            if (!button || !row) return;
            updateUserAccess(Number(row.dataset.userId), button.dataset.adminAction);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    bindAdmin();
    applyAdminLanguage();
    fetchAdminUsers();
});
