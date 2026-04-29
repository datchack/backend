const PREFS_KEY = 'tt_prefs_v1';
const CALENDAR_REFRESH_MS = 60000;
const NEWS_REFRESH_MS = 8000;
const CONTEXT_REFRESH_MS = 15000;
const IMPACT_LEVELS = ['High', 'Medium', 'Low'];
const DEFAULT_ACCOUNT_MODE = 'register';

function loadPrefs() {
    try {
        return JSON.parse(localStorage.getItem(PREFS_KEY)) || {};
    } catch {
        return {};
    }
}

function savePrefs(patch) {
    try {
        const current = loadPrefs();
        const next = { ...current, ...patch };
        localStorage.setItem(PREFS_KEY, JSON.stringify(next));
        schedulePrefsSync(next);
    } catch {}
}

const PREFS = loadPrefs();
const DEFAULT_LAYOUT = {
    leftWidth: 340,
    rightWidth: 340,
    insightWidth: 320,
    collapsed: {
        left: false,
        right: false,
        chart: false,
        insight: false,
    },
};

let currentSymbol = PREFS.symbol || 'OANDA:XAUUSD';
let soundEnabled = !!PREFS.soundEnabled;
let soundType = PREFS.soundType || 'chime';
let currentCenterTab = PREFS.centerTab || 'bias';
let layoutState = loadLayoutPrefs();
let accountMode = DEFAULT_ACCOUNT_MODE;
let accountState = { authenticated: false, account: null };
let adminPanelOpen = false;
let adminUsers = [];
let prefsSyncTimer = null;
let appBooted = false;
let accessFormMode = 'intro';
let lastSeenNewsTs = 0;
let calEvents = [];
let contextState = null;
let calendarMeta = { timezone: 'Europe/Paris', error: null, count: 0, weekStart: null, weekEnd: null };
let audioCtx = null;

const calFilters = {
    impact: new Set(PREFS.impactFilters || IMPACT_LEVELS),
};

const MARKETS = {
    NY: { tz: 'America/New_York', label: 'NEW YORK', open: [9, 30], close: [16, 0] },
    LDN: { tz: 'Europe/London', label: 'LONDON', open: [8, 0], close: [16, 30] },
    TKY: { tz: 'Asia/Tokyo', label: 'TOKYO', open: [9, 0], close: [15, 0] },
    SYD: { tz: 'Australia/Sydney', label: 'SYDNEY', open: [10, 0], close: [16, 0] },
};

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function loadLayoutPrefs(source = null) {
    const raw = source || PREFS.layout || {};
    return {
        leftWidth: clamp(Number(raw.leftWidth) || DEFAULT_LAYOUT.leftWidth, 260, 520),
        rightWidth: clamp(Number(raw.rightWidth) || DEFAULT_LAYOUT.rightWidth, 260, 520),
        insightWidth: clamp(Number(raw.insightWidth) || DEFAULT_LAYOUT.insightWidth, 260, 520),
        collapsed: {
            left: !!raw.collapsed?.left,
            right: !!raw.collapsed?.right,
            chart: !!raw.collapsed?.chart,
            insight: !!raw.collapsed?.insight,
        },
    };
}

function persistLayout() {
    savePrefs({ layout: layoutState });
}

function getClientPrefsSnapshot() {
    return {
        ...loadPrefs(),
        symbol: currentSymbol,
        soundEnabled,
        soundType,
        centerTab: currentCenterTab,
        impactFilters: [...calFilters.impact],
        layout: layoutState,
    };
}

function schedulePrefsSync(nextPrefs = null) {
    if (!accountState.authenticated) return;

    const payload = nextPrefs || getClientPrefsSnapshot();
    window.clearTimeout(prefsSyncTimer);
    prefsSyncTimer = window.setTimeout(() => {
        syncPreferences(payload);
    }, 350);
}

async function syncPreferences(prefs = null) {
    if (!accountState.authenticated) return;

    try {
        await fetch('/api/account/preferences', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prefs: prefs || getClientPrefsSnapshot() }),
        });
    } catch (error) {
        console.error(error);
    }
}

function applyLoadedPrefs(prefs = {}) {
    if (!prefs || typeof prefs !== 'object') return;

    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));

    currentSymbol = prefs.symbol || currentSymbol;
    soundEnabled = typeof prefs.soundEnabled === 'boolean' ? prefs.soundEnabled : soundEnabled;
    soundType = prefs.soundType || soundType;
    currentCenterTab = prefs.centerTab || currentCenterTab;
    layoutState = {
        ...layoutState,
        ...loadLayoutPrefs(prefs.layout),
        ...(prefs.layout || {}),
        collapsed: {
            ...layoutState.collapsed,
            ...(prefs.layout?.collapsed || {}),
        },
    };

    const impactPrefs = Array.isArray(prefs.impactFilters) && prefs.impactFilters.length ? prefs.impactFilters : IMPACT_LEVELS;
    calFilters.impact = new Set(impactPrefs);

    renderSoundToggle();
    renderCalendarFilters();
    const soundSelect = document.getElementById('sound-pick');
    if (soundSelect) soundSelect.value = soundType;
    const cmdInput = document.getElementById('cmd');
    if (cmdInput) cmdInput.value = currentSymbol;
    setCenterTab(currentCenterTab);
    applyLayoutState();
    if (appBooted) {
        changeChart(currentSymbol);
    }
}

function hasTerminalAccess() {
    return !!accountState.account?.has_access;
}

