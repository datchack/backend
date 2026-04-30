import {
    CALENDAR_REFRESH_MS,
    CONTEXT_REFRESH_MS,
    DEFAULT_ACCOUNT_MODE,
    DEFAULT_MARKET_PROFILE,
    DEFAULT_WIDGETS,
    IMPACT_LEVELS,
    MARKETS,
    MARKET_PROFILES,
    NEWS_REFRESH_MS,
    PREFS_KEY,
    QUOTES_REFRESH_MS,
} from './terminal-config.js';
import { fetchAccount, logoutAccountSession, saveAccountPreferences, submitAccountAuth } from './terminal-account-api.js';
import {
    bindAccountControls as bindAccountControlsModule,
    hasTerminalAccess as accountHasTerminalAccess,
    renderAccessGate as renderAccessGateView,
    renderAccountState as renderAccountStateView,
    setAccessAuthMessage,
    setAccountMessage,
    toggleAccountPanel as toggleAccountPanelView,
} from './terminal-account-ui.js';
import {
    renderCalendar as renderCalendarView,
    renderCalendarFilters as renderCalendarFilterView,
    updateCalendarStatus,
} from './terminal-calendar.js';
import {
    bindCenterTabs as bindCenterTabsModule,
    bindCommandInput as bindCommandInputModule,
    bindMarketProfileControls as bindMarketProfileControlsModule,
    changeChart as changeChartView,
    initChart as initChartView,
    renderMarketProfileSelect as renderMarketProfileSelectView,
    setCenterTab as setCenterTabView,
    syncCommandSymbol,
} from './terminal-chart.js';
import { getTzParts, isMarketOpen } from './terminal-clocks.js';
import { renderMarketContext, renderWatchlist } from './terminal-context-ui.js';
import {
    bindCustomizeControls as bindCustomizeControlsModule,
    renderCustomizePanel as renderCustomizePanelView,
} from './terminal-customize.js';
import {
    applyLayoutState,
    applyWidgetVisibility,
    bindLayoutControls as bindLayoutControlsModule,
    bindResizers as bindResizersModule,
    loadLayoutPrefs,
} from './terminal-layout.js';
import { fetchCalendarFeed, fetchMarketContext, fetchNewsFeed } from './terminal-market-api.js';
import { renderNewsError, renderNewsFeed } from './terminal-news.js';
import { loadStoredPrefs, mergeStoredPrefs, writeStoredPrefs } from './terminal-prefs.js';
import { bindQuoteCards, startQuotesRefresh } from './terminal-quotes.js';
import {
    beep as playNotificationSound,
    bindSoundPicker as bindSoundPickerControl,
    bindSoundToggle as bindSoundToggleControl,
    ensureAudio,
    renderSoundToggle as renderSoundToggleControl,
    syncSoundPicker,
} from './terminal-sound.js';

function loadPrefs() {
    return loadStoredPrefs(PREFS_KEY);
}

function savePrefs(patch) {
    try {
        const next = mergeStoredPrefs(PREFS_KEY, patch);
        schedulePrefsSync(next);
    } catch {}
}

const PREFS = loadPrefs();
let currentMarketProfile = PREFS.marketProfile || DEFAULT_MARKET_PROFILE;
let currentSymbol = PREFS.symbol || MARKET_PROFILES[currentMarketProfile]?.symbol || MARKET_PROFILES[DEFAULT_MARKET_PROFILE].symbol;
let soundEnabled = !!PREFS.soundEnabled;
let soundType = PREFS.soundType || 'chime';
let currentCenterTab = PREFS.centerTab || 'bias';
let customCalendarCountries = Array.isArray(PREFS.calendarCountries) ? PREFS.calendarCountries : null;
let customWatchlistKeys = Array.isArray(PREFS.watchlistKeys) ? PREFS.watchlistKeys : null;
let widgetVisibility = { ...DEFAULT_WIDGETS, ...(PREFS.widgets || {}) };
let layoutState = loadLayoutPrefs(PREFS.layout);
let accountMode = DEFAULT_ACCOUNT_MODE;
let accountState = { authenticated: false, account: null, loading: true };
let prefsSyncTimer = null;
let appBooted = false;
let accessFormMode = 'intro';
let lastSeenNewsTs = 0;
let hasLoadedNews = false;
let suppressNextNewsFresh = false;
let alertedNewsIds = new Set();
let calEvents = [];
let contextState = null;
let calendarMeta = { timezone: 'Europe/Paris', error: null, count: 0, weekStart: null, weekEnd: null, refreshMs: CALENDAR_REFRESH_MS };
let calendarRefreshTimer = null;
let contextRefreshTimer = null;

