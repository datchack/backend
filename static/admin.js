let adminUsers = [];
let searchQuery = '';
let statusFilter = 'all';

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
    return new Date(value).toLocaleDateString('fr-FR');
}

function formatAccessEnd(user) {
    if (user.role === 'owner') return 'LIFETIME';
    if (user.role === 'member') return 'ACCES ACTIF';
    if (user.role === 'trial') return formatDate(user.trial_ends_at);
    return 'EXPIRE';
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
        body.innerHTML = '<tr><td colspan="6" class="admin-empty">Aucun compte trouve.</td></tr>';
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
        setAdminMessage('Chargement des comptes...');
        const response = await fetch('/api/admin/users', { cache: 'no-store' });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || 'Acces admin indisponible');
        }

        adminUsers = payload.users || [];
        renderMetrics();
        renderUsers();
        setAdminMessage(`${adminUsers.length} compte(s) synchronise(s).`, 'ok');
    } catch (error) {
        setAdminMessage(error.message || 'Erreur admin', 'err');
    }
}

async function updateUserAccess(userId, action) {
    try {
        setAdminMessage('Mise a jour du compte...');
        const response = await fetch(`/api/admin/users/${userId}/access`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || 'Action impossible');
        }

        adminUsers = adminUsers.map((user) => user.id === payload.user.id ? payload.user : user);
        renderMetrics();
        renderUsers();
        setAdminMessage('Compte mis a jour.', 'ok');
    } catch (error) {
        setAdminMessage(error.message || 'Erreur admin', 'err');
    }
}

function bindAdmin() {
    const refresh = document.getElementById('admin-refresh');
    const search = document.getElementById('admin-search');
    const filter = document.getElementById('admin-status-filter');
    const body = document.getElementById('admin-users-body');

    if (refresh) refresh.addEventListener('click', fetchAdminUsers);
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
    fetchAdminUsers();
});
