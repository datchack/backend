import { CALENDAR_REFRESH_MS, IMPACT_LEVELS } from './terminal-config.js';
import {
    formatValue,
    getActualVsPreviousTone,
    getCalendarBiasClass,
    getDateKeyFromTs,
} from './terminal-formatters.js';
import { fetchCalendarFeed } from './terminal-market-api.js';

function renderCalendarValue(label, value, unit = '', tone = '') {
    return `
        <span class="cal-stat ${tone}">
            <span class="cal-stat-label">${label}</span>
            <strong>${formatValue(value, unit)}</strong>
        </span>
    `;
}

function renderCalendarRead(event) {
    const parts = [];
    if (event.surprise_label) {
        const tone = event.result_tone || '';
        const pct = Number.isFinite(Number(event.surprise_pct)) ? ` (${Number(event.surprise_pct).toFixed(2)}%)` : '';
        parts.push(`<span class="cal-read ${tone}">SURPRISE ${event.surprise_label}${pct}</span>`);
    }
    if (event.market_read) {
        parts.push(`<span class="cal-read ${event.result_tone || ''}">${event.market_read}</span>`);
    }
    if (!parts.length) return '';
    return `<div class="cal-read-row">${parts.join('')}</div>`;
}

function buildImpactDots(level) {
    return `<span class="cal-impact ${String(level || '').toLowerCase()}"><i></i><i></i><i></i></span>`;
}

export function renderCalendarFilters(filters, onChange) {
    const root = document.getElementById('cal-filters');
    if (!root) return;

    root.innerHTML = IMPACT_LEVELS.map((level) => `
        <button class="cal-chip ${filters.impact.has(level) ? 'on' : ''}" data-impact="${level}" type="button">
            ${level}
        </button>
    `).join('');

    root.querySelectorAll('[data-impact]').forEach((button) => {
        button.addEventListener('click', () => {
            const { impact } = button.dataset;
            if (!impact) return;
            onChange(impact);
        });
    });
}

export function renderCalendar(events, meta, filters) {
    const root = document.getElementById('calendar-content');
    if (!root) return;

    if (meta.error && events.length === 0) {
        root.innerHTML = `<div class="cal-empty">Erreur calendrier: ${meta.error}</div>`;
        return;
    }

    if (!Array.isArray(events) || events.length === 0) {
        root.innerHTML = '<div class="cal-empty">Aucun evenement a venir.</div>';
        return;
    }

    const filtered = events.filter((event) => filters.impact.has(event.impact));
    if (filtered.length === 0) {
        root.innerHTML = '<div class="cal-empty">Aucun evenement pour ce filtre.</div>';
        return;
    }

    const nowTs = Math.floor(Date.now() / 1000);
    const timeZone = meta.timezone || 'Europe/Paris';
    const todayKey = getDateKeyFromTs(nowTs, timeZone);
    const upcoming = filtered.filter((event) => getDateKeyFromTs(event.ts, timeZone) >= todayKey);

    if (upcoming.length === 0) {
        root.innerHTML = '<div class="cal-empty">Aucun evenement a venir.</div>';
        return;
    }

    const eventsByDay = new Map();

    upcoming.forEach((event) => {
        const key = getDateKeyFromTs(event.ts, timeZone);
        if (!eventsByDay.has(key)) {
            eventsByDay.set(key, []);
        }
        eventsByDay.get(key).push(event);
    });

    let html = '';
    const dayKeys = [...eventsByDay.keys()].sort();

    dayKeys.forEach((dayKey) => {
        const dayDate = new Date(`${dayKey}T12:00:00`);
        const dayLabel = dayDate.toLocaleDateString('fr-FR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long',
        });
        const dayEvents = eventsByDay.get(dayKey) || [];

        html += `<div class="cal-day">${dayLabel}</div>`;

        const clusters = new Map();
        dayEvents.forEach((event) => {
            const key = `${event.ts}:${event.country || '-'}`;
            if (!clusters.has(key)) clusters.set(key, []);
            clusters.get(key).push(event);
        });

        dayEvents.forEach((event, index) => {
            const dt = new Date(event.ts * 1000);
            const time = dt.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit',
                timeZone,
            });
            const clusterKey = `${event.ts}:${event.country || '-'}`;
            const cluster = clusters.get(clusterKey) || [];
            const firstInCluster = index === dayEvents.findIndex((candidate) => `${candidate.ts}:${candidate.country || '-'}` === clusterKey);
            if (firstInCluster && cluster.length >= 3) {
                const keyCount = cluster.filter((item) => item.market_label === 'KEY').length;
                const watchCount = cluster.filter((item) => item.market_label === 'WATCH').length;
                html += `
                <div class="cal-release-block">
                    <span>${time} ${event.country || '-'}</span>
                    <strong>RELEASE BLOCK</strong>
                    <em>${cluster.length} events${keyCount ? ` / ${keyCount} key` : ''}${watchCount ? ` / ${watchCount} watch` : ''}</em>
                </div>`;
            }

            const dueSoon = event.ts >= nowTs && event.ts - nowTs <= 1800;
            const isPast = event.ts < nowTs;
            const actualTone = event.result_tone || getActualVsPreviousTone(event);
            const rowClasses = [
                'cal-row',
                getCalendarBiasClass(event),
                event.market_label ? `priority-${String(event.market_label).toLowerCase()}` : '',
                dueSoon ? 'due' : '',
                isPast ? 'past' : '',
            ].filter(Boolean).join(' ');
            const priorityBadge = event.market_label
                ? `<span class="cal-priority ${String(event.market_label).toLowerCase()}">${event.market_label}</span>`
                : '';

            html += `
            <div class="${rowClasses}" data-ts="${event.ts}">
                <div class="cal-event-main">
                    <div class="cal-event-top">
                        <span class="cal-time">${time}</span>
                        <span class="cal-country">${event.country || '-'}</span>
                        ${buildImpactDots(event.impact)}
                        ${priorityBadge}
                    </div>
                    <div class="cal-title-text">${event.title || '-'}</div>
                    <div class="cal-stats">
                        ${renderCalendarValue('Actual', event.actual, event.unit, actualTone)}
                        ${renderCalendarValue('Forecast', event.forecast, event.unit)}
                        ${renderCalendarValue('Previous', event.previous, event.unit)}
                    </div>
                    ${renderCalendarRead(event)}
                </div>
            </div>`;
        });
    });

    root.innerHTML = html;
}