const calFilters = {
    impact: new Set(PREFS.impactFilters || IMPACT_LEVELS),
};

function persistLayout() {
    savePrefs({ layout: layoutState });
}

function getClientPrefsSnapshot() {
    return {
        ...loadPrefs(),
        marketProfile: currentMarketProfile,
        symbol: currentSymbol,
        soundEnabled,
        soundType,
        centerTab: currentCenterTab,
        impactFilters: [...calFilters.impact],
        calendarCountries: getCalendarCountries(),
        watchlistKeys: customWatchlistKeys,
        widgets: widgetVisibility,
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
        await saveAccountPreferences(prefs || getClientPrefsSnapshot());
    } catch (error) {
        console.error(error);
    }
}

function applyLoadedPrefs(prefs = {}) {
    if (!prefs || typeof prefs !== 'object') return;

    writeStoredPrefs(PREFS_KEY, prefs);

    currentMarketProfile = prefs.marketProfile || currentMarketProfile;
    currentSymbol = prefs.symbol || MARKET_PROFILES[currentMarketProfile]?.symbol || currentSymbol;
    soundEnabled = typeof prefs.soundEnabled === 'boolean' ? prefs.soundEnabled : soundEnabled;
    soundType = prefs.soundType || soundType;
    currentCenterTab = prefs.centerTab || currentCenterTab;
    customCalendarCountries = Array.isArray(prefs.calendarCountries) ? prefs.calendarCountries : customCalendarCountries;
    customWatchlistKeys = Array.isArray(prefs.watchlistKeys) ? prefs.watchlistKeys : customWatchlistKeys;
    widgetVisibility = { ...DEFAULT_WIDGETS, ...(prefs.widgets || widgetVisibility) };
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

    renderSoundToggleControl(soundEnabled);
    renderCalendarFilters();
    syncSoundPicker(soundType);
    const cmdInput = document.getElementById('cmd');
    if (cmdInput) cmdInput.value = currentSymbol;
    renderMarketProfileSelect();
    renderCustomizePanel();
    applyWidgetVisibility(widgetVisibility);
    setCenterTab(currentCenterTab);
    applyLayoutState(layoutState);
    if (appBooted) {
        changeChart(currentSymbol);
    }
}

function hasTerminalAccess() {
    return accountHasTerminalAccess(accountState);
}

function renderAccessGate() {
    renderAccessGateView(accountState, accessFormMode);
}

function bootTerminalApp() {
    if (appBooted) return;
    appBooted = true;

    renderMarketProfileSelect();
    initChart(currentSymbol);
    startQuotesRefresh({
        hasAccess: hasTerminalAccess,
        getCurrentSymbol: () => currentSymbol,
    });
    getNews();
    fetchCalendar();
    fetchContext();
    window.setInterval(getNews, NEWS_REFRESH_MS);
}

function getActiveMarketProfile() {
    return MARKET_PROFILES[currentMarketProfile] || MARKET_PROFILES[DEFAULT_MARKET_PROFILE];
}

function getProfileQuery() {
    return encodeURIComponent(getActiveMarketProfile().id);
}

function getCalendarCountries() {
    const profileCountries = getActiveMarketProfile().countries || ['US'];
    return Array.isArray(customCalendarCountries) && customCalendarCountries.length
        ? customCalendarCountries
        : profileCountries;
}

function getCalendarCountryQuery() {
    return encodeURIComponent(getCalendarCountries().join(','));
}

function renderMarketProfileSelect() {
    renderMarketProfileSelectView(MARKET_PROFILES, currentMarketProfile);
}

function setMarketProfile(profileId) {
    const profile = MARKET_PROFILES[profileId] || MARKET_PROFILES[DEFAULT_MARKET_PROFILE];
    currentMarketProfile = profile.id;
    currentSymbol = profile.symbol;
    suppressNextNewsFresh = true;

    syncCommandSymbol(currentSymbol);

    changeChart(currentSymbol, { save: false });
    savePrefs({ marketProfile: currentMarketProfile, symbol: currentSymbol });
    renderCustomizePanel();
    getNews();
    fetchCalendar(false);
    fetchContext(false);
}

