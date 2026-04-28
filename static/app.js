const PREFS_KEY = 'tt_prefs_v1';
const CALENDAR_REFRESH_MS = 60000;
const NEWS_REFRESH_MS = 8000;
const CONTEXT_REFRESH_MS = 15000;
const IMPACT_LEVELS = ['High', 'Medium', 'Low'];

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
        localStorage.setItem(PREFS_KEY, JSON.stringify({ ...current, ...patch }));
    } catch {}
}

const PREFS = loadPrefs();

let currentSymbol = PREFS.symbol || 'OANDA:XAUUSD';
let soundEnabled = !!PREFS.soundEnabled;
let soundType = PREFS.soundType || 'chime';
let currentCenterTab = PREFS.centerTab || 'bias';
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
    bindCenterTabs();
    bindCommandInput();
    bindSoundPicker();
    bindSoundToggle();

    initChart(currentSymbol);
    updateClocks();
    getNews();
    fetchCalendar();
    fetchContext();

    window.setInterval(updateClocks, 1000);
    window.setInterval(getNews, NEWS_REFRESH_MS);
}

init();