function renderAccessGate() {
    const gate = document.getElementById('access-gate');
    const title = document.getElementById('access-title');
    const copy = document.getElementById('access-copy');
    const intro = document.getElementById('access-intro');
    const auth = document.getElementById('access-auth');
    if (!gate || !title || !copy || !intro || !auth) return;

    const authenticated = !!accountState.authenticated;
    const role = accountState.account?.role || 'guest';
    const gated = !hasTerminalAccess();

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

function setAccessAuthMessage(message = '', tone = '') {
    const el = document.getElementById('access-auth-message');
    if (!el) return;
    el.textContent = message;
    el.className = `access-auth-message${tone ? ` ${tone}` : ''}`;
}

function setAccessFormMode(mode) {
    accessFormMode = mode === 'login' ? 'login' : mode === 'register' ? 'register' : 'intro';

    const kicker = document.getElementById('access-auth-kicker');
    const title = document.getElementById('access-auth-title');
    const copy = document.getElementById('access-auth-copy');
    const submit = document.getElementById('access-auth-submit');
    const switchBtn = document.getElementById('access-auth-switch');
    const password = document.getElementById('access-auth-password');

    if (accessFormMode === 'intro') {
        renderAccessGate();
        return;
    }

    if (kicker) kicker.textContent = accessFormMode === 'login' ? 'CONNEXION' : 'CREATION DE COMPTE';
    if (title) title.textContent = accessFormMode === 'login' ? 'Reconnecte-toi au terminal' : 'Active ton essai maintenant';
    if (copy) copy.textContent = accessFormMode === 'login'
        ? 'Connecte-toi pour retrouver ton workspace et tes preferences.'
        : 'Cree ton compte pour ouvrir le terminal complet pendant 7 jours.';
    if (submit) submit.textContent = accessFormMode === 'login' ? 'SE CONNECTER' : 'CREER MON COMPTE';
    if (switchBtn) switchBtn.textContent = accessFormMode === 'login' ? 'CREER UN COMPTE' : "J'AI DEJA UN COMPTE";
    if (password) password.autocomplete = accessFormMode === 'login' ? 'current-password' : 'new-password';

    renderAccessGate();

    const email = document.getElementById('access-auth-email');
    if (email) {
        window.setTimeout(() => email.focus(), 30);
    }
}

function bootTerminalApp() {
    if (appBooted) return;
    appBooted = true;

    initChart(currentSymbol);
    getNews();
    fetchCalendar();
    fetchContext();
    window.setInterval(getNews, NEWS_REFRESH_MS);
}

function ensureAudio() {
    if (!audioCtx) {
        try {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        } catch {
            audioCtx = null;
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

function tone(freq, startOffset, duration, peak, type) {
    const now = audioCtx.currentTime;
    const oscillator = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    oscillator.type = type;
    oscillator.frequency.value = freq;

    gain.gain.setValueAtTime(0.0001, now + startOffset);
    gain.gain.exponentialRampToValueAtTime(peak, now + startOffset + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + startOffset + duration);

    oscillator.connect(gain).connect(audioCtx.destination);
    oscillator.start(now + startOffset);
    oscillator.stop(now + startOffset + duration + 0.02);
}

function playSound(kind) {
    if (!audioCtx) return;

    switch (kind) {
        case 'ping':
            tone(1760, 0, 0.18, 0.22, 'sine');
            break;
        case 'chime':
            tone(880, 0, 0.2, 0.25, 'sine');
            tone(1320, 0.12, 0.2, 0.25, 'sine');
            break;
        case 'siren':
            [0, 0.18, 0.36].forEach((offset) => {
                tone(700, offset, 0.1, 0.22, 'square');
                tone(1100, offset + 0.09, 0.1, 0.22, 'square');
            });
            break;
        case 'bloop':
            tone(440, 0, 0.15, 0.22, 'triangle');
            break;
        case 'alert':
            [0, 0.14, 0.28].forEach((offset) => tone(2000, offset, 0.08, 0.28, 'sawtooth'));
            break;
    }
}

function beep() {
    if (!soundEnabled || !audioCtx) return;
    playSound(soundType);
}

function renderSoundToggle() {
    const soundEl = document.getElementById('status-sound');
    if (!soundEl) return;

    soundEl.textContent = soundEnabled ? 'SOUND ON' : 'SOUND OFF';
    soundEl.style.color = soundEnabled ? '#22c55e' : '';
}

function setAccountMessage(message = '', tone = '') {
    const messageEl = document.getElementById('account-message');
    if (!messageEl) return;
    messageEl.textContent = message;
    messageEl.className = `account-message${tone ? ` ${tone}` : ''}`;
}

function setAccountMode(mode) {
    accountMode = mode === 'login' ? 'login' : 'register';

    const titleEl = document.getElementById('account-title');
    const submitEl = document.getElementById('account-submit');
    const switchEl = document.getElementById('account-switch');
    const passwordEl = document.getElementById('account-password');

    if (titleEl) titleEl.textContent = accountMode === 'login' ? 'CONNEXION' : 'ESPACE COMPTE';
    if (submitEl) submitEl.textContent = accountMode === 'login' ? 'SE CONNECTER' : 'CREER MON COMPTE';
    if (switchEl) switchEl.textContent = accountMode === 'login' ? 'CREER UN COMPTE' : "J'AI DEJA UN COMPTE";
    if (passwordEl) passwordEl.autocomplete = accountMode === 'login' ? 'current-password' : 'new-password';
}

function renderAccountState() {
    const toggle = document.getElementById('account-toggle');
    const trial = document.getElementById('account-trial');
    const summary = document.getElementById('account-summary');
    const form = document.getElementById('account-form');
    const userBlock = document.getElementById('account-user');
    const emailValue = document.getElementById('account-email-value');
    const planValue = document.getElementById('account-plan-value');
    const expiryValue = document.getElementById('account-expiry-value');
    const adminToggle = document.getElementById('account-admin-toggle');
    const adminPanel = document.getElementById('account-admin');

    if (!toggle || !trial || !summary || !form || !userBlock) return;

    if (!accountState.authenticated || !accountState.account) {
        toggle.textContent = 'ACCOUNT';
        trial.textContent = 'TRIAL 7J';
        summary.textContent = "Connecte-toi pour sauvegarder ton terminal et demarrer un essai 7 jours.";
        form.classList.remove('hidden');
        userBlock.classList.add('hidden');
        if (adminToggle) adminToggle.classList.add('hidden');
        if (adminPanel) adminPanel.classList.add('hidden');
        adminPanelOpen = false;
        setAccountMode(accountMode);
        renderAccessGate();
        return;
    }

    const { account } = accountState;
    toggle.textContent = 'MY ACCOUNT';
    trial.textContent = account.role === 'owner'
        ? 'OWNER'
        : account.trial_active ? `TRIAL ${account.trial_days_left}J` : (account.plan || 'PLAN').toUpperCase();
    summary.textContent = account.role === 'owner'
        ? 'Acces createur actif a vie. Le terminal complet reste ouvert sans limitation.'
        : account.trial_active
        ? `Essai actif jusqu'au ${new Date(account.trial_ends_at).toLocaleDateString('fr-FR')}. Tes preferences sont synchronisees.`
        : 'Compte actif. Structure abonnement prete a etre branchee.';
    form.classList.add('hidden');
    userBlock.classList.remove('hidden');
    if (emailValue) emailValue.textContent = account.email;
    if (planValue) planValue.textContent = account.role === 'owner' ? 'OWNER' : String(account.plan || 'trial').toUpperCase();
    if (expiryValue) expiryValue.textContent = account.role === 'owner' ? 'LIFETIME' : new Date(account.trial_ends_at).toLocaleDateString('fr-FR');
    if (adminToggle) adminToggle.classList.toggle('hidden', account.role !== 'owner');
    if (adminPanel) adminPanel.classList.toggle('hidden', account.role !== 'owner' || !adminPanelOpen);
    renderAccessGate();
}

function renderAdminUsers() {
    const list = document.getElementById('account-admin-list');
    if (!list) return;

    if (!adminUsers.length) {
        list.innerHTML = '<div class="account-admin-empty">Aucun utilisateur.</div>';
        return;
    }

    list.innerHTML = adminUsers.map((user) => {
        const expiry = user.role === 'owner' ? 'LIFETIME' : new Date(user.trial_ends_at).toLocaleDateString('fr-FR');
        const statusClass = user.has_access ? 'ok' : 'err';
        return `
            <div class="account-admin-row" data-user-id="${user.id}">
                <div class="account-admin-main">
                    <strong>${escapeHtml(user.email)}</strong>
                    <span>${String(user.role || user.plan).toUpperCase()} · <span class="${statusClass}">${String(user.status || '').toUpperCase()}</span> · ${expiry}</span>
                </div>
                <div class="account-admin-actions">
                    <button type="button" class="panel-btn" data-admin-action="active">ACTIVE</button>
                    <button type="button" class="panel-btn" data-admin-action="trial">TRIAL</button>
                    <button type="button" class="panel-btn" data-admin-action="expire">EXPIRE</button>
                    <button type="button" class="panel-btn" data-admin-action="owner">OWNER</button>
                </div>
            </div>
        `;
    }).join('');
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

async function fetchAdminUsers() {
    if (accountState.account?.role !== 'owner') return;

    try {
        setAccountMessage('Chargement admin...');
        const response = await fetch('/api/admin/users', { cache: 'no-store' });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || 'Admin indisponible');
        }

        adminUsers = payload.users || [];
        renderAdminUsers();
        setAccountMessage('Admin synchronise.', 'ok');
    } catch (error) {
        setAccountMessage(error.message || 'Erreur admin', 'err');
    }
}

async function updateAdminUserAccess(userId, action) {
    try {
        setAccountMessage('Mise a jour utilisateur...');
        const response = await fetch(`/api/admin/users/${userId}/access`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || 'Action admin impossible');
        }

        adminUsers = adminUsers.map((user) => user.id === payload.user.id ? payload.user : user);
        renderAdminUsers();
        setAccountMessage('Utilisateur mis a jour.', 'ok');
    } catch (error) {
        setAccountMessage(error.message || 'Erreur admin', 'err');
    }
}

function toggleAccountPanel(forceOpen = null, heroOpen = false) {
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

async function fetchAccountState() {
    try {
        const response = await fetch('/api/account/me', { cache: 'no-store' });
        const payload = await response.json();
        accountState = payload;
        if (accountState.authenticated && accountState.account?.prefs) {
            applyLoadedPrefs(accountState.account.prefs);
        }
        renderAccountState();
        if (hasTerminalAccess()) {
            bootTerminalApp();
        }
    } catch (error) {
        console.error(error);
    }
}

async function submitAccountForm(event) {
    event.preventDefault();

    const emailEl = document.getElementById('account-email');
    const passwordEl = document.getElementById('account-password');
    if (!emailEl || !passwordEl) return;

    const email = emailEl.value.trim().toLowerCase();
    const password = passwordEl.value;
    if (!email || !password) return;

    try {
        setAccountMessage('Connexion en cours...');
        const response = await fetch(`/api/account/${accountMode}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || 'Action impossible');
        }

        accountState = payload;
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

async function submitAccessAuthForm(event) {
    event.preventDefault();

    const emailEl = document.getElementById('access-auth-email');
    const passwordEl = document.getElementById('access-auth-password');
    if (!emailEl || !passwordEl) return;

    const email = emailEl.value.trim().toLowerCase();
    const password = passwordEl.value;
    if (!email || !password) return;

    try {
        setAccessAuthMessage(accessFormMode === 'login' ? 'Connexion en cours...' : 'Creation du compte...');
        const endpoint = accessFormMode === 'login' ? 'login' : 'register';
        const response = await fetch(`/api/account/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || 'Action impossible');
        }

        accountState = payload;
        renderAccountState();
        setAccessAuthMessage(accessFormMode === 'login' ? 'Connexion reussie.' : 'Compte cree. Essai active.', 'ok');
        await syncPreferences();
        emailEl.value = '';
        passwordEl.value = '';
        if (hasTerminalAccess()) {
            bootTerminalApp();
            accessFormMode = 'intro';
            renderAccessGate();
        }
    } catch (error) {
        setAccessAuthMessage(error.message || 'Erreur compte', 'err');
    }
}

async function logoutAccount() {
    try {
        await fetch('/api/account/logout', { method: 'POST' });
        window.location.reload();
    } catch (error) {
        setAccountMessage('Impossible de fermer la session.', 'err');
    }
}

function bindAccountControls() {
    const toggle = document.getElementById('account-toggle');
    const form = document.getElementById('account-form');
    const switchBtn = document.getElementById('account-switch');
    const logoutBtn = document.getElementById('account-logout');
    const syncBtn = document.getElementById('account-sync');
    const adminToggle = document.getElementById('account-admin-toggle');
    const adminRefresh = document.getElementById('account-admin-refresh');
    const adminList = document.getElementById('account-admin-list');
    const panel = document.getElementById('account-panel');
    const startTrialBtn = document.getElementById('access-start-trial');
    const loginBtn = document.getElementById('access-login');
    const accessForm = document.getElementById('access-auth-form');
    const accessSwitchBtn = document.getElementById('access-auth-switch');
    const accessBackBtn = document.getElementById('access-back');

    if (toggle) {
        toggle.addEventListener('click', () => {
            toggleAccountPanel(null, false);
            renderAccountState();
        });
    }
    if (form) form.addEventListener('submit', submitAccountForm);
    if (switchBtn) {
        switchBtn.addEventListener('click', () => {
            setAccountMode(accountMode === 'login' ? 'register' : 'login');
            setAccountMessage('');
        });
    }
    if (logoutBtn) logoutBtn.addEventListener('click', logoutAccount);
    if (syncBtn) {
        syncBtn.addEventListener('click', async () => {
            await syncPreferences();
            setAccountMessage('Preferences synchronisees.', 'ok');
        });
    }
    if (adminToggle) {
        adminToggle.addEventListener('click', async () => {
            adminPanelOpen = !adminPanelOpen;
            renderAccountState();
            if (adminPanelOpen) {
                await fetchAdminUsers();
            }
        });
    }
    if (adminRefresh) adminRefresh.addEventListener('click', fetchAdminUsers);
    if (adminList) {
        adminList.addEventListener('click', (event) => {
            const button = event.target.closest('[data-admin-action]');
            const row = event.target.closest('[data-user-id]');
            if (!button || !row) return;
            updateAdminUserAccess(Number(row.dataset.userId), button.dataset.adminAction);
        });
    }
    if (startTrialBtn) {
        startTrialBtn.addEventListener('click', () => {
            setAccessFormMode('register');
            setAccessAuthMessage('');
        });
    }
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            setAccessFormMode('login');
            setAccessAuthMessage('');
        });
    }
    if (accessForm) accessForm.addEventListener('submit', submitAccessAuthForm);
    if (accessSwitchBtn) {
        accessSwitchBtn.addEventListener('click', () => {
            setAccessFormMode(accessFormMode === 'login' ? 'register' : 'login');
            setAccessAuthMessage('');
        });
    }
    if (accessBackBtn) {
        accessBackBtn.addEventListener('click', () => {
            setAccessFormMode('intro');
            setAccessAuthMessage('');
        });
    }

    document.addEventListener('click', (event) => {
        if (!panel || panel.classList.contains('hidden')) return;
        const slot = document.querySelector('.account-slot');
        if (slot && !slot.contains(event.target)) {
            toggleAccountPanel(false, false);
        }
    });

    renderAccountState();
    setAccountMode(accountMode);
    setAccessFormMode('intro');
    renderAccessGate();
}