function beep() {
    playNotificationSound(soundEnabled, soundType);
}

function renderAccountState() {
    accountMode = renderAccountStateView(accountState, accountMode, accessFormMode);
}

function toggleAccountPanel(forceOpen = null, heroOpen = false) {
    toggleAccountPanelView(accountState, forceOpen, heroOpen);
}

async function fetchAccountState() {
    try {
        const payload = await fetchAccount();
        accountState = { ...payload, loading: false };
        if (accountState.authenticated && accountState.account?.prefs) {
            applyLoadedPrefs(accountState.account.prefs);
        }
        renderAccountState();
        if (hasTerminalAccess()) {
            bootTerminalApp();
        }
    } catch (error) {
        console.error(error);
        accountState = { authenticated: false, account: null, loading: false };
        renderAccountState();
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
        const payload = await submitAccountAuth(accountMode, email, password);

        accountState = { ...payload, loading: false };
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
        const payload = await submitAccountAuth(endpoint, email, password);

        accountState = { ...payload, loading: false };
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
        await logoutAccountSession();
        window.location.href = '/';
    } catch (error) {
        setAccountMessage('Impossible de fermer la session.', 'err');
    }
}

function bindAccountControls() {
    bindAccountControlsModule({
        getAccountState: () => accountState,
        getAccountMode: () => accountMode,
        setAccountModeState: (mode) => {
            accountMode = mode;
        },
        getAccessFormMode: () => accessFormMode,
        setAccessFormModeState: (mode) => {
            accessFormMode = mode;
        },
        renderAccount: renderAccountState,
        submitAccountForm,
        submitAccessAuthForm,
        logoutAccount,
        syncPreferences,
    });
}

function bindMarketProfileControls() {
    bindMarketProfileControlsModule({
        renderSelect: renderMarketProfileSelect,
        onChange: setMarketProfile,
    });
}

function bindLayoutControls() {
    bindLayoutControlsModule({
        getLayoutState: () => layoutState,
        setLayoutState: (nextLayoutState) => {
            layoutState = nextLayoutState;
        },
        persistLayout,
    });
}

function bindResizers() {
    bindResizersModule({
        getLayoutState: () => layoutState,
        persistLayout,
    });
}

function setCenterTab(tab) {
    currentCenterTab = tab;
    savePrefs({ centerTab: tab });
    setCenterTabView(tab);
}

function bindCenterTabs() {
    bindCenterTabsModule({
        getCurrentTab: () => currentCenterTab,
        onChange: setCenterTab,
    });
}

function initChart(symbol) {
    currentSymbol = symbol;
    initChartView(symbol);
}

function changeChart(symbol, options = {}) {
    currentSymbol = symbol;
    changeChartView(symbol);
    if (options.save !== false) {
        savePrefs({ symbol, marketProfile: currentMarketProfile });
    }
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

}

function handleCalendarFilterChange(impact) {
    if (calFilters.impact.has(impact) && calFilters.impact.size > 1) {
        calFilters.impact.delete(impact);
    } else {
        calFilters.impact.add(impact);
    }

    savePrefs({ impactFilters: [...calFilters.impact] });
    renderCalendarFilters();
    renderCalendar();
}

function renderCalendarFilters() {
    renderCalendarFilterView(calFilters, handleCalendarFilterChange);
}

function renderCalendar() {
    renderCalendarView(calEvents, calendarMeta, calFilters);
}

async function fetchCalendar(scheduleNext = true) {
    try {
        const payload = await fetchCalendarFeed(getProfileQuery(), getCalendarCountryQuery());

        calEvents = Array.isArray(payload.events) ? payload.events : [];
        calendarMeta = {
            timezone: payload.timezone || 'Europe/Paris',
            error: payload.error || null,
            count: payload.count || 0,
            hot: !!payload.hot,
            releaseWatch: !!payload.release_watch,
            refreshMs: Number(payload.refresh_ms) || CALENDAR_REFRESH_MS,
            weekStart: payload.week_start || null,
            weekEnd: payload.week_end || null,
        };

        updateCalendarStatus(calendarMeta);
        renderCalendar();
    } catch (error) {
        console.error(error);
        calendarMeta = { timezone: 'Europe/Paris', error: 'Requete impossible', count: 0, hot: false, releaseWatch: false, refreshMs: CALENDAR_REFRESH_MS, weekStart: null, weekEnd: null };
        calEvents = [];
        updateCalendarStatus(calendarMeta);
        renderCalendar();
    }

    if (scheduleNext) {
        window.clearTimeout(calendarRefreshTimer);
        calendarRefreshTimer = window.setTimeout(fetchCalendar, calendarMeta.refreshMs || CALENDAR_REFRESH_MS);
    }
}

