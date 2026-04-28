// ===================== STATE =====================
const PREFS_KEY = 'tt_prefs_v1';

function loadPrefs() {
    try { return JSON.parse(localStorage.getItem(PREFS_KEY)) || {}; }
    catch { return {}; }
}

function savePrefs(patch) {
    try {
        const cur = loadPrefs();
        localStorage.setItem(PREFS_KEY, JSON.stringify({ ...cur, ...patch }));
    } catch {}
}

const PREFS = loadPrefs();

let lastSeenTs = 0;
let currentSymbol = PREFS.symbol || "OANDA:XAUUSD";
let soundEnabled = !!PREFS.soundEnabled;
let soundType = PREFS.soundType || 'chime';

let audioCtx = null;

// ===================== AUDIO =====================
function ensureAudio() {
    if (!audioCtx) {
        try {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        } catch {
            audioCtx = null;
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
}

function tone(freq, startOffset, duration, peak, type) {
    const now = audioCtx.currentTime;
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();

    o.type = type;
    o.frequency.value = freq;

    g.gain.setValueAtTime(0.0001, now + startOffset);
    g.gain.exponentialRampToValueAtTime(peak, now + startOffset + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, now + startOffset + duration);

    o.connect(g).connect(audioCtx.destination);
    o.start(now + startOffset);
    o.stop(now + startOffset + duration + 0.02);
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
            [0, 0.18, 0.36].forEach(t => {
                tone(700, t, 0.1, 0.22, 'square');
                tone(1100, t + 0.09, 0.1, 0.22, 'square');
            });
            break;

        case 'bloop':
            tone(440, 0, 0.15, 0.22, 'triangle');
            break;

        case 'alert':
            [0, 0.14, 0.28].forEach(t => tone(2000, t, 0.08, 0.28, 'sawtooth'));
            break;
    }
}

function beep() {
    if (!soundEnabled || !audioCtx) return;
    playSound(soundType);
}

// ===================== SOUND UI =====================
const soundEl = document.getElementById('status-sound');

function renderSoundToggle() {
    if (!soundEl) return;
    soundEl.textContent = soundEnabled ? '🔔 SOUND ON' : '🔇 SOUND OFF';
    soundEl.style.color = soundEnabled ? '#22c55e' : '';
}

soundEl?.addEventListener('click', () => {
    soundEnabled = !soundEnabled;
    savePrefs({ soundEnabled });
    renderSoundToggle();
    ensureAudio();
    beep();
});

renderSoundToggle();

// ===================== CHART =====================
function initChart(symbol) {
    currentSymbol = symbol;
    const wrap = document.getElementById('tv_main_wrap');

    wrap.innerHTML = '<div id="tv_main" style="height:100%;"></div>';
    document.getElementById('chart-symbol').textContent = symbol;

    new TradingView.widget({
        autosize: true,
        symbol,
        interval: "1",
        theme: "dark",
        style: "1",
        locale: "fr",
        container_id: "tv_main",
        hide_side_toolbar: false,
        allow_symbol_change: true,
        details: true,
        studies: ["Volume@tv-basicstudies"]
    });
}

function changeChart(symbol) {
    initChart(symbol);
    savePrefs({ symbol });
}

// ===================== CLOCKS =====================
const MARKETS = {
    NY:  { tz: 'America/New_York', open: [9,30], close: [16,0] },
    LDN: { tz: 'Europe/London', open: [8,0], close: [16,30] },
    TKY: { tz: 'Asia/Tokyo', open: [9,0], close: [15,0] },
    SYD: { tz: 'Australia/Sydney', open: [10,0], close: [16,0] },
};

function getTz(tz) {
    const fmt = new Intl.DateTimeFormat('en-GB', {
        timeZone: tz,
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    return Object.fromEntries(fmt.formatToParts(new Date()).map(p => [p.type, p.value]));
}

function updateClocks() {
    for (const [k, m] of Object.entries(MARKETS)) {
        const p = getTz(m.tz);
        const el = document.getElementById('time-' + k);
        if (el) el.textContent = `${p.hour}:${p.minute}:${p.second}`;
    }
}

// ===================== NEWS =====================
async function getNews() {
    try {
        const r = await fetch('/api/news');
        const data = await r.json();

        const items = data.items || [];
        const container = document.getElementById('news-content');

        container.innerHTML = '';

        items.forEach(n => {
            const item = document.createElement('div');
            item.className = 'n-item' + (n.crit ? ' critical' : '');

            const meta = document.createElement('div');
            meta.className = 'n-meta';

            const time = document.createElement('span');
            time.textContent = n.time;

            const tag = document.createElement('span');
            tag.className = 'tag ' + n.s;
            tag.textContent = n.s;

            meta.appendChild(time);
            meta.appendChild(tag);

            const link = document.createElement('a');
            link.href = n.l;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = n.t;

            item.appendChild(meta);
            item.appendChild(link);

            container.appendChild(item);
        });

    } catch (e) {
        console.error(e);
    }
}

// ===================== CALENDAR =====================
let calEvents = [];

async function fetchCalendar() {
    try {
        const r = await fetch('/api/calendar', { cache: "no-store" });
        const j = await r.json();

        calEvents = Array.isArray(j.events) ? j.events : [];

        document.getElementById('cal-live').innerHTML =
            j.hot ? '<span style="color:#f59e0b">HOT</span>' : 'LIVE';

        renderCalendar();

    } catch (e) {
        console.error(e);
    }

    setTimeout(fetchCalendar, 60000);
}

function renderCalendar() {
    const root = document.getElementById('calendar-content');

    if (!Array.isArray(calEvents) || calEvents.length === 0) {
        root.innerHTML = '<div class="cal-empty">Chargement...</div>';
        return;
    }

    let html = '';
    let lastDay = '';

    calEvents.forEach(e => {
        const dt = new Date(e.ts * 1000);

        const day = dt.toLocaleDateString('fr-FR', {
            weekday: 'long',
            day: 'numeric',
            month: 'long'
        });

        if (day !== lastDay) {
            html += `<div class="cal-day">${day}</div>`;
            lastDay = day;
        }

        const time = dt.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const impactClass =
            e.impact === 'High' ? 'high' :
            e.impact === 'Medium' ? 'medium' : 'low';

        html += `
        <div class="cal-row">
            <span class="cal-time">${time}</span>
            <span class="cal-flag">${e.country}</span>
            <span class="cal-title">
                <span class="cal-impact ${impactClass}"></span>
                ${e.title}
            </span>
            <span class="cal-num">${e.actual || '-'}</span>
            <span class="cal-num">${e.forecast || '-'}</span>
            <span class="cal-num">${e.previous || '-'}</span>
        </div>`;
    });

    root.innerHTML = html;
}

// ===================== INIT =====================
initChart(currentSymbol);
updateClocks();
getNews();
fetchCalendar();

setInterval(updateClocks, 1000);
setInterval(getNews, 8000);