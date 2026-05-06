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
        metric_unconfirmed: 'NON CONFIRMÉS',
        metric_to_pay: 'À PAYER',
        metric_active: 'ACTIFS',
        metric_review: 'À VÉRIFIER',
        users_kicker: 'USERS',
        users_title: 'Comptes terminal',
        resend_activation: 'Relancer validations',
        search_placeholder: 'Rechercher un email',
        filter_title: 'Filtrer par statut',
        filter_all: 'TOUS',
        filter_unconfirmed: 'NON CONFIRMÉS',
        filter_confirmed_no_stripe: 'CONFIRMÉS SANS STRIPE',
        filter_active: 'ACTIFS',
        filter_needs_review: 'À VÉRIFIER',
        loading: 'Chargement...',
        status: 'Statut',
        role: 'Rôle',
        account: 'Compte',
        state: 'État',
        checks: 'Contrôles',
        stripe: 'Stripe',
        stripe_billing: 'Stripe & billing',
        timeline: 'Dates',
        expiration: 'Expiration',
        created: 'Création',
        reminder: 'Relance',
        actions: 'Actions',
        empty: 'Aucun compte trouvé.',
        access_active: 'ACCÈS ACTIF',
        expired: 'EXPIRÉ',
        yes: 'Oui',
        no: 'Non',
        email_confirmed: 'Email',
        terminal_access: 'Terminal',
        stripe_linked: 'Stripe lié',
        stripe_missing: 'Stripe absent',
        customer: 'Client',
        subscription: 'Abo',
        session: 'Session',
        price: 'Prix',
        period_end: 'Fin période',
        never: 'Jamais',
        billing_status_ok: 'Billing OK',
        issue_confirmed_no_stripe: 'Confirmé sans Stripe',
        issue_stripe_without_access: 'Stripe lié, accès inactif',
        issue_missing_period_end: 'Fin de période manquante',
        no_issue: 'Aucun souci détecté',
        loading_accounts: 'Chargement des comptes...',
        admin_unavailable: 'Accès admin indisponible',
        synced: 'compte(s) synchronisé(s).',
        admin_error: 'Erreur admin',
        updating: 'Mise à jour du compte...',
        sending_one: 'Envoi de la relance...',
        syncing_stripe: 'Synchronisation Stripe...',
        action_error: 'Action impossible',
        account_updated: 'Compte mis à jour.',
        reminder_sent: 'Relance envoyée.',
        stripe_synced: 'Stripe synchronisé.',
        action_remind: 'RELANCE',
        action_open_stripe: 'STRIPE',
        action_sync_stripe: 'SYNC',
        action_confirm: 'CONFIRM',
        action_activate: 'ACTIVER',
        action_trial: 'ESSAI',
        action_expire: 'EXPIRER',
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
        metric_unconfirmed: 'UNCONFIRMED',
        metric_to_pay: 'TO PAY',
        metric_active: 'ACTIVE',
        metric_review: 'TO REVIEW',
        users_kicker: 'USERS',
        users_title: 'Terminal accounts',
        resend_activation: 'Send reminders',
        search_placeholder: 'Search email',
        filter_title: 'Filter by status',
        filter_all: 'ALL',
        filter_unconfirmed: 'UNCONFIRMED',
        filter_confirmed_no_stripe: 'CONFIRMED NO STRIPE',
        filter_active: 'ACTIVE',
        filter_needs_review: 'TO REVIEW',
        loading: 'Loading...',
        status: 'Status',
        role: 'Role',
        account: 'Account',
        state: 'State',
        checks: 'Checks',
        stripe: 'Stripe',
        stripe_billing: 'Stripe & billing',
        timeline: 'Timeline',
        expiration: 'Expiration',
        created: 'Created',
        reminder: 'Reminder',
        actions: 'Actions',
        empty: 'No account found.',
        access_active: 'ACCESS ACTIVE',
        expired: 'EXPIRED',
        yes: 'Yes',
        no: 'No',
        email_confirmed: 'Email',
        terminal_access: 'Terminal',
        stripe_linked: 'Stripe linked',
        stripe_missing: 'No Stripe',
        customer: 'Customer',
        subscription: 'Sub',
        session: 'Session',
        price: 'Price',
        period_end: 'Period end',
        never: 'Never',
        billing_status_ok: 'Billing OK',
        issue_confirmed_no_stripe: 'Confirmed without Stripe',
        issue_stripe_without_access: 'Stripe linked, access inactive',
        issue_missing_period_end: 'Missing period end',
        no_issue: 'No issue detected',
        loading_accounts: 'Loading accounts...',
        admin_unavailable: 'Admin access unavailable',
        synced: 'account(s) synced.',
        admin_error: 'Admin error',
        updating: 'Updating account...',
        sending_one: 'Sending reminder...',
        syncing_stripe: 'Syncing Stripe...',
        action_error: 'Action impossible',
        account_updated: 'Account updated.',
        reminder_sent: 'Reminder sent.',
        stripe_synced: 'Stripe synced.',
        action_remind: 'REMIND',
        action_open_stripe: 'STRIPE',
        action_sync_stripe: 'SYNC',
        action_confirm: 'CONFIRM',
        action_activate: 'ACTIVATE',
        action_trial: 'TRIAL',
        action_expire: 'EXPIRE',
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
    updateQuickFilterState();
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