function updateToggleButtons(panel, collapsed) {
    document.querySelectorAll(`.panel-btn[data-toggle-panel="${panel}"]`).forEach((button) => {
        button.textContent = collapsed ? '+' : '-';
        button.title = collapsed ? 'Ouvrir le panel' : 'Reduire le panel';
    });
}

function applyLayoutState() {
    const root = document.documentElement;
    const mainLayout = document.querySelector('.main-layout');
    const centerShell = document.querySelector('.center-shell');

    root.style.setProperty('--left-width', `${layoutState.leftWidth}px`);
    root.style.setProperty('--right-width', `${layoutState.rightWidth}px`);
    root.style.setProperty('--insight-width', `${layoutState.insightWidth}px`);

    if (mainLayout) {
        mainLayout.dataset.leftCollapsed = String(layoutState.collapsed.left);
        mainLayout.dataset.rightCollapsed = String(layoutState.collapsed.right);
    }

    if (centerShell) {
        centerShell.dataset.chartCollapsed = String(layoutState.collapsed.chart);
        centerShell.dataset.insightCollapsed = String(layoutState.collapsed.insight);
    }

    ['left', 'right', 'chart', 'insight'].forEach((panel) => {
        const el = document.querySelector(`[data-layout-panel="${panel}"]`);
        if (el) {
            el.dataset.collapsed = String(layoutState.collapsed[panel]);
        }
        updateToggleButtons(panel, layoutState.collapsed[panel]);
    });
}

