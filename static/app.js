const PREFS_KEY = 'tt_prefs_v1';
const CALENDAR_REFRESH_MS = 60000;
const NEWS_REFRESH_MS = 8000;
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
let lastSeenNewsTs = 0;
let calEvents = [];
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

function initChart(symbol) {
    currentSymbol = symbol;

    const wrap = document.getElementById('tv_main_wrap');
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

function formatValue(value, unit) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    return unit ? `${value}${unit}` : String(value);
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

function renderCalendar() {
    const root = document.getElementById('calendar-content');
    if (!root) return;

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

async function getNews() {
    try {
        const response = await fetch('/api/news');
        const data = await response.json();
        const items = data.items || [];
        const container = document.getElementById('news-content');

        if (!container) return;
        container.innerHTML = '';

        let freshCount = 0;

        items.forEach((itemData) => {
            const item = document.createElement('div');
            const isFresh = itemData.ts > lastSeenNewsTs;
            if (isFresh) {
                freshCount += 1;
            }

            item.className = `n-item${itemData.crit ? ' critical' : ''}${isFresh ? ' fresh' : ''}`;

            const meta = document.createElement('div');
            meta.className = 'n-meta';

            const time = document.createElement('span');
            time.textContent = itemData.time;

            const tag = document.createElement('span');
            tag.className = `tag ${itemData.s}`;
            tag.textContent = itemData.s;

            meta.appendChild(time);
            meta.appendChild(tag);

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
            statusNews.textContent = `News: ${items.length} items${data.cached ? ` - cache ${data.age}s` : ''}`;
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
    bindCommandInput();
    bindSoundPicker();
    bindSoundToggle();

    initChart(currentSymbol);
    updateClocks();
    getNews();
    fetchCalendar();

    window.setInterval(updateClocks, 1000);
    window.setInterval(getNews, NEWS_REFRESH_MS);
}

init();