function shortId(value) {
    if (!value) return '-';
    const text = String(value);
    if (text.length <= 16) return text;
    return `${text.slice(0, 8)}...${text.slice(-5)}`;
}

function formatAccessEnd(user) {
    if (user.role === 'owner') return 'LIFETIME';
    if (user.role === 'member') return t('access_active');
    if (user.role === 'trial') return formatDate(user.trial_ends_at);
    return t('expired');
}

function hasStripe(user) {
    return !!(user.stripe_customer_id || user.stripe_subscription_id || user.stripe_price_id);
}

function isOwner(user) {
    return String(user.role || '').toLowerCase() === 'owner';
}

function needsReview(user) {
    return !!user.admin?.needs_review || (hasStripe(user) && !user.has_access && user.email_confirmed);
}

function userMatchesFilter(user, filter) {
    const role = String(user.role || '').toLowerCase();
    const status = String(user.status || '').toLowerCase();
    const plan = String(user.plan || '').toLowerCase();
    if (filter === 'all') return true;
    if (filter === 'unconfirmed') return !user.email_confirmed && !isOwner(user);
    if (filter === 'confirmed_no_stripe') return user.email_confirmed && !hasStripe(user) && !isOwner(user);
    if (filter === 'active') return user.has_access && role !== 'trial' && !isOwner(user);
    if (filter === 'needs_review') return needsReview(user);
    return role === filter || status === filter || plan === filter;
}

function statusPill(label, ok) {
    return `<span class="admin-pill ${ok ? 'ok' : 'err'}">${label}: ${ok ? t('yes') : t('no')}</span>`;
}

function issueLabel(issue) {
    return t(`issue_${issue}`);
}

function renderAccount(user) {
    const profile = user.profile || {};
    const name = [profile.first_name, profile.last_name].filter(Boolean).join(' ');
    if (!hasStripe(user)) {
        return `
            <div class="admin-account-cell">
                <strong>${escapeHtml(user.email)}</strong>
                <span>#${user.id}</span>
                ${name ? `<em>${escapeHtml(name)}</em>` : ''}
            </div>
        `;
    }
    return `
        <div class="admin-account-cell">
            <strong>${escapeHtml(user.email)}</strong>
            <span>#${user.id}</span>
            ${name ? `<em>${escapeHtml(name)}</em>` : ''}
        </div>
    `;
}

function renderState(user) {
    const role = String(user.role || user.plan || '-').toUpperCase();
    const status = String(user.status || '-').toUpperCase();
    const issues = user.admin?.issues || [];
    return `
        <div class="admin-card-stack">
            <div class="admin-state-line">
                <span class="admin-pill ${user.has_access ? 'ok' : 'err'}">${status}</span>
                <span class="admin-pill">${role}</span>
            </div>
            ${statusPill(t('email_confirmed'), !!user.email_confirmed)}
            ${statusPill(t('terminal_access'), !!user.has_access)}
            <span class="admin-pill ${issues.length ? 'warn' : 'ok'}">${issues.length ? issueLabel(issues[0]) : t('no_issue')}</span>
        </div>
    `;
}

function renderStripeBilling(user) {
    const issues = user.admin?.issues || [];
    if (!hasStripe(user)) {
        return `
            <div class="admin-card-stack">
                <span class="admin-pill err">${t('stripe_missing')}</span>
                <span>${t('price')}: -</span>
            </div>
        `;
    }
    return `
        <div class="admin-id-stack">
            <span class="admin-pill ${issues.length ? 'warn' : 'ok'}">${issues.length ? issueLabel(issues[0]) : t('billing_status_ok')}</span>
            <span>${t('customer')}: ${shortId(user.stripe_customer_id)}</span>
            <span>${t('subscription')}: ${shortId(user.stripe_subscription_id)}</span>
            <span>${t('session')}: ${shortId(user.stripe_checkout_session_id)}</span>
            <span>${t('price')}: ${shortId(user.stripe_price_id)}</span>
            <span>${t('period_end')}: ${formatDate(user.stripe_current_period_end)}</span>
        </div>
    `;
}

function renderTimeline(user) {
    return `
        <div class="admin-id-stack">
            <span>${t('created')}: ${formatDate(user.created_at)}</span>
            <span>${t('expiration')}: ${formatAccessEnd(user)}</span>
            <span>${t('reminder')}: ${user.email_confirmation_reminder_sent_at ? formatDate(user.email_confirmation_reminder_sent_at) : t('never')}</span>
        </div>
    `;
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
        const matchesQuery = !query || String(user.email || '').toLowerCase().includes(query);
        const matchesFilter = userMatchesFilter(user, statusFilter);
        return matchesQuery && matchesFilter;
    });
}

