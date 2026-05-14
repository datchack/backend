import {
    CONTEXT_REFRESH_MS,
    DEFAULT_ACCOUNT_MODE,
    DEFAULT_MARKET_PROFILE,
    DEFAULT_WIDGETS,
    MARKETS,
    MARKET_CATEGORIES,
    MARKET_PROFILES,
    NEWS_REFRESH_MS,
    PREFS_KEY,
    WORKSPACE_PRESETS,
} from './terminal-config.js?v=20260514-workspace-presets';
import { saveAccountPreferences, syncBillingCheckoutSession } from './terminal-account-api.js?v=20260514-workspace-presets';
import {
    fetchAccountState as fetchAccountStateAction,
    submitAccessAuthForm as submitAccessAuthFormAction,
} from './terminal-account-actions.js?v=20260514-workspace-presets';
import {
    bindAccountControls as bindAccountControlsModule,
    hasTerminalAccess as accountHasTerminalAccess,
    renderAccessGate as renderAccessGateView,
    renderAccountState as renderAccountStateView,
    setAccessAuthMessage,
} from './terminal-account-ui.js?v=20260514-workspace-presets';
import { createCalendarController } from './terminal-calendar.js?v=20260514-workspace-presets';
import {
    bindCenterTabs as bindCenterTabsModule,
    bindCommandInput as bindCommandInputModule,
    bindMarketProfileControls as bindMarketProfileControlsModule,
    changeChart as changeChartView,
    initChart as initChartView,
    setCenterTab as setCenterTabView,
    syncCommandSymbol,
} from './terminal-chart.js?v=20260514-workspace-presets';
import { updateClocks as updateClocksView } from './terminal-clocks.js?v=20260514-workspace-presets';
import { renderMarketContext, renderWatchlist } from './terminal-context-ui.js?v=20260514-workspace-presets';
import {
    bindCustomizeControls as bindCustomizeControlsModule,
    renderCustomizePanel as renderCustomizePanelView,
} from './terminal-customize.js?v=20260514-workspace-presets';
import {
    applyLayoutState,
    applyWidgetVisibility,
    bindLayoutControls as bindLayoutControlsModule,
    bindResizers as bindResizersModule,
    loadLayoutPrefs,
} from './terminal-layout.js?v=20260514-workspace-presets';
import { fetchMarketContext, fetchNewsFeed } from './terminal-market-api.js?v=20260514-workspace-presets';
import { bindMarketSelector, renderWorkspacePresetSelect } from './terminal-market-selector.js?v=20260514-workspace-presets';
import { renderNewsError, renderNewsFeed } from './terminal-news.js?v=20260514-workspace-presets';
import { loadStoredPrefs, mergeStoredPrefs, writeStoredPrefs } from './terminal-prefs.js?v=20260514-workspace-presets';
import { bindQuoteCards, renderPersonalQuoteCards, startQuotesRefresh, syncActiveQuoteCard } from './terminal-quotes.js?v=20260514-workspace-presets';
import {
    beep as playNotificationSound,
    bindSoundPicker as bindSoundPickerControl,
    bindSoundToggle as bindSoundToggleControl,
    ensureAudio,
    renderSoundToggle as renderSoundToggleControl,
    syncSoundPicker,
} from './terminal-sound.js?v=20260514-workspace-presets';

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
const INITIAL_URL_SYMBOL = new URLSearchParams(window.location.search).get('symbol');
let currentMarketProfile = getProfileIdFromSymbol(INITIAL_URL_SYMBOL) || PREFS.marketProfile || DEFAULT_MARKET_PROFILE;
let currentSymbol = INITIAL_URL_SYMBOL || PREFS.symbol || MARKET_PROFILES[currentMarketProfile]?.symbol || MARKET_PROFILES[DEFAULT_MARKET_PROFILE].symbol;
let customContextSymbol = null;
let soundEnabled = !!PREFS.soundEnabled;
let soundType = PREFS.soundType || 'chime';
let currentCenterTab = PREFS.centerTab || 'bias';
let customCalendarCountries = Array.isArray(PREFS.calendarCountries) ? PREFS.calendarCountries : null;
let customWatchlistKeys = Array.isArray(PREFS.watchlistKeys) ? PREFS.watchlistKeys : null;
let quoteCards = Array.isArray(PREFS.quoteCards) ? PREFS.quoteCards : [];
let currentWorkspacePreset = WORKSPACE_PRESETS[PREFS.workspacePreset] ? PREFS.workspacePreset : '';
let marketFavorites = Array.isArray(PREFS.marketFavorites) ? PREFS.marketFavorites : ['xauusd', 'eurusd', 'usdjpy', 'gbpjpy'];
let marketRecents = Array.isArray(PREFS.marketRecents) ? PREFS.marketRecents : [];
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
let contextState = null;
let contextRefreshTimer = null;
let calendarController = null;

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
        impactFilters: calendarController?.getImpactFilters() || [],
        calendarCountries: getCalendarCountries(),
        watchlistKeys: customWatchlistKeys,
        quoteCards,
        workspacePreset: currentWorkspacePreset,
        marketFavorites,
        marketRecents,
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

    currentMarketProfile = getProfileIdFromSymbol(INITIAL_URL_SYMBOL) || prefs.marketProfile || currentMarketProfile;
    currentSymbol = INITIAL_URL_SYMBOL || prefs.symbol || MARKET_PROFILES[currentMarketProfile]?.symbol || currentSymbol;
    soundEnabled = typeof prefs.soundEnabled === 'boolean' ? prefs.soundEnabled : soundEnabled;
    soundType = prefs.soundType || soundType;
    currentCenterTab = prefs.centerTab || currentCenterTab;
    customCalendarCountries = Array.isArray(prefs.calendarCountries) ? prefs.calendarCountries : customCalendarCountries;
    customWatchlistKeys = Array.isArray(prefs.watchlistKeys) ? prefs.watchlistKeys : customWatchlistKeys;
    quoteCards = Array.isArray(prefs.quoteCards) ? prefs.quoteCards : quoteCards;
    currentWorkspacePreset = WORKSPACE_PRESETS[prefs.workspacePreset] ? prefs.workspacePreset : currentWorkspacePreset;
    marketFavorites = Array.isArray(prefs.marketFavorites) ? prefs.marketFavorites : marketFavorites;
    marketRecents = Array.isArray(prefs.marketRecents) ? prefs.marketRecents : marketRecents;
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

    calendarController?.setImpactFilters(prefs.impactFilters);

    renderSoundToggleControl(soundEnabled);
    renderCalendarFilters();
    syncSoundPicker(soundType);
    syncCommandSymbol(currentSymbol);
    renderMarketProfileSelect();
    renderCustomizePanel();
    renderPersonalQuoteCards(quoteCards, currentSymbol);
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
        getQuoteCards: () => quoteCards,
    });
    getNews();
    fetchCalendar();
    fetchContext();
    window.setInterval(getNews, NEWS_REFRESH_MS);
}

