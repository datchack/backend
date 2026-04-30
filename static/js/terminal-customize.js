import { CALENDAR_COUNTRY_OPTIONS, DEFAULT_WIDGETS, WIDGET_OPTIONS } from './terminal-config.js';

export function toggleCustomizePanel(open = null, renderPanel = null) {
    const panel = document.getElementById('customize-panel');
    if (!panel) return;
    const shouldOpen = open === null ? panel.classList.contains('hidden') : open;
    panel.classList.toggle('hidden', !shouldOpen);
    if (shouldOpen) renderPanel?.();
}

export function renderCustomizePanel({
    countries,
    context,
    selectedWatchlistKeys,
    widgetVisibility,
}) {
    const countriesRoot = document.getElementById('customize-countries');
    const watchRoot = document.getElementById('customize-watchlist');
    const widgetsRoot = document.getElementById('customize-widgets');
    const activeCountries = new Set(countries);

    if (countriesRoot) {
        countriesRoot.innerHTML = CALENDAR_COUNTRY_OPTIONS.map((country) => `
            <label class="customize-check">
                <input type="checkbox" data-custom-country="${country}" ${activeCountries.has(country) ? 'checked' : ''}>
                <span>${country}</span>
            </label>
        `).join('');
    }

    if (watchRoot) {
        const available = context?.available_watchlist || context?.watchlist || [];
        const activeKeys = new Set(selectedWatchlistKeys || (context?.watchlist || []).map((item) => item.key));
        watchRoot.innerHTML = available.map((item) => `
            <label class="customize-check">
                <input type="checkbox" data-custom-watch="${item.key}" ${activeKeys.has(item.key) ? 'checked' : ''}>
                <span>${item.label}</span>
            </label>
        `).join('') || '<span class="customize-empty">Watchlist en chargement</span>';
    }

    if (widgetsRoot) {
        widgetsRoot.innerHTML = WIDGET_OPTIONS.map((widget) => `
            <label class="customize-check">
                <input type="checkbox" data-custom-widget="${widget.key}" ${widgetVisibility[widget.key] !== false ? 'checked' : ''}>
                <span>${widget.label}</span>
            </label>
        `).join('');
    }
}

export function bindCustomizeControls({
    getCalendarCountries,
    getContext,
    getSelectedWatchlistKeys,
    getWidgetVisibility,
    setCalendarCountries,
    setSelectedWatchlistKeys,
    setWidgetVisibility,
    savePrefs,
    applyWidgetVisibility,
    renderPanel,
    renderWatchlist,
    onSymbolSelect,
    refreshCalendar,
    refreshContext,
}) {
    const toggle = document.getElementById('customize-toggle');
    const close = document.getElementById('customize-close');
    const reset = document.getElementById('customize-reset');
    const panel = document.getElementById('customize-panel');

    toggle?.addEventListener('click', () => toggleCustomizePanel(null, renderPanel));
    close?.addEventListener('click', () => toggleCustomizePanel(false, renderPanel));
    reset?.addEventListener('click', () => {
        setCalendarCountries(null);
        setSelectedWatchlistKeys(null);
        setWidgetVisibility({ ...DEFAULT_WIDGETS });
        savePrefs({ calendarCountries: null, watchlistKeys: null, widgets: getWidgetVisibility() });
        applyWidgetVisibility(getWidgetVisibility());
        renderPanel();
        refreshCalendar(false);
        refreshContext(false);
    });

    panel?.addEventListener('change', (event) => {
        const input = event.target;
        if (!(input instanceof HTMLInputElement)) return;

        if (input.dataset.customCountry) {
            const next = new Set(getCalendarCountries());
            if (input.checked) next.add(input.dataset.customCountry);
            else if (next.size > 1) next.delete(input.dataset.customCountry);
            setCalendarCountries([...next]);
            savePrefs({ calendarCountries: [...next] });
            renderPanel();
            refreshCalendar(false);
            refreshContext(false);
        }

        if (input.dataset.customWatch) {
            const context = getContext();
            const fallback = (context?.watchlist || []).map((item) => item.key);
            const next = new Set(getSelectedWatchlistKeys() || fallback);
            if (input.checked) next.add(input.dataset.customWatch);
            else if (next.size > 1) next.delete(input.dataset.customWatch);
            const nextKeys = [...next];
            setSelectedWatchlistKeys(nextKeys);
            savePrefs({ watchlistKeys: nextKeys });
            renderWatchlist(context || {}, { selectedKeys: nextKeys, onSymbolSelect });
            renderPanel();
        }

        if (input.dataset.customWidget) {
            const nextWidgetVisibility = {
                ...getWidgetVisibility(),
                [input.dataset.customWidget]: input.checked,
            };
            setWidgetVisibility(nextWidgetVisibility);
            savePrefs({ widgets: nextWidgetVisibility });
            applyWidgetVisibility(nextWidgetVisibility);
        }
    });
}