function renderMetrics() {
    const total = adminUsers.length;
    const active = adminUsers.filter((user) => user.has_access && user.role !== 'trial' && !isOwner(user)).length;
    const unconfirmed = adminUsers.filter((user) => !user.email_confirmed && !isOwner(user)).length;
    const toPay = adminUsers.filter((user) => user.email_confirmed && !hasStripe(user) && !isOwner(user)).length;
    const review = adminUsers.filter((user) => needsReview(user)).length;

    document.getElementById('metric-total').textContent = total;
    document.getElementById('metric-unconfirmed').textContent = unconfirmed;
    document.getElementById('metric-to-pay').textContent = toPay;
    document.getElementById('metric-active').textContent = active;
    document.getElementById('metric-review').textContent = review;
}

function renderUsers() {
    const body = document.getElementById('admin-users-body');
    if (!body) return;

    const users = getFilteredUsers();
    if (!users.length) {
        body.innerHTML = `<tr><td colspan="5" class="admin-empty">${t('empty')}</td></tr>`;
        return;
    }

    body.innerHTML = users.map((user) => {
        const ownerLocked = user.role === 'owner';
        const stripeUrl = user.admin?.stripe_customer_url || user.admin?.stripe_subscription_url;
        const stripeActions = hasStripe(user)
            ? `
                ${stripeUrl ? `<a class="panel-btn admin-action-link" href="${escapeHtml(stripeUrl)}" target="_blank" rel="noopener">${t('action_open_stripe')}</a>` : ''}
                <button type="button" class="panel-btn" data-admin-sync-stripe>${t('action_sync_stripe')}</button>
            `
            : '';
        const actions = ownerLocked
            ? '<button type="button" class="panel-btn" disabled>OWNER</button>'
            : `
                ${stripeActions}
                ${!user.email_confirmed ? `<button type="button" class="panel-btn" data-admin-remind>${t('action_remind')}</button>` : ''}
                ${!user.email_confirmed ? `<button type="button" class="panel-btn" data-admin-action="confirm">${t('action_confirm')}</button>` : ''}
                <button type="button" class="panel-btn" data-admin-action="active">${t('action_activate')}</button>
                <button type="button" class="panel-btn" data-admin-action="trial">${t('action_trial')}</button>
                <button type="button" class="panel-btn" data-admin-action="expire">${t('action_expire')}</button>
                <button type="button" class="panel-btn" data-admin-action="owner">OWNER</button>
            `;
        return `
            <tr data-user-id="${user.id}">
                <td data-label="${t('account')}">${renderAccount(user)}</td>
                <td data-label="${t('state')}">${renderState(user)}</td>
                <td data-label="${t('stripe_billing')}">${renderStripeBilling(user)}</td>
                <td data-label="${t('timeline')}">${renderTimeline(user)}</td>
                <td data-label="${t('actions')}">
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

async function resendUserActivation(userId) {
    try {
        setAdminMessage(t('sending_one'));
        const response = await fetch(`/api/admin/users/${userId}/resend-activation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || t('resend_error'));
        }

        adminUsers = adminUsers.map((user) => user.id === payload.user.id ? payload.user : user);
        renderMetrics();
        renderUsers();
        setAdminMessage(t('reminder_sent'), 'ok');
    } catch (error) {
        setAdminMessage(error.message || t('resend_error'), 'err');
    }
}

async function syncUserStripe(userId) {
    try {
        setAdminMessage(t('syncing_stripe'));
        const response = await fetch(`/api/admin/users/${userId}/sync-stripe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || t('action_error'));
        }

        adminUsers = adminUsers.map((user) => user.id === payload.user.id ? payload.user : user);
        renderMetrics();
        renderUsers();
        setAdminMessage(t('stripe_synced'), 'ok');
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

function updateQuickFilterState() {
    document.querySelectorAll('[data-admin-filter]').forEach((button) => {
        button.classList.toggle('active', button.dataset.adminFilter === statusFilter);
    });
    const select = document.getElementById('admin-status-filter');
    if (!select) return;
    const hasOption = Array.from(select.options).some((option) => option.value === statusFilter);
    select.value = hasOption ? statusFilter : 'all';
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
            updateQuickFilterState();
            renderUsers();
        });
    }
    document.querySelectorAll('[data-admin-filter]').forEach((button) => {
        button.addEventListener('click', () => {
            statusFilter = button.dataset.adminFilter || 'all';
            updateQuickFilterState();
            renderUsers();
        });
    });
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
            const remindButton = event.target.closest('[data-admin-remind]');
            const syncStripeButton = event.target.closest('[data-admin-sync-stripe]');
            const button = event.target.closest('[data-admin-action]');
            const row = event.target.closest('[data-user-id]');
            if (!row) return;
            if (remindButton) {
                resendUserActivation(Number(row.dataset.userId));
                return;
            }
            if (syncStripeButton) {
                syncUserStripe(Number(row.dataset.userId));
                return;
            }
            if (!button) return;
            updateUserAccess(Number(row.dataset.userId), button.dataset.adminAction);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    bindAdmin();
    applyAdminLanguage();
    fetchAdminUsers();
});