function getActiveMarketProfile() {
    return MARKET_PROFILES[currentMarketProfile] || MARKET_PROFILES[DEFAULT_MARKET_PROFILE];
}

function getContextSymbol() {
    return customContextSymbol || getActiveMarketProfile().symbol;
}

function normalizeTradingViewSymbol(symbol) {
    return String(symbol || '').split(':').pop().toUpperCase().replace(/[^A-Z0-9]/g, '');
}

function getProfileIdFromSymbol(symbol) {
    const normalized = normalizeTradingViewSymbol(symbol);
    if (!normalized) return null;
    return Object.values(MARKET_PROFILES).find((profile) => normalizeTradingViewSymbol(profile.symbol) === normalized)?.id || null;
}

const CURRENCY_COUNTRIES = {
    USD: 'US',
    EUR: 'EU',
    GBP: 'GB',
    JPY: 'JP',
    AUD: 'AU',
    CAD: 'CA',
    CHF: 'CH',
    NZD: 'NZ',
    CNY: 'CN',
    HKD: 'HK',
};

function parseForexSymbol(symbol) {
    const raw = String(symbol || '').split(':').pop().toUpperCase().replace(/[^A-Z]/g, '');
    if (raw.length !== 6) return null;
    const base = raw.slice(0, 3);
    const quote = raw.slice(3);
    if (!CURRENCY_COUNTRIES[base] || !CURRENCY_COUNTRIES[quote]) return null;
    return { base, quote };
}

function getProfileQuery() {
    return encodeURIComponent(getActiveMarketProfile().id);
}

function getCalendarCountries() {
    const profileCountries = getActiveMarketProfile().countries || ['US'];
    const forex = parseForexSymbol(getContextSymbol());
    const symbolCountries = forex
        ? [CURRENCY_COUNTRIES[forex.base], CURRENCY_COUNTRIES[forex.quote], 'US'].filter(Boolean)
        : profileCountries;
    return Array.isArray(customCalendarCountries) && customCalendarCountries.length
        ? customCalendarCountries
        : [...new Set(symbolCountries)].slice(0, 4);
}