export function updateCalendarStatus(meta) {
    const liveEl = document.getElementById('cal-live');
    if (!liveEl) return;

    if (meta.error) {
        liveEl.textContent = 'ERROR';
        liveEl.style.color = '#ff4d6d';
        return;
    }

    liveEl.textContent = meta.releaseWatch ? 'LIVE 2S' : meta.hot ? 'HOT' : 'LIVE';
    liveEl.style.color = meta.releaseWatch ? '#ffcc00' : meta.hot ? '#f59e0b' : '#22c55e';
}

function defaultCalendarMeta() {
    return {
        timezone: 'Europe/Paris',
        error: null,
        count: 0,
        hot: false,
        releaseWatch: false,
        refreshMs: CALENDAR_REFRESH_MS,
        weekStart: null,
        weekEnd: null,
    };
}

export function createCalendarController({
    initialImpactFilters = IMPACT_LEVELS,
    getProfileQuery,
    getCalendarCountryQuery,
    savePrefs,
}) {
    let events = [];
    let meta = defaultCalendarMeta();
    let refreshTimer = null;
    const filters = {
        impact: new Set(Array.isArray(initialImpactFilters) && initialImpactFilters.length ? initialImpactFilters : IMPACT_LEVELS),
    };

    function getImpactFilters() {
        return [...filters.impact];
    }

    function setImpactFilters(nextImpactFilters) {
        filters.impact = new Set(Array.isArray(nextImpactFilters) && nextImpactFilters.length ? nextImpactFilters : IMPACT_LEVELS);
    }

    function renderFilters() {
        renderCalendarFilters(filters, handleFilterChange);
    }

    function render() {
        renderCalendar(events, meta, filters);
    }

    function handleFilterChange(impact) {
        if (filters.impact.has(impact) && filters.impact.size > 1) {
            filters.impact.delete(impact);
        } else {
            filters.impact.add(impact);
        }

        savePrefs?.({ impactFilters: getImpactFilters() });
        renderFilters();
        render();
    }

    async function fetch(scheduleNext = true) {
        try {
            const payload = await fetchCalendarFeed(getProfileQuery(), getCalendarCountryQuery());

            events = Array.isArray(payload.events) ? payload.events : [];
            meta = {
                timezone: payload.timezone || 'Europe/Paris',
                error: payload.error || null,
                count: payload.count || 0,
                hot: !!payload.hot,
                releaseWatch: !!payload.release_watch,
                refreshMs: Number(payload.refresh_ms) || CALENDAR_REFRESH_MS,
                weekStart: payload.week_start || null,
                weekEnd: payload.week_end || null,
            };

            updateCalendarStatus(meta);
            render();
        } catch (error) {
            console.error(error);
            meta = { ...defaultCalendarMeta(), error: 'Requete impossible' };
            events = [];
            updateCalendarStatus(meta);
            render();
        }

        if (scheduleNext) {
            window.clearTimeout(refreshTimer);
            refreshTimer = window.setTimeout(fetch, meta.refreshMs || CALENDAR_REFRESH_MS);
        }
    }

    return {
        fetch,
        getImpactFilters,
        render,
        renderFilters,
        setImpactFilters,
    };
}