function togglePanel(panel) {
    if (panel === 'chart' && !layoutState.collapsed.chart && layoutState.collapsed.insight) {
        layoutState.collapsed.insight = false;
    }
    if (panel === 'insight' && !layoutState.collapsed.insight && layoutState.collapsed.chart) {
        layoutState.collapsed.chart = false;
    }

    layoutState.collapsed[panel] = !layoutState.collapsed[panel];
    applyLayoutState();
    persistLayout();
}

function resetLayout() {
    layoutState = {
        leftWidth: DEFAULT_LAYOUT.leftWidth,
        rightWidth: DEFAULT_LAYOUT.rightWidth,
        insightWidth: DEFAULT_LAYOUT.insightWidth,
        collapsed: { ...DEFAULT_LAYOUT.collapsed },
    };
    applyLayoutState();
    persistLayout();
}

function bindLayoutControls() {
    document.querySelectorAll('[data-toggle-panel]').forEach((button) => {
        button.addEventListener('click', () => {
            const panel = button.dataset.togglePanel;
            if (!panel) return;
            togglePanel(panel);
        });
    });

    ['layout-reset', 'layout-reset-status'].forEach((id) => {
        const button = document.getElementById(id);
        if (!button) return;
        button.addEventListener('click', resetLayout);
    });

    applyLayoutState();
}