function renderCustomizePanel() {
    renderCustomizePanelView({
        countries: getCalendarCountries(),
        context: contextState,
        selectedWatchlistKeys: customWatchlistKeys,
        widgetVisibility,
    });
}

function bindCustomizeControls() {
    bindCustomizeControlsModule({
        getCalendarCountries,
        getContext: () => contextState,
        getSelectedWatchlistKeys: () => customWatchlistKeys,
        getWidgetVisibility: () => widgetVisibility,
        setCalendarCountries: (countries) => {
            customCalendarCountries = countries;
        },
        setSelectedWatchlistKeys: (keys) => {
            customWatchlistKeys = keys;
        },
        setWidgetVisibility: (nextWidgetVisibility) => {
            widgetVisibility = nextWidgetVisibility;
        },
        savePrefs,
        applyWidgetVisibility,
        renderPanel: renderCustomizePanel,
        renderWatchlist,
        onSymbolSelect: changeChart,
        refreshCalendar: fetchCalendar,
        refreshContext: fetchContext,
    });
}

async function fetchContext(scheduleNext = true) {
    try {
        const payload = await fetchMarketContext(getProfileQuery(), getCalendarCountryQuery());
        contextState = payload;
        renderMarketContext(payload, { selectedKeys: customWatchlistKeys, onSymbolSelect: changeChart });
        renderCustomizePanel();
        updateClocks();
    } catch (error) {
        console.error(error);
    }

    if (scheduleNext) {
        window.clearTimeout(contextRefreshTimer);
        contextRefreshTimer = window.setTimeout(fetchContext, CONTEXT_REFRESH_MS);
    }
}

async function getNews() {
    try {
        const data = await fetchNewsFeed(getProfileQuery());
        const rendered = renderNewsFeed(data, {
            lastSeenTs: lastSeenNewsTs,
            hasLoaded: hasLoadedNews,
            suppressNextFresh: suppressNextNewsFresh,
            alertedNewsIds,
        });
        lastSeenNewsTs = rendered.state.lastSeenTs;
        hasLoadedNews = rendered.state.hasLoaded;
        suppressNextNewsFresh = rendered.state.suppressNextFresh;
        alertedNewsIds = rendered.state.alertedNewsIds;

        if (rendered.freshAlertCount > 0 && !rendered.suppressFresh) {
            ensureAudio();
            beep();
        }
    } catch (error) {
        console.error(error);
        renderNewsError();
    }
}

function bindCommandInput() {
    bindCommandInputModule({
        getCurrentSymbol: () => currentSymbol,
        onChange: changeChart,
    });
}

function bindSoundPicker() {
    bindSoundPickerControl({
        getSoundType: () => soundType,
        setSoundType: (nextSoundType) => {
            soundType = nextSoundType;
        },
        isSoundEnabled: () => soundEnabled,
        savePrefs,
    });
}

function bindSoundToggle() {
    bindSoundToggleControl({
        isSoundEnabled: () => soundEnabled,
        setSoundEnabled: (enabled) => {
            soundEnabled = enabled;
        },
        getSoundType: () => soundType,
        savePrefs,
    });
}

function init() {
    renderSoundToggleControl(soundEnabled);
    renderCalendarFilters();
    applyWidgetVisibility(widgetVisibility);
    renderCustomizePanel();
    bindMarketProfileControls();
    bindQuoteCards(changeChart);
    bindAccountControls();
    bindLayoutControls();
    bindResizers();
    bindCenterTabs();
    bindCommandInput();
    bindSoundPicker();
    bindSoundToggle();
    bindCustomizeControls();

    fetchAccountState();
    updateClocks();

    window.setInterval(updateClocks, 1000);
    window.addEventListener('resize', () => applyLayoutState(layoutState));
}

init();