function getCalendarCountryQuery() {
    return encodeURIComponent(getCalendarCountries().join(','));
}

calendarController = createCalendarController({
    initialImpactFilters: PREFS.impactFilters,
    getProfileQuery,
    getCalendarCountryQuery,
    savePrefs,
});

function renderMarketProfileSelect() {
    renderWorkspacePresetSelect(WORKSPACE_PRESETS, currentWorkspacePreset);
}

function normalizeRecentSymbol(symbol) {
    return String(symbol || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
}

function withRecentMarket(nextItem) {
    const normalizedNext = nextItem.type === 'symbol'
        ? normalizeRecentSymbol(nextItem.symbol)
        : nextItem.id;
    marketRecents = [
        nextItem,
        ...marketRecents.filter((item) => {
            const type = item?.type || (typeof item === 'string' ? 'profile' : null);
            const value = type === 'symbol' ? normalizeRecentSymbol(item.symbol) : (item?.id || item);
            return !(type === nextItem.type && value === normalizedNext);
        }),
    ].slice(0, 8);
    return marketRecents;
}

function rememberProfile(profileId) {
    return withRecentMarket({ type: 'profile', id: profileId });
}

function rememberCustomSymbol(symbol) {
    return withRecentMarket({ type: 'symbol', symbol });
}

function setMarketProfile(profileId) {
    const profile = MARKET_PROFILES[profileId] || MARKET_PROFILES[DEFAULT_MARKET_PROFILE];
    currentMarketProfile = profile.id;
    currentSymbol = profile.symbol;
    customContextSymbol = null;
    currentWorkspacePreset = '';
    suppressNextNewsFresh = true;
    customCalendarCountries = null;

    syncCommandSymbol(currentSymbol);

    changeChart(currentSymbol, { save: false, refresh: false });
    renderMarketProfileSelect();
    const nextRecents = rememberProfile(profile.id);
    savePrefs({ workspacePreset: currentWorkspacePreset, marketProfile: currentMarketProfile, symbol: currentSymbol, calendarCountries: null, marketRecents: nextRecents });
    renderCustomizePanel();
    getNews();
    fetchCalendar(false);
    fetchContext(false);
}

function applyWorkspacePreset(presetId) {
    const preset = WORKSPACE_PRESETS[presetId];
    if (!preset) return;

    const profile = MARKET_PROFILES[preset.marketProfile] || MARKET_PROFILES[DEFAULT_MARKET_PROFILE];
    currentWorkspacePreset = preset.id;
    currentMarketProfile = profile.id;
    currentSymbol = preset.symbol || profile.symbol;
    customContextSymbol = null;
    customCalendarCountries = Array.isArray(preset.calendarCountries) ? preset.calendarCountries : null;
    quoteCards = Array.isArray(preset.quoteCards) ? preset.quoteCards : quoteCards;
    suppressNextNewsFresh = true;

    syncCommandSymbol(currentSymbol);
    changeChart(currentSymbol, { save: false, refresh: false, fromWorkspace: true });
    renderMarketProfileSelect();
    renderPersonalQuoteCards(quoteCards, currentSymbol);
    refreshQuoteCards();
    const nextRecents = rememberProfile(profile.id);
    savePrefs({
        workspacePreset: currentWorkspacePreset,
        marketProfile: currentMarketProfile,
        symbol: currentSymbol,
        calendarCountries: customCalendarCountries,
        quoteCards,
        marketRecents: nextRecents,
    });
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

async function fetchAccountState() {
    await fetchAccountStateAction({
        setAccountState: (nextAccountState) => {
            accountState = nextAccountState;
        },
        getAccountState: () => accountState,
        applyLoadedPrefs,
        renderAccountState,
        hasTerminalAccess,
        bootTerminalApp,
    });
}

async function syncBillingReturn() {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');
    if (params.get('billing') !== 'success' || !sessionId) return;

    try {
        await syncBillingCheckoutSession(sessionId);
        window.history.replaceState({}, '', window.location.pathname);
    } catch (error) {
        console.error(error);
        setAccessAuthMessage(error.message || 'Validation Stripe en attente. Recharge la page dans quelques instants.', 'err');
    }
}

async function submitAccessAuthForm(event) {
    await submitAccessAuthFormAction(event, {
        getAccessFormMode: () => accessFormMode,
        setAccessFormMode: (mode) => {
            accessFormMode = mode;
        },
        setAccountState: (nextAccountState) => {
            accountState = nextAccountState;
        },
        renderAccountState,
        syncPreferences,
        hasTerminalAccess,
        bootTerminalApp,
        renderAccessGate,
    });
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
        submitAccessAuthForm,
        syncPreferences,
    });
}