function bindResizers() {
    document.querySelectorAll('[data-resize]').forEach((handle) => {
        handle.addEventListener('pointerdown', (event) => {
            const mode = handle.dataset.resize;
            const mainLayout = document.querySelector('.main-layout');
            const centerShell = document.querySelector('.center-shell');

            if (!mode || !mainLayout || !centerShell) return;
            if ((mode === 'left' || mode === 'right') && window.innerWidth < 1180) return;
            if (mode === 'insight' && (window.innerWidth < 1400 || layoutState.collapsed.chart || layoutState.collapsed.insight)) return;

            event.preventDefault();
            handle.classList.add('dragging');

            const onMove = (moveEvent) => {
                if (mode === 'left') {
                    const rect = mainLayout.getBoundingClientRect();
                    layoutState.leftWidth = clamp(moveEvent.clientX - rect.left, 260, 520);
                } else if (mode === 'right') {
                    const rect = mainLayout.getBoundingClientRect();
                    layoutState.rightWidth = clamp(rect.right - moveEvent.clientX, 260, 520);
                } else if (mode === 'insight') {
                    const rect = centerShell.getBoundingClientRect();
                    layoutState.insightWidth = clamp(rect.right - moveEvent.clientX, 260, Math.min(520, rect.width - 260));
                }

                applyLayoutState();
            };

            const onUp = () => {
                handle.classList.remove('dragging');
                window.removeEventListener('pointermove', onMove);
                window.removeEventListener('pointerup', onUp);
                persistLayout();
            };

            window.addEventListener('pointermove', onMove);
            window.addEventListener('pointerup', onUp);
        });
    });
}

function setCenterTab(tab) {
    currentCenterTab = tab;
    savePrefs({ centerTab: tab });

    document.querySelectorAll('[data-center-tab]').forEach((button) => {
        button.classList.toggle('active', button.dataset.centerTab === tab);
    });

    document.querySelectorAll('[data-panel]').forEach((panel) => {
        panel.classList.toggle('active', panel.dataset.panel === tab);
    });
}

function bindCenterTabs() {
    const tabs = document.querySelectorAll('[data-center-tab]');
    if (!tabs.length) return;

    tabs.forEach((button) => {
        button.addEventListener('click', () => {
            const { centerTab } = button.dataset;
            if (!centerTab) return;
            setCenterTab(centerTab);
        });
    });

    setCenterTab(currentCenterTab);
}

function initChart(symbol) {
    currentSymbol = symbol;

    const wrap = document.getElementById('tv_main_wrap');
    if (!wrap) return;

    wrap.innerHTML = '<div id="tv_main" style="height:100%;"></div>';

    const symbolLabel = document.getElementById('chart-symbol');
    if (symbolLabel) {
        symbolLabel.textContent = symbol;
    }

    new TradingView.widget({
        autosize: true,
        symbol,
        interval: '1',
        theme: 'dark',
        style: '1',
        locale: 'fr',
        container_id: 'tv_main',
        hide_side_toolbar: false,
        allow_symbol_change: true,
        details: true,
        studies: ['Volume@tv-basicstudies'],
    });
}

function changeChart(symbol) {
    initChart(symbol);
    savePrefs({ symbol });

    document.querySelectorAll('.qcard').forEach((card) => {
        card.classList.toggle('active', card.dataset.symbol === symbol);
    });
}

function getTzParts(tz) {
    const formatter = new Intl.DateTimeFormat('en-GB', {
        timeZone: tz,
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });

    return Object.fromEntries(formatter.formatToParts(new Date()).map((part) => [part.type, part.value]));
}

function isMarketOpen(parts, market) {
    const nowMinutes = (Number(parts.hour) * 60) + Number(parts.minute);
    const openMinutes = (market.open[0] * 60) + market.open[1];
    const closeMinutes = (market.close[0] * 60) + market.close[1];
    return nowMinutes >= openMinutes && nowMinutes < closeMinutes;
}

function getActiveSessionLabel() {
    if (contextState?.session) {
        return contextState.session;
    }

    const hour = new Date().getHours();
    if (hour >= 14 && hour < 17) return 'LONDON / NEW YORK';
    if (hour >= 17 && hour < 22) return 'NEW YORK';
    if (hour >= 8 && hour < 14) return 'LONDON';
    return 'ASIA';
}

