        // ====== STATE + PERSISTENCE ======
        const PREFS_KEY = 'tt_prefs_v1';
        function loadPrefs() {
            try { return JSON.parse(localStorage.getItem(PREFS_KEY)) || {}; }
            catch (e) { return {}; }
        }
        function savePrefs(patch) {
            try {
                const cur = loadPrefs();
                const next = Object.assign({}, cur, patch);
                localStorage.setItem(PREFS_KEY, JSON.stringify(next));
            } catch (e) {}
        }
        const PREFS = loadPrefs();

        let lastSeenTs = 0;
        let currentSymbol = PREFS.symbol || "OANDA:XAUUSD";
        let soundEnabled = !!PREFS.soundEnabled;
        let soundType = PREFS.soundType || 'chime';
        let audioCtx = null;

        // ====== AUDIO ALERT ======
        function ensureAudio() {
            if (!audioCtx) {
                try {
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                } catch (e) { audioCtx = null; }
            }
            if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
        }
        function tone(freq, startOffset, duration, peak, type) {
            const now = audioCtx.currentTime;
            const o = audioCtx.createOscillator();
            const g = audioCtx.createGain();
            o.type = type || 'sine';
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
                    tone(880,  0,    0.20, 0.25, 'sine');
                    tone(1320, 0.12, 0.20, 0.25, 'sine');
                    break;
                case 'siren':
                    [0, 0.18, 0.36].forEach(t => {
                        tone(700,  t,        0.10, 0.22, 'square');
                        tone(1100, t + 0.09, 0.10, 0.22, 'square');
                    });
                    break;
                case 'bloop':
                    tone(440, 0,    0.15, 0.22, 'triangle');
                    tone(660, 0.10, 0.15, 0.22, 'triangle');
                    tone(880, 0.20, 0.20, 0.22, 'triangle');
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
        function renderSoundToggle() {
            const el = document.getElementById('status-sound');
            if (soundEnabled) {
                el.textContent = '🔔 SOUND ON';
                el.style.color = '#22c55e';
            } else {
                el.textContent = '🔇 SOUND OFF';
                el.style.color = '';
            }
        }
        document.getElementById('status-sound').addEventListener('click', () => {
            soundEnabled = !soundEnabled;
            savePrefs({ soundEnabled });
            renderSoundToggle();
            if (soundEnabled) {
                ensureAudio();
                beep();
            }
        });
        const soundPick = document.getElementById('sound-pick');
        soundPick.value = soundType;
        soundPick.addEventListener('change', (e) => {
            soundType = e.target.value;
            savePrefs({ soundType });
            ensureAudio();
            if (audioCtx) playSound(soundType);  // preview the chosen sound
        });
        renderSoundToggle();

        // ====== CHART ======
        function initChart(symbol) {
            currentSymbol = symbol;
            const wrap = document.getElementById('tv_main_wrap');
            wrap.innerHTML = '<div id="tv_main" style="height:100%;"></div>';
            document.getElementById('chart-symbol').textContent = symbol;
            new TradingView.widget({
                "autosize": true, "symbol": symbol, "interval": "1", "theme": "dark",
                "style": "1", "locale": "fr", "container_id": "tv_main",
                "hide_side_toolbar": false, "allow_symbol_change": true, "details": true,
                "studies": ["Volume@tv-basicstudies"]
            });
        }

        function selectCard(card) {
            document.querySelectorAll('.qcard').forEach(c => c.classList.remove('active'));
            if (card) card.classList.add('active');
        }

        function changeChart(symbol, fromCard) {
            initChart(symbol);
            savePrefs({ symbol });
            const card = fromCard || document.querySelector(`.qcard[data-symbol="${symbol}"]`);
            selectCard(card || null);
            if (window.innerWidth < 1024) window.scrollTo({top: 0, behavior: 'smooth'});
        }

        // Wire quote cards
        document.querySelectorAll('.qcard').forEach(card => {
            card.addEventListener('click', () => changeChart(card.dataset.symbol, card));
        });

        // Command bar
        const cmd = document.getElementById('cmd');
        cmd.addEventListener('keydown', (ev) => {
            if (ev.key === 'Enter') {
                const v = cmd.value.trim().toUpperCase();
                if (v) {
                    changeChart(v, null);
                    cmd.value = '';
                    cmd.blur();
                }
            }
        });

        // ====== WORLD CLOCKS + MARKET STATUS ======
        // Stock-market hours (local time, weekdays)
        const MARKETS = {
            NY:  { tz: 'America/New_York', open: [9, 30], close: [16, 0] },
            LDN: { tz: 'Europe/London',    open: [8, 0],  close: [16, 30] },
            TKY: { tz: 'Asia/Tokyo',       open: [9, 0],  close: [15, 0] },
            SYD: { tz: 'Australia/Sydney', open: [10, 0], close: [16, 0] },
        };

        function getTzParts(tz) {
            const fmt = new Intl.DateTimeFormat('en-GB', {
                timeZone: tz, hour12: false,
                weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
            const parts = Object.fromEntries(fmt.formatToParts(new Date()).map(p => [p.type, p.value]));
            return parts;
        }

        function isMarketOpen(m) {
            const p = getTzParts(m.tz);
            const dow = p.weekday;
            if (dow === 'Sat' || dow === 'Sun') return false;
            const h = parseInt(p.hour, 10), min = parseInt(p.minute, 10);
            const cur = h * 60 + min;
            const op = m.open[0] * 60 + m.open[1];
            const cl = m.close[0] * 60 + m.close[1];
            return cur >= op && cur < cl;
        }

        function updateClocks() {
            for (const [code, m] of Object.entries(MARKETS)) {
                const p = getTzParts(m.tz);
                document.getElementById('time-' + code).textContent = `${p.hour}:${p.minute}:${p.second}`;
                const el = document.getElementById('mk-' + code);
                el.classList.toggle('open', isMarketOpen(m));
            }
            const now = new Date();
            document.getElementById('status-clock').textContent =
                String(now.getHours()).padStart(2, '0') + ':' +
                String(now.getMinutes()).padStart(2, '0') + ':' +
                String(now.getSeconds()).padStart(2, '0') + ' LOCAL';
        }

        // ====== NEWS (safe DOM, fresh-flash) ======
        function buildNewsItem(n, isFresh) {
            const item = document.createElement('div');
            item.className = 'n-item' + (n.crit ? ' critical' : '') + (isFresh ? ' fresh' : '');

            const meta = document.createElement('div');
            meta.className = 'n-meta';
            const timeSpan = document.createElement('span');
            timeSpan.textContent = n.time;
            const tag = document.createElement('span');
            tag.className = 'tag ' + n.s;
            tag.textContent = n.s;
            meta.appendChild(timeSpan);
            meta.appendChild(tag);

            const link = document.createElement('a');
            link.href = n.l;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = (n.crit ? '⚠️ ' : '') + n.t; // textContent escapes safely

            item.appendChild(meta);
            item.appendChild(link);
            return item;
        }

        async function getNews() {
            try {
                const r = await fetch('/api/news');
                const data = await r.json();
                const items = data.items || [];
                const container = document.getElementById('news-content');

                const previousLastSeen = lastSeenTs;
                let maxTs = lastSeenTs;
                let freshCount = 0;
                container.innerHTML = '';
                items.forEach(n => {
                    const isFresh = previousLastSeen > 0 && n.ts > previousLastSeen;
                    if (isFresh) freshCount++;
                    if (n.ts > maxTs) maxTs = n.ts;
                    container.appendChild(buildNewsItem(n, isFresh));
                });
                lastSeenTs = maxTs;

                const status = document.getElementById('status-news');
                const cacheTag = data.cached ? `cache ${data.age}s` : 'fresh';
                status.innerHTML = `News: <span class="ok">${items.length}</span> · ${cacheTag}` +
                    (freshCount > 0 ? ` · <span class="warn">+${freshCount} new</span>` : '');
                if (freshCount > 0) beep();
            } catch (e) {
                document.getElementById('status-news').innerHTML = 'News: <span class="err">offline</span>';
            }
        }

        // ====== ECONOMIC CALENDAR ======
        const FLAGS = {
            USD: '\u{1F1FA}\u{1F1F8}', EUR: '\u{1F1EA}\u{1F1FA}', GBP: '\u{1F1EC}\u{1F1E7}',
            JPY: '\u{1F1EF}\u{1F1F5}', CHF: '\u{1F1E8}\u{1F1ED}', CAD: '\u{1F1E8}\u{1F1E6}',
            AUD: '\u{1F1E6}\u{1F1FA}', NZD: '\u{1F1F3}\u{1F1FF}', CNY: '\u{1F1E8}\u{1F1F3}',
        };
        const CCY_LIST = ['USD','EUR','GBP','JPY','CHF','CAD','AUD','NZD','CNY'];
        const IMPACTS = ['High','Medium','Low'];

        const calFilters = {
            impact: new Set(Array.isArray(PREFS.calImpact) ? PREFS.calImpact : ['High','Medium']),
            ccy:    new Set(Array.isArray(PREFS.calCcy)    ? PREFS.calCcy    : ['USD','EUR','GBP','JPY']),
        };
        let calEvents = [];
        let calLastSeenActual = new Set();
        let calPollTimer = null;
        let calFirstLoad = true;

        function persistCalFilters() {
            savePrefs({ calImpact: [...calFilters.impact], calCcy: [...calFilters.ccy] });
        }
        function buildCalToolbar() {
            const root = document.getElementById('cal-filters');
            root.innerHTML = '';
            IMPACTS.forEach(imp => {
                const c = document.createElement('span');
                c.className = 'cal-chip' + (calFilters.impact.has(imp) ? ' on' : '');
                c.textContent = imp.toUpperCase();
                c.addEventListener('click', () => {
                    if (calFilters.impact.has(imp)) calFilters.impact.delete(imp);
                    else calFilters.impact.add(imp);
                    persistCalFilters();
                    buildCalToolbar();
                    renderCalendar();
                });
                root.appendChild(c);
            });
            const sep = document.createElement('span');
            sep.className = 'cal-chip sep';
            sep.textContent = '|';
            root.appendChild(sep);
            CCY_LIST.forEach(ccy => {
                const c = document.createElement('span');
                c.className = 'cal-chip' + (calFilters.ccy.has(ccy) ? ' on' : '');
                c.textContent = ccy;
                c.addEventListener('click', () => {
                    if (calFilters.ccy.has(ccy)) calFilters.ccy.delete(ccy);
                    else calFilters.ccy.add(ccy);
                    persistCalFilters();
                    buildCalToolbar();
                    renderCalendar();
                });
                root.appendChild(c);
            });
        }
        function calToNum(s) {
            if (s === null || s === undefined || s === '') return null;
            const m = String(s).match(/-?\d+(?:\.\d+)?/);
            if (!m) return null;
            let n = parseFloat(m[0]);
            const u = String(s).slice(-1).toUpperCase();
            if (u === 'T') n *= 1e12;
            else if (u === 'B') n *= 1e9;
            else if (u === 'M') n *= 1e6;
            else if (u === 'K') n *= 1e3;
            return n;
        }
        function compareActual(actual, forecast) {
            const a = calToNum(actual), f = calToNum(forecast);
            if (a === null || f === null) return 'eq';
            if (a > f) return 'up';
            if (a < f) return 'down';
            return 'eq';
        }
        function fmtCountdown(secs) {
            if (secs < 0) secs = 0;
            const m = Math.floor(secs / 60);
            const s = secs % 60;
            return `${m}:${String(s).padStart(2,'0')}`;
        }
        function escapeHtml(s) {
            return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
        }
        function renderCalendar() {
            const root = document.getElementById('calendar-content');
            if (!calEvents.length) {
                root.innerHTML = '<div class="cal-empty">Chargement…</div>';
                return;
            }
            const filtered = calEvents.filter(e =>
                calFilters.impact.has(e.impact) && calFilters.ccy.has(e.country)
            );
            if (!filtered.length) {
                root.innerHTML = '<div class="cal-empty">Aucun événement avec les filtres actuels.</div>';
                return;
            }
            const now = Date.now() / 1000;
            const newFreshTriggers = [];
            let html = '';
            let lastDay = '';
            filtered.forEach(e => {
                const dt = new Date(e.ts * 1000);
                const dayKey = dt.toLocaleDateString('fr-FR', { weekday:'long', day:'numeric', month:'long' });
                if (dayKey !== lastDay) {
                    html += `<div class="cal-day">${dayKey}</div>`;
                    lastDay = dayKey;
                }
                const localTime = dt.toLocaleTimeString('fr-FR', { hour:'2-digit', minute:'2-digit' });
                const flag = FLAGS[e.country] || '\u{1F3F3}';
                const impClass = e.impact.toLowerCase();
                const isPast = !!e.actual || (e.ts < now - 60);
                const isDue  = !e.actual && (e.ts - now) <= 75 && (e.ts - now) >= -10;
                const cmp = e.actual ? compareActual(e.actual, e.forecast) : 'eq';
                const fresh = !!e.actual && !calLastSeenActual.has(e.ts) && !calFirstLoad;
                if (e.actual) {
                    if (fresh) newFreshTriggers.push(e);
                    calLastSeenActual.add(e.ts);
                }
                const cls = ['cal-row'];
                if (isPast && !fresh) cls.push('past');
                if (isDue) cls.push('due');
                if (fresh) cls.push('fresh-result');

                let cdHtml = '';
                if (isDue) {
                    const secs = Math.max(0, Math.floor(e.ts - now));
                    const urgent = secs < 30 ? ' urgent' : '';
                    cdHtml = `<span class="cal-countdown${urgent}" data-cd-target="${e.ts}">T-${fmtCountdown(secs)}</span>`;
                }
                const actualHtml = e.actual
                    ? `<span class="cal-num ${cmp}">${escapeHtml(e.actual)}</span>`
                    : `<span class="cal-num muted">—</span>`;
                const forecastHtml = e.forecast
                    ? `<span class="cal-num">${escapeHtml(e.forecast)}</span>`
                    : `<span class="cal-num muted">—</span>`;
                const previousHtml = e.previous
                    ? `<span class="cal-num muted">${escapeHtml(e.previous)}</span>`
                    : `<span class="cal-num muted">—</span>`;
                const safeTitle = escapeHtml(e.title || '');

                html += `<div class="${cls.join(' ')}">
                    <span class="cal-time"><span>${localTime}</span>${cdHtml}</span>
                    <span class="cal-flag-wrap"><span class="cal-flag">${flag}</span><span class="cal-ccy">${e.country}</span></span>
                    <span class="cal-title">
                        <span class="cal-impact ${impClass}"><i></i><i></i><i></i></span>
                        <span class="cal-title-text" title="${safeTitle}">${safeTitle}</span>
                    </span>
                    ${actualHtml}
                    ${forecastHtml}
                    ${previousHtml}
                </div>`;
            });
            root.innerHTML = html;

            // Sound triggers (only after first load — avoid mass-flash on first paint)
            if (!calFirstLoad && newFreshTriggers.some(e => e.impact === 'High' || e.impact === 'Medium')) {
                if (soundEnabled) { ensureAudio(); beep(); }
            }
            calFirstLoad = false;
        }
        function tickCountdowns() {
            const now = Date.now() / 1000;
            let crossedZero = false;
            document.querySelectorAll('[data-cd-target]').forEach(el => {
                const ts = parseFloat(el.dataset.cdTarget);
                const secs = Math.floor(ts - now);
                if (secs < -2) { crossedZero = true; return; }
                el.textContent = `T-${fmtCountdown(Math.max(0, secs))}`;
                if (secs < 30 && !el.classList.contains('urgent')) el.classList.add('urgent');
            });
            if (crossedZero) fetchCalendar();
        }
        function nextHotMomentSec() {
            // Returns: 0 if currently in hot window (event within ±90s), else seconds until hot window starts
            const now = Date.now() / 1000;
            for (const e of calEvents) {
                if (e.actual) continue;
                if (!calFilters.impact.has(e.impact) || !calFilters.ccy.has(e.country)) continue;
                const delta = e.ts - now;
                if (delta < -120) continue;
                if (delta <= 90) return 0;
                return delta - 90;
            }
            return Infinity;
        }
        function scheduleCalPoll() {
            clearTimeout(calPollTimer);
            const hot = nextHotMomentSec();
            let delay;
            if (hot === 0) delay = 3000;
            else if (hot < 60) delay = Math.max(2000, hot * 1000);
            else delay = 60000;
            calPollTimer = setTimeout(fetchCalendar, delay);
        }
        async function fetchCalendar() {
            try {
                const r = await fetch('/api/calendar');
                const j = await r.json();
                calEvents = j.events || [];
                document.getElementById('cal-live').innerHTML = j.hot
                    ? '<span style="color:var(--warn);">HOT</span>' : 'LIVE';
                renderCalendar();
            } catch (e) {
                document.getElementById('cal-live').innerHTML = '<span style="color:var(--sell);">OFFLINE</span>';
            } finally {
                scheduleCalPoll();
            }
        }
        buildCalToolbar();
        fetchCalendar();
        setInterval(tickCountdowns, 1000);

        // ====== BOOT ======
        const startSymbol = currentSymbol;
        const startCard = document.querySelector(`.qcard[data-symbol="${startSymbol}"]`);
        initChart(startSymbol);
        selectCard(startCard || document.querySelector('.qcard'));
        updateClocks();
        getNews();
        setInterval(updateClocks, 1000);
        setInterval(getNews, 5000);   // safe — server-side cache makes this cheap