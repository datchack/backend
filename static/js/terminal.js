import {
    CONTEXT_REFRESH_MS,
    DEFAULT_ACCOUNT_MODE,
    DEFAULT_MARKET_PROFILE,
    DEFAULT_WIDGETS,
    MARKETS,
    MARKET_PROFILES,
    NEWS_REFRESH_MS,
    PREFS_KEY,
} from './terminal-config.js';
import { saveAccountPreferences } from './terminal-account-api.js';
import {
    fetchAccountState as fetchAccountStateAction,
    logoutAccount as logoutAccountAction,
    openBillingPortal as openBillingPortalAction,
    submitAccessAuthForm as submitAccessAuthFormAction,
    submitAccountForm as submitAccountFormAction,
} from './terminal-account-actions.js';
import {
    bindAccountControls as bindAccountControlsModule,
    hasTerminalAccess as accountHasTerminalAccess,
    renderAccessGate as renderAccessGateView,
    renderAccountState as renderAccountStateView,
    toggleAccountPanel as toggleAccountPanelView,
} from './terminal-account-ui.js';
import { createCalendarController } from './terminal-calendar.js';
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
import { updateClocks as updateClocksView } from './terminal-clocks.js';
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
import { fetchMarketContext, fetchNewsFeed } from './terminal-market-api.js';
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

    calendarController?.setImpactFilters(prefs.impactFilters);

    renderSoundToggleControl(soundEnabled);
    renderCalendarFilters();
    syncSoundPicker(soundType);
    syncCommandSymbol(currentSymbol);
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

calendarController = createCalendarController({
    initialImpactFilters: PREFS.impactFilters,
    getProfileQuery,
    getCalendarCountryQuery,
    savePrefs,
});

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

async function submitAccountForm(event) {
    await submitAccountFormAction(event, {
        getAccountMode: () => accountMode,
        setAccountState: (nextAccountState) => {
            accountState = nextAccountState;
        },
        renderAccountState,
        syncPreferences,
        hasTerminalAccess,
        bootTerminalApp,
        renderAccessGate,
        toggleAccountPanel,
    });
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

async function logoutAccount() {
    await logoutAccountAction();
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
        openBillingPortal: openBillingPortalAction,
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