function updateClocks() {
    Object.entries(MARKETS).forEach(([key, market]) => {
        const parts = getTzParts(market.tz);
        const timeEl = document.getElementById(`time-${key}`);
        const clockEl = document.getElementById(`mk-${key}`);

        if (timeEl) {
            timeEl.textContent = `${parts.hour}:${parts.minute}:${parts.second}`;
        }
        if (clockEl) {
            clockEl.classList.toggle('open', isMarketOpen(parts, market));
        }
    });

    const statusClock = document.getElementById('status-clock');
    if (statusClock) {
        statusClock.textContent = new Intl.DateTimeFormat('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        }).format(new Date());
    }

    const sessionBadge = document.getElementById('session-badge');
    if (sessionBadge) {
        sessionBadge.textContent = getActiveSessionLabel();
    }
}

function formatValue(value, unit = '') {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    const text = typeof value === 'number' ? value.toLocaleString('en-US', { maximumFractionDigits: 3 }) : String(value);
    return unit ? `${text}${unit}` : text;
}

function formatSignedPercent(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return '-';
    }
    const num = Number(value);
    return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`;
}

function parseComparable(value) {
    if (value === null || value === undefined || value === '') {
        return NaN;
    }
    return Number.parseFloat(String(value).replace(/[^\d.-]/g, ''));
}

function getCalendarBiasClass(event) {
    const actual = parseComparable(event.actual);
    const forecast = parseComparable(event.forecast);
    if (Number.isNaN(actual) || Number.isNaN(forecast)) {
        return '';
    }

    const title = (event.title || '').toLowerCase();
    const negativeHigher = ['unemployment', 'claims', 'jobless', 'inventories', 'stock change'];
    const lowerIsBetter = negativeHigher.some((keyword) => title.includes(keyword));
    const betterThanForecast = lowerIsBetter ? actual < forecast : actual > forecast;

    if (actual === forecast) {
        return '';
    }
    return betterThanForecast ? 'cal-green' : 'cal-red';
}

function buildImpactDots(level) {
    return `<span class="cal-impact ${level.toLowerCase()}"><i></i><i></i><i></i></span>`;
}

function getDateKeyFromTs(ts, timeZone = 'Europe/Paris') {
    const formatter = new Intl.DateTimeFormat('en-CA', {
        timeZone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    });
    return formatter.format(new Date(ts * 1000));
}

function getDateKeyFromIso(isoString, timeZone = 'Europe/Paris') {
    const date = new Date(isoString);
    return getDateKeyFromTs(Math.floor(date.getTime() / 1000), timeZone);
}

function addDays(date, days) {
    const next = new Date(date);
    next.setDate(next.getDate() + days);
    return next;
}

function renderCalendarFilters() {
    const root = document.getElementById('cal-filters');
    if (!root) return;

    root.innerHTML = IMPACT_LEVELS.map((level) => `
        <button class="cal-chip ${calFilters.impact.has(level) ? 'on' : ''}" data-impact="${level}" type="button">
            ${level}
        </button>
    `).join('');

    root.querySelectorAll('[data-impact]').forEach((button) => {
        button.addEventListener('click', () => {
            const { impact } = button.dataset;
            if (!impact) return;

            if (calFilters.impact.has(impact) && calFilters.impact.size > 1) {
                calFilters.impact.delete(impact);
            } else {
                calFilters.impact.add(impact);
            }

            savePrefs({ impactFilters: [...calFilters.impact] });
            renderCalendarFilters();
            renderCalendar();
        });
    });
}

function renderWeekRange() {
    const weekEl = document.getElementById('week-range');
    if (!weekEl) return;

    if (!calendarMeta.weekStart || !calendarMeta.weekEnd) {
        weekEl.textContent = 'SEMAINE EN COURS';
        return;
    }

    const start = new Date(calendarMeta.weekStart);
    const end = addDays(new Date(calendarMeta.weekEnd), -1);
    const startLabel = start.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' });
    const endLabel = end.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
    weekEl.textContent = `SEMAINE DU ${startLabel.toUpperCase()} AU ${endLabel.toUpperCase()}`;
}

function renderCalendar() {
    const root = document.getElementById('calendar-content');
    if (!root) return;

    renderWeekRange();

    if (calendarMeta.error && calEvents.length === 0) {
        root.innerHTML = `<div class="cal-empty">Erreur calendrier: ${calendarMeta.error}</div>`;
        return;
    }

    if (!Array.isArray(calEvents) || calEvents.length === 0) {
        root.innerHTML = '<div class="cal-empty">Aucun evenement sur la semaine en cours.</div>';
        return;
    }

    const filtered = calEvents.filter((event) => calFilters.impact.has(event.impact));
    if (filtered.length === 0) {
        root.innerHTML = '<div class="cal-empty">Aucun evenement pour ce filtre.</div>';
        return;
    }

    const nowTs = Math.floor(Date.now() / 1000);
    const timeZone = calendarMeta.timezone || 'Europe/Paris';
    const eventsByDay = new Map();

    filtered.forEach((event) => {
        const key = getDateKeyFromTs(event.ts, timeZone);
        if (!eventsByDay.has(key)) {
            eventsByDay.set(key, []);
        }
        eventsByDay.get(key).push(event);
    });

    let weekStartDate = calendarMeta.weekStart ? new Date(calendarMeta.weekStart) : null;
    if (!weekStartDate || Number.isNaN(weekStartDate.getTime())) {
        const fallback = new Date();
        const offset = (fallback.getDay() + 6) % 7;
        fallback.setHours(0, 0, 0, 0);
        fallback.setDate(fallback.getDate() - offset);
        weekStartDate = fallback;
    }

    let html = '';

    for (let index = 0; index < 7; index += 1) {
        const dayDate = addDays(weekStartDate, index);
        const dayLabel = dayDate.toLocaleDateString('fr-FR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
        });
        const dayKey = getDateKeyFromIso(dayDate.toISOString(), timeZone);
        const dayEvents = eventsByDay.get(dayKey) || [];

        html += `<div class="cal-day">${dayLabel}</div>`;

        if (dayEvents.length === 0) {
            html += `
            <div class="cal-row cal-row-empty">
                <span class="cal-time">--:--</span>
                <span class="cal-flag">-</span>
                <span class="cal-title">
                    <span class="cal-title-text">Aucun evenement programme</span>
                </span>
                <span class="cal-num">-</span>
                <span class="cal-num">-</span>
                <span class="cal-num">-</span>
            </div>`;
            continue;
        }

        dayEvents.forEach((event) => {
            const dt = new Date(event.ts * 1000);
            const time = dt.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit',
                timeZone,
            });

            const dueSoon = event.ts >= nowTs && event.ts - nowTs <= 1800;
            const isPast = event.ts < nowTs;
            const rowClasses = [
                'cal-row',
                getCalendarBiasClass(event),
                dueSoon ? 'due' : '',
                isPast ? 'past' : '',
            ].filter(Boolean).join(' ');

            html += `
            <div class="${rowClasses}">
                <span class="cal-time">${time}</span>
                <span class="cal-flag">${event.country || '-'}</span>
                <span class="cal-title">
                    ${buildImpactDots(event.impact)}
                    <span class="cal-title-text">${event.title || '-'}</span>
                </span>
                <span class="cal-num">${formatValue(event.actual, event.unit)}</span>
                <span class="cal-num">${formatValue(event.forecast, event.unit)}</span>
                <span class="cal-num">${formatValue(event.previous, event.unit)}</span>
            </div>`;
        });
    }

    root.innerHTML = html;
}

function updateCalendarStatus(meta) {
    const liveEl = document.getElementById('cal-live');
    if (!liveEl) return;

    if (meta.error) {
        liveEl.textContent = 'ERROR';
        liveEl.style.color = '#ff4d6d';
        return;
    }

    liveEl.textContent = meta.hot ? 'HOT' : 'LIVE';
    liveEl.style.color = meta.hot ? '#f59e0b' : '#22c55e';
}

async function fetchCalendar() {
    try {
        const response = await fetch('/api/calendar', { cache: 'no-store' });
        const payload = await response.json();

        calEvents = Array.isArray(payload.events) ? payload.events : [];
        calendarMeta = {
            timezone: payload.timezone || 'Europe/Paris',
            error: payload.error || null,
            count: payload.count || 0,
            hot: !!payload.hot,
            weekStart: payload.week_start || null,
            weekEnd: payload.week_end || null,
        };

        updateCalendarStatus(calendarMeta);
        renderCalendar();
    } catch (error) {
        console.error(error);
        calendarMeta = { timezone: 'Europe/Paris', error: 'Requete impossible', count: 0, hot: false, weekStart: null, weekEnd: null };
        calEvents = [];
        updateCalendarStatus(calendarMeta);
        renderCalendar();
    }

    window.setTimeout(fetchCalendar, CALENDAR_REFRESH_MS);
}

function renderBiasCard(context) {
    const card = document.getElementById('bias-card');
    const scoreEl = document.getElementById('bias-score');
    const labelEl = document.getElementById('bias-label');
    const toneEl = document.getElementById('bias-tone');
    const reasonsEl = document.getElementById('bias-reasons');
    const confidenceEl = document.getElementById('confidence-badge');
    const volEl = document.getElementById('volatility-badge');
    const sessionEl = document.getElementById('session-active');
    const statusContext = document.getElementById('status-context');
    const snapshotBias = document.getElementById('snapshot-bias');
    const snapshotSession = document.getElementById('snapshot-session');
    const snapshotVol = document.getElementById('snapshot-vol');

    if (!card || !scoreEl || !labelEl || !toneEl || !reasonsEl || !confidenceEl || !volEl || !sessionEl) return;

    const toneClass = context.bias === 'Bullish' ? 'bullish' : context.bias === 'Bearish' ? 'bearish' : 'neutral';
    card.classList.remove('bullish', 'bearish', 'neutral');
    card.classList.add(toneClass);

    scoreEl.textContent = `${context.score > 0 ? '+' : ''}${Number(context.score).toFixed(1)}`;
    scoreEl.className = `desk-pill ${toneClass}`;
    labelEl.textContent = context.bias.toUpperCase();
    labelEl.className = `bias-label ${toneClass}`;
    toneEl.textContent = `${context.tone.toUpperCase()} - ${context.summary || (context.gold ? `Gold ${formatSignedPercent(context.gold.change_pct)}` : 'Gold feed live')}`;
    reasonsEl.innerHTML = (context.reasons || []).slice(0, 3).map((reason) => `<span class="bias-reason">${reason}</span>`).join('');
    confidenceEl.textContent = `CONF ${context.confidence || 0}%`;
    confidenceEl.className = `desk-pill ${toneClass}`;
    volEl.textContent = `VOL ${context.volatility}`;
    sessionEl.textContent = context.session;

    if (snapshotBias) {
        snapshotBias.textContent = `${context.bias.toUpperCase()} ${context.score > 0 ? '+' : ''}${Number(context.score).toFixed(1)}`;
        snapshotBias.className = `desk-pill ${toneClass}`;
    }
    if (snapshotSession) {
        snapshotSession.textContent = context.session || 'SESSION -';
    }
    if (snapshotVol) {
        snapshotVol.textContent = `VOL ${context.volatility || '-'}`;
    }

    if (statusContext) {
        statusContext.textContent = `Bias: ${context.bias} (${context.score > 0 ? '+' : ''}${Number(context.score).toFixed(1)}) - ${context.confidence || 0}%`;
    }
}

function renderDrivers(context) {
    const root = document.getElementById('drivers-grid');
    if (!root) return;

    root.innerHTML = (context.drivers || []).map((driver) => `
        <div class="driver-item ${driver.bias}">
            <div class="driver-top">
                <span class="driver-label">${driver.label}</span>
                <span class="driver-change ${driver.bias}">${formatSignedPercent(driver.change_pct)}</span>
            </div>
            <div class="driver-value">${formatValue(driver.value)}</div>
            <div class="driver-note">${driver.note}</div>
        </div>
    `).join('');
}

function renderWatchlist(context) {
    const root = document.getElementById('watchlist-grid');
    if (!root) return;

    root.innerHTML = (context.watchlist || []).map((item) => {
        const direction = item.change_pct > 0 ? 'up' : item.change_pct < 0 ? 'down' : 'flat';
        return `
        <button type="button" class="watch-item" data-symbol="${item.symbol}">
            <span class="watch-label">${item.label}</span>
            <span class="watch-price">${formatValue(item.price)}</span>
            <span class="watch-change ${direction}">${formatSignedPercent(item.change_pct)}</span>
        </button>`;
    }).join('');

    root.querySelectorAll('[data-symbol]').forEach((button) => {
        button.addEventListener('click', () => {
            const symbol = button.dataset.symbol;
            if (!symbol) return;

            const tvMap = {
                'GC=F': 'COMEX:GC1!',
                'SI=F': 'COMEX:SI1!',
                'DX-Y.NYB': 'CAPITALCOM:DXY',
                '^TNX': 'TVC:US10Y',
                'CL=F': 'NYMEX:CL1!',
                'SPY': 'AMEX:SPY',
                'QQQ': 'NASDAQ:QQQ',
            };
            changeChart(tvMap[symbol] || symbol);
        });
    });
}

async function fetchContext() {
    try {
        const response = await fetch('/api/context', { cache: 'no-store' });
        const payload = await response.json();
        contextState = payload;
        renderBiasCard(payload);
        renderDrivers(payload);
        renderWatchlist(payload);
        updateClocks();
    } catch (error) {
        console.error(error);
    }

    window.setTimeout(fetchContext, CONTEXT_REFRESH_MS);
}

function sourceClass(source) {
    return source.replace(/[^A-Z0-9_-]/gi, '_');
}

function renderNewsSummaries(items) {
    const priorityEl = document.getElementById('news-priority-summary');
    const officialEl = document.getElementById('official-summary');
    if (!priorityEl || !officialEl) return;

    const high = items.filter((item) => item.priority === 'high').length;
    const official = items.filter((item) => (item.tags || []).includes('OFFICIAL')).length;

    priorityEl.textContent = `HIGH ${high}`;
    officialEl.textContent = `OFFICIAL ${official}`;
}

async function getNews() {
    try {
        const response = await fetch('/api/news');
        const data = await response.json();
        const items = data.items || [];
        const container = document.getElementById('news-content');

        if (!container) return;
        container.innerHTML = '';

        let freshCount = 0;
        renderNewsSummaries(items);

        items.forEach((itemData) => {
            const item = document.createElement('div');
            const isFresh = itemData.ts > lastSeenNewsTs;
            if (isFresh) {
                freshCount += 1;
            }

            item.className = `n-item ${itemData.priority || 'low'}${itemData.crit ? ' critical' : ''}${isFresh ? ' fresh' : ''}`;

            const meta = document.createElement('div');
            meta.className = 'n-meta';

            const time = document.createElement('span');
            time.textContent = itemData.time;

            const source = document.createElement('span');
            source.className = `tag ${sourceClass(itemData.s)}`;
            source.textContent = itemData.s;

            const priority = document.createElement('span');
            priority.className = `tag priority ${itemData.priority || 'low'}`;
            priority.textContent = (itemData.priority || 'low').toUpperCase();

            meta.appendChild(time);
            meta.appendChild(source);
            meta.appendChild(priority);

            (itemData.tags || []).slice(0, 3).forEach((tagName) => {
                const tag = document.createElement('span');
                tag.className = `tag topic ${tagName.toLowerCase()}`;
                tag.textContent = tagName;
                meta.appendChild(tag);
            });

            const link = document.createElement('a');
            link.href = itemData.l;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = itemData.t;

            item.appendChild(meta);
            item.appendChild(link);
            container.appendChild(item);
        });

        if (items.length) {
            lastSeenNewsTs = Math.max(lastSeenNewsTs, items[0].ts || 0);
        }

        const statusNews = document.getElementById('status-news');
        if (statusNews) {
            const highCount = items.filter((item) => item.priority === 'high').length;
            statusNews.textContent = `News: ${items.length} items - high ${highCount}${data.cached ? ` - cache ${data.age}s` : ''}`;
        }

        if (freshCount > 0) {
            ensureAudio();
            beep();
        }
    } catch (error) {
        console.error(error);
        const statusNews = document.getElementById('status-news');
        if (statusNews) {
            statusNews.textContent = 'News: erreur de chargement';
        }
    }
}

function bindQuoteCards() {
    document.querySelectorAll('.qcard').forEach((card) => {
        card.addEventListener('click', () => {
            const symbol = card.dataset.symbol;
            if (symbol) {
                changeChart(symbol);
            }
        });
    });
}

function bindCommandInput() {
    const input = document.getElementById('cmd');
    if (!input) return;

    input.value = currentSymbol;
    input.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') return;

        const value = input.value.trim().toUpperCase();
        if (!value) return;
        changeChart(value);
    });
}

function bindSoundPicker() {
    const select = document.getElementById('sound-pick');
    if (!select) return;

    select.value = soundType;
    select.addEventListener('change', () => {
        soundType = select.value;
        savePrefs({ soundType });
        ensureAudio();
        beep();
    });
}

function bindSoundToggle() {
    const soundEl = document.getElementById('status-sound');
    if (!soundEl) return;

    soundEl.addEventListener('click', () => {
        soundEnabled = !soundEnabled;
        savePrefs({ soundEnabled });
        renderSoundToggle();
        ensureAudio();
        beep();
    });
}

function init() {
    renderSoundToggle();
    renderCalendarFilters();
    bindQuoteCards();
    bindAccountControls();
    bindLayoutControls();
    bindResizers();
    bindCenterTabs();
    bindCommandInput();
    bindSoundPicker();
    bindSoundToggle();

    fetchAccountState();
    updateClocks();

    window.setInterval(updateClocks, 1000);
    window.addEventListener('resize', applyLayoutState);
}

init();
