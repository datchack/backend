import { MARKET_CATEGORIES, MARKET_PROFILES, QUOTES_REFRESH_MS } from './terminal-config.js?v=20260514-workspace-presets';
import { formatQuoteChange, formatQuotePrice } from './terminal-formatters.js?v=20260514-workspace-presets';
import { fetchMarketQuotes } from './terminal-market-api.js?v=20260514-workspace-presets';

const QUOTE_SLOT_COUNT = 8;
const CATEGORY_ALL = 'all';

let quotesRefreshTimer = null;
let latestQuotes = [];

function normalizeSymbol(symbol) {
    return String(symbol || '').trim().toUpperCase();
}

function normalizeSearch(value) {
    return String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function quoteSymbol(quote, fallback = '') {
    return quote?.tv_symbol || quote?.symbol || fallback;
}

function quoteKey(quote) {
    return String(quote?.key || quote?.label || quoteSymbol(quote)).toLowerCase().replace(/[^a-z0-9_]/g, '');
}

function quoteName(quote) {
    return quote?.name || quote?.label || quoteSymbol(quote);
}

function quoteSource(quote) {
    return quote?.source || 'YAHOO';
}

function compactSymbol(symbol) {
    return String(symbol || '').split(':').pop().toUpperCase();
}

function formatSymbolLabel(symbol) {
    const clean = compactSymbol(symbol).replace(/[^A-Z0-9]/g, '');
    if (clean.length === 6 && /^[A-Z]{6}$/.test(clean)) {
        return `${clean.slice(0, 3)}/${clean.slice(3)}`;
    }
    return clean || symbol;
}

function cardFromSymbol(input) {
    const rawSymbol = typeof input === 'object' ? input?.symbol : input;
    const normalized = normalizeSymbol(rawSymbol);
    if (!normalized) return null;
    return {
        symbol: normalized,
        label: typeof input === 'object' && input?.label
            ? String(input.label)
            : formatSymbolLabel(normalized),
    };
}

function cleanCards(cards = []) {
    const seen = new Set();
    return cards
        .map((card) => cardFromSymbol(card?.symbol || card))
        .filter(Boolean)
        .filter((card) => {
            const key = card.symbol.split(':').pop().replace(/[^A-Z0-9]/g, '');
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        })
        .slice(0, QUOTE_SLOT_COUNT);
}

function renderEmptyCard(index) {
    return `
        <button type="button" class="qcard qcard-empty" data-quote-empty="${index}" aria-label="Ajouter une carte marche">
            <span class="quote-plus">+</span>
            <span class="quote-empty-label">AJOUTER</span>
        </button>
    `;
}

function renderFilledCard(card, quote, currentSymbol) {
    const symbol = quoteSymbol(quote, card.symbol);
    const key = quoteKey(quote || card);
    const price = Number(quote?.price);
    const previousPrice = Number(card.price);
    const change = Number(quote?.change || 0);
    const tone = change > 0 ? 'up' : change < 0 ? 'down' : 'flat';
    const tickTone = Number.isFinite(previousPrice) && Number.isFinite(price) && price !== previousPrice
        ? price > previousPrice ? 'tick-up' : 'tick-down'
        : '';
    const active = symbol === currentSymbol ? 'active' : '';
    const loading = quote ? '' : 'loading';
    const unavailable = quote?.source === 'UNAVAILABLE' ? 'unavailable' : '';
    const classes = ['qcard', tone, active, loading, tickTone].filter(Boolean).join(' ');

    return `
        <button type="button" class="${classes} ${unavailable}" data-symbol="${escapeHtml(symbol)}" data-quote-card-symbol="${escapeHtml(card.symbol)}" data-quote-key="${escapeHtml(key)}" data-price="${Number.isFinite(price) ? price : ''}">
            <span class="quote-accent"></span>
            <span class="quote-card-head">
                <span>
                    <strong>${escapeHtml(quote?.label || card.label || symbol)}</strong>
                    <em>${escapeHtml(quote ? quoteName(quote) : 'Chargement')}</em>
                </span>
                <span class="quote-source">${escapeHtml(quote ? quoteSource(quote) : '...')}</span>
            </span>
            <span class="quote-price">${quote ? formatQuotePrice(quote.price, quote.decimals ?? 2) : '--'}</span>
            <span class="quote-change">${quote ? formatQuoteChange(quote.change, quote.change_pct) : '--'}</span>
            <span class="quote-card-actions">
                <span class="quote-move" data-quote-move="${escapeHtml(card.symbol)}" data-quote-direction="-1" aria-label="Deplacer vers la gauche">‹</span>
                <span class="quote-move" data-quote-move="${escapeHtml(card.symbol)}" data-quote-direction="1" aria-label="Deplacer vers la droite">›</span>
                <span class="quote-replace" data-quote-replace="${escapeHtml(card.symbol)}" aria-label="Remplacer cette carte">↻</span>
                <span class="quote-remove" data-quote-remove="${escapeHtml(card.symbol)}" aria-label="Retirer cette carte">x</span>
            </span>
        </button>
    `;
}

function profileCategory(profile) {
    return profile.category || 'forex_major';
}

function profileMatches(profile, query) {
    if (!query) return true;
    const symbol = String(profile.symbol || '');
    const haystack = normalizeSearch([
        profile.label,
        symbol,
        compactSymbol(symbol),
        profile.description,
        profile.aliases?.join(' '),
        profile.countries?.join(' '),
        profileCategory(profile),
    ].join(' '));
    return haystack.includes(normalizeSearch(query));
}

function customSymbolFromQuery(query) {
    const raw = String(query || '').trim().toUpperCase();
    const clean = raw.replace(/[^A-Z0-9]/g, '');
    if (!clean || clean.length < 2) return null;
    if (raw.includes(':')) return raw;
    if (['XAUUSD', 'XAGUSD', 'XPTUSD', 'XPDUSD'].includes(clean)) return `OANDA:${clean}`;
    if (/^[A-Z]{6}$/.test(clean)) return `FX:${clean}`;
    if (clean.endsWith('USD')) return `BITSTAMP:${clean}`;
    return clean;
}

function cardFromProfile(profile) {
    return cardFromSymbol({ symbol: profile.symbol, label: profile.label });
}

function renderQuotePickerCard(profile, selectedSymbols) {
    const selected = selectedSymbols.has(compactSymbol(profile.symbol).replace(/[^A-Z0-9]/g, ''));
    return `
        <button type="button" class="quote-picker-card ${selected ? 'selected' : ''}" data-quote-profile="${escapeHtml(profile.id)}">
            <span>
                <strong>${escapeHtml(profile.label)}</strong>
                <em>${escapeHtml(compactSymbol(profile.symbol))}</em>
            </span>
            <small>${escapeHtml(profile.description || 'Market profile')}</small>
            <b>${selected ? 'DEJA AJOUTE' : 'AJOUTER'}</b>
        </button>`;
}

function renderQuotePickerCustomCard(symbol) {
    return `
        <button type="button" class="quote-picker-card custom" data-quote-custom-symbol="${escapeHtml(symbol)}">
            <span>
                <strong>${escapeHtml(formatSymbolLabel(symbol))}</strong>
                <em>${escapeHtml(compactSymbol(symbol))}</em>
            </span>
            <small>Ajouter ce symbole TradingView aux cartes temps réel.</small>
            <b>AJOUTER</b>
        </button>`;
}

function renderQuoteSlots({ cards = [], quotes = [], currentSymbol = '' } = {}) {
    const header = document.querySelector('.header');
    if (!header) return;

    const clean = cleanCards(cards);
    const bySymbol = new Map();
    const byKey = new Map();
    quotes.forEach((quote) => {
        bySymbol.set(normalizeSymbol(quoteSymbol(quote)), quote);
        bySymbol.set(normalizeSymbol(quote.symbol), quote);
        byKey.set(quoteKey(quote), quote);
    });

    const slots = [];
    for (let index = 0; index < QUOTE_SLOT_COUNT; index += 1) {
        const card = clean[index];
        if (!card) {
            slots.push(renderEmptyCard(index));
            continue;
        }
        const quote = bySymbol.get(normalizeSymbol(card.symbol)) || byKey.get(quoteKey(card));
        slots.push(renderFilledCard(card, quote, currentSymbol));
    }
    header.innerHTML = slots.join('');
}

async function refreshQuotes({ hasAccess, getCurrentSymbol, getQuoteCards }) {
    if (!hasAccess()) return;

    const cards = cleanCards(getQuoteCards?.() || []);
    renderQuoteSlots({ cards, quotes: latestQuotes, currentSymbol: getCurrentSymbol() });
    if (!cards.length) return;

    try {
        const payload = await fetchMarketQuotes(cards.map((card) => card.symbol));
        latestQuotes = payload.items || [];
        renderQuoteSlots({
            cards,
            quotes: latestQuotes,
            currentSymbol: getCurrentSymbol(),
        });
    } catch (error) {
        console.error(error);
    }
}

export function startQuotesRefresh(options) {
    window.clearInterval(quotesRefreshTimer);
    refreshQuotes(options);
    quotesRefreshTimer = window.setInterval(() => refreshQuotes(options), QUOTES_REFRESH_MS);
}

export function renderPersonalQuoteCards(cards, currentSymbol = '') {
    renderQuoteSlots({ cards, quotes: latestQuotes, currentSymbol });
}

export function syncActiveQuoteCard(currentSymbol = '') {
    const activeSymbol = normalizeSymbol(currentSymbol);
    document.querySelectorAll('.qcard[data-symbol]').forEach((card) => {
        const symbol = normalizeSymbol(card.dataset.symbol);
        const cardSymbol = normalizeSymbol(card.dataset.quoteCardSymbol);
        card.classList.toggle('active', symbol === activeSymbol || cardSymbol === activeSymbol);
    });
}

export function bindQuoteCards({ onSymbolSelect, getCurrentSymbol, getQuoteCards, setQuoteCards, savePrefs, refreshQuotesNow }) {
    const header = document.querySelector('.header');
    if (!header) return;

    let pickerSlotIndex = null;
    let pickerCategory = CATEGORY_ALL;

    function selectedSymbolKeys(cards = []) {
        return new Set(cleanCards(cards).map((card) => compactSymbol(card.symbol).replace(/[^A-Z0-9]/g, '')));
    }

    function commitQuoteCard(nextCard, slotIndex = pickerSlotIndex) {
        if (!nextCard) return;
        const currentCards = cleanCards(getQuoteCards());
        const nextCards = [...currentCards];
        const targetIndex = Number.isInteger(slotIndex) ? slotIndex : nextCards.length;
        if (targetIndex >= 0 && targetIndex < QUOTE_SLOT_COUNT) {
            nextCards[targetIndex] = nextCard;
        } else {
            nextCards.push(nextCard);
        }
        const clean = cleanCards(nextCards);
        setQuoteCards(clean);
        savePrefs({ quoteCards: clean });
        renderQuoteSlots({ cards: clean, currentSymbol: getCurrentSymbol?.() || '' });
        refreshQuotesNow?.();
    }

    function ensureQuotePicker() {
        let picker = document.getElementById('quote-picker');
        if (picker) return picker;

        picker = document.createElement('div');
        picker.id = 'quote-picker';
        picker.className = 'quote-picker-overlay hidden';
        picker.innerHTML = `
            <div class="quote-picker-panel" role="dialog" aria-modal="true" aria-labelledby="quote-picker-title">
                <div class="quote-picker-head">
                    <div>
                        <span>QUOTE CARDS</span>
                        <h2 id="quote-picker-title">Ajouter un marché</h2>
                    </div>
                    <button type="button" class="panel-btn" data-quote-picker-close title="Fermer">x</button>
                </div>
                <div class="quote-picker-tools">
                    <input id="quote-picker-search" type="search" placeholder="Rechercher XAU/USD, ETH, NASDAQ, GBP/JPY..." autocomplete="off" spellcheck="false">
                    <span id="quote-picker-count" class="desk-pill">0 marché</span>
                </div>
                <div id="quote-picker-categories" class="quote-picker-categories"></div>
                <div id="quote-picker-results" class="quote-picker-results"></div>
            </div>`;
        document.body.appendChild(picker);
        return picker;
    }

    function closeQuotePicker() {
        const picker = document.getElementById('quote-picker');
        picker?.classList.add('hidden');
        pickerSlotIndex = null;
    }

    function renderQuotePicker() {
        const picker = ensureQuotePicker();
        const search = picker.querySelector('#quote-picker-search');
        const categoryRoot = picker.querySelector('#quote-picker-categories');
        const resultsRoot = picker.querySelector('#quote-picker-results');
        const countEl = picker.querySelector('#quote-picker-count');
        const query = search?.value.trim() || '';
        const categories = [{ id: CATEGORY_ALL, label: 'Tous' }, ...MARKET_CATEGORIES.filter((category) => category.id !== 'favorites')];
        const selected = selectedSymbolKeys(getQuoteCards());
        const profiles = Object.values(MARKET_PROFILES).filter((profile) => {
            const matchesCategory = pickerCategory === CATEGORY_ALL || profileCategory(profile) === pickerCategory;
            return matchesCategory && profileMatches(profile, query);
        });
        const customSymbol = customSymbolFromQuery(query);
        const hasExactProfile = customSymbol && Object.values(MARKET_PROFILES).some((profile) => (
            compactSymbol(profile.symbol).replace(/[^A-Z0-9]/g, '') === compactSymbol(customSymbol).replace(/[^A-Z0-9]/g, '')
        ));
        const customCard = customSymbol && !hasExactProfile ? renderQuotePickerCustomCard(customSymbol) : '';

        categoryRoot.innerHTML = categories.map((category) => `
            <button type="button" class="market-filter ${category.id === pickerCategory ? 'active' : ''}" data-quote-picker-category="${escapeHtml(category.id)}">${escapeHtml(category.label)}</button>
        `).join('');

        resultsRoot.innerHTML = profiles.length || customCard
            ? `${profiles.map((profile) => renderQuotePickerCard(profile, selected)).join('')}${customCard}`
            : '<div class="market-selector-empty">Aucun marché trouvé. Essaie EURUSD, XAG/USD, ETHUSD ou NASDAQ:QQQ.</div>';

        if (countEl) {
            const count = profiles.length + (customCard ? 1 : 0);
            countEl.textContent = `${count} marché${count > 1 ? 's' : ''}`;
        }

        categoryRoot.querySelectorAll('[data-quote-picker-category]').forEach((button) => {
            button.addEventListener('click', () => {
                pickerCategory = button.dataset.quotePickerCategory || CATEGORY_ALL;
                renderQuotePicker();
            });
        });

        resultsRoot.querySelectorAll('[data-quote-profile]').forEach((button) => {
            button.addEventListener('click', () => {
                const profile = MARKET_PROFILES[button.dataset.quoteProfile];
                if (!profile) return;
                commitQuoteCard(cardFromProfile(profile));
                closeQuotePicker();
            });
        });

        resultsRoot.querySelectorAll('[data-quote-custom-symbol]').forEach((button) => {
            button.addEventListener('click', () => {
                const symbol = button.dataset.quoteCustomSymbol;
                const nextCard = cardFromSymbol(symbol);
                if (!nextCard) return;
                commitQuoteCard(nextCard);
                closeQuotePicker();
            });
        });
    }

    function openQuotePicker(slotIndex = null) {
        const picker = ensureQuotePicker();
        pickerSlotIndex = Number.isInteger(slotIndex) ? slotIndex : null;
        pickerCategory = CATEGORY_ALL;
        picker.classList.remove('hidden');
        const input = picker.querySelector('#quote-picker-search');
        if (input) input.value = '';
        renderQuotePicker();
        input?.focus();
    }

    const picker = ensureQuotePicker();
    picker.querySelector('[data-quote-picker-close]')?.addEventListener('click', closeQuotePicker);
    picker.querySelector('#quote-picker-search')?.addEventListener('input', renderQuotePicker);
    picker.addEventListener('click', (event) => {
        if (event.target === picker) closeQuotePicker();
    });
    window.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !picker.classList.contains('hidden')) {
            closeQuotePicker();
        }
    });

    header.addEventListener('click', (event) => {
        const moveButton = event.target.closest('[data-quote-move]');
        if (moveButton) {
            event.stopPropagation();
            const symbol = moveButton.dataset.quoteMove;
            const direction = Number.parseInt(moveButton.dataset.quoteDirection || '0', 10);
            const nextCards = cleanCards(getQuoteCards());
            const index = nextCards.findIndex((card) => card.symbol === symbol);
            const nextIndex = index + direction;
            if (index >= 0 && nextIndex >= 0 && nextIndex < nextCards.length) {
                [nextCards[index], nextCards[nextIndex]] = [nextCards[nextIndex], nextCards[index]];
                setQuoteCards(nextCards);
                savePrefs({ quoteCards: nextCards });
                renderQuoteSlots({ cards: nextCards, quotes: latestQuotes, currentSymbol: getCurrentSymbol?.() || '' });
            }
            return;
        }

        const removeButton = event.target.closest('[data-quote-remove]');
        if (removeButton) {
            event.stopPropagation();
            const symbol = removeButton.dataset.quoteRemove;
            const nextCards = cleanCards(getQuoteCards()).filter((card) => card.symbol !== symbol);
            setQuoteCards(nextCards);
            savePrefs({ quoteCards: nextCards });
            renderQuoteSlots({ cards: nextCards, currentSymbol: getCurrentSymbol?.() || '' });
            refreshQuotesNow?.();
            return;
        }

        const replaceButton = event.target.closest('[data-quote-replace]');
        if (replaceButton) {
            event.stopPropagation();
            const symbol = replaceButton.dataset.quoteReplace;
            const slotIndex = cleanCards(getQuoteCards()).findIndex((card) => card.symbol === symbol);
            openQuotePicker(slotIndex >= 0 ? slotIndex : null);
            return;
        }

        const emptyCard = event.target.closest('[data-quote-empty]');
        if (emptyCard) {
            const slotIndex = Number.parseInt(emptyCard.dataset.quoteEmpty || '', 10);
            openQuotePicker(Number.isInteger(slotIndex) ? slotIndex : null);
            return;
        }

        const card = event.target.closest('.qcard[data-symbol]');
        const symbol = card?.dataset.symbol;
        if (symbol) {
            onSymbolSelect(symbol);
        }
    });
}