function bindMarketProfileControls() {
    bindMarketProfileControlsModule({
        renderSelect: renderMarketProfileSelect,
        onChange: applyWorkspacePreset,
    });

    bindMarketSelector({
        profiles: MARKET_PROFILES,
        categories: MARKET_CATEGORIES,
        getCurrentProfile: () => currentMarketProfile,
        getFavorites: () => marketFavorites,
        getRecents: () => marketRecents,
        setFavorites: (favorites) => {
            marketFavorites = favorites;
            savePrefs({ marketFavorites });
        },
        onSelect: setMarketProfile,
        onCustomSymbol: (symbol) => {
            syncCommandSymbol(symbol);
            const nextRecents = rememberCustomSymbol(symbol);
            currentWorkspacePreset = '';
            renderMarketProfileSelect();
            savePrefs({ workspacePreset: currentWorkspacePreset, marketRecents: nextRecents });
            changeChart(symbol, { contextMode: 'symbol' });
        },
    });
}

function refreshQuoteCards() {
    startQuotesRefresh({
        hasAccess: hasTerminalAccess,
        getCurrentSymbol: () => currentSymbol,
        getQuoteCards: () => quoteCards,
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
    const matchedProfileId = getProfileIdFromSymbol(symbol);
    const shouldUseSymbolContext = options.contextMode === 'symbol';
    if (!options.fromWorkspace && shouldUseSymbolContext) {
        currentWorkspacePreset = '';
    }
    if (shouldUseSymbolContext) {
        customContextSymbol = symbol;
    }
    if (matchedProfileId && matchedProfileId !== currentMarketProfile && shouldUseSymbolContext) {
        currentMarketProfile = matchedProfileId;
        customContextSymbol = null;
        customCalendarCountries = null;
        suppressNextNewsFresh = true;
        renderMarketProfileSelect();
        getNews();
    }
    if (matchedProfileId) {
        rememberProfile(matchedProfileId);
    }
    changeChartView(symbol);
    syncActiveQuoteCard(currentSymbol);
    if (options.save !== false) {
        savePrefs({ workspacePreset: currentWorkspacePreset, symbol, marketProfile: currentMarketProfile, marketRecents, calendarCountries: customCalendarCountries });
    }
    if (options.refresh !== false) {
        fetchCalendar(false);
        fetchContext(false);
    }
}

function updateClocks() {
    updateClocksView(MARKETS);
}

function renderCalendarFilters() {
    calendarController.renderFilters();
}

function renderCalendar() {
    calendarController.render();
}

async function fetchCalendar(scheduleNext = true) {
    await calendarController.fetch(scheduleNext);
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
        onSymbolSelect: (symbol) => changeChart(symbol, { contextMode: 'symbol' }),
        refreshCalendar: fetchCalendar,
        refreshContext: fetchContext,
    });
}

async function fetchContext(scheduleNext = true) {
    try {
        const payload = await fetchMarketContext(getProfileQuery(), getCalendarCountryQuery(), getContextSymbol());
        contextState = payload;
        renderMarketContext(payload, { selectedKeys: customWatchlistKeys, onSymbolSelect: (symbol) => changeChart(symbol, { contextMode: 'symbol' }) });
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
        onChange: (symbol) => changeChart(symbol, { contextMode: 'symbol' }),
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
    renderPersonalQuoteCards(quoteCards, currentSymbol);
    bindQuoteCards({
        onSymbolSelect: (symbol) => changeChart(symbol, { contextMode: 'symbol' }),
        getCurrentSymbol: () => currentSymbol,
        getQuoteCards: () => quoteCards,
        setQuoteCards: (nextQuoteCards) => {
            quoteCards = nextQuoteCards;
        },
        savePrefs,
        refreshQuotesNow: refreshQuoteCards,
    });
    bindAccountControls();
    bindLayoutControls();
    bindResizers();
    bindCenterTabs();
    bindCommandInput();
    bindSoundPicker();
    bindSoundToggle();
    bindCustomizeControls();

    syncBillingReturn().finally(fetchAccountState);
    updateClocks();

    window.setInterval(updateClocks, 1000);
    window.addEventListener('resize', () => applyLayoutState(layoutState));
}

init();
