import { QUOTES_REFRESH_MS } from './terminal-config.js';
import { formatQuoteChange, formatQuotePrice } from './terminal-formatters.js';
import { fetchMarketQuotes } from './terminal-market-api.js';

const QUOTE_SLOT_COUNT = 8;

let quotesRefreshTimer = null;
let latestQuotes = [];

function normalizeSymbol(symbol) {
    return String(symbol || '').trim().toUpperCase();
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

function cardFromSymbol(symbol) {
    const normalized = normalizeSymbol(symbol);
    if (!normalized) return null;
    return {
        symbol: normalized,
        label: normalized.split(':').pop().replace(/[^A-Z0-9]/g, ''),
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
    const classes = ['qcard', tone, active, loading, tickTone].filter(Boolean).join(' ');

    return `
        <button type="button" class="${classes}" data-symbol="${symbol}" data-quote-card-symbol="${card.symbol}" data-quote-key="${key}" data-price="${Number.isFinite(price) ? price : ''}">
            <span class="quote-accent"></span>
            <span class="quote-card-head">
                <span>
                    <strong>${quote?.label || card.label || symbol}</strong>
                    <em>${quote ? quoteName(quote) : 'Chargement'}</em>
                </span>
                <span class="quote-source">${quote ? quoteSource(quote) : '...'}</span>
            </span>
            <span class="quote-price">${quote ? formatQuotePrice(quote.price, quote.decimals ?? 2) : '--'}</span>
            <span class="quote-change">${quote ? formatQuoteChange(quote.change, quote.change_pct) : '--'}</span>
            <span class="quote-remove" data-quote-remove="${card.symbol}" aria-label="Retirer cette carte">x</span>
        </button>
    `;
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
    renderQuoteSlots({ cards, currentSymbol });
}

export function bindQuoteCards({ onSymbolSelect, getCurrentSymbol, getQuoteCards, setQuoteCards, savePrefs, refreshQuotesNow }) {
    const header = document.querySelector('.header');
    if (!header) return;

    header.addEventListener('click', (event) => {
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

        const emptyCard = event.target.closest('[data-quote-empty]');
        if (emptyCard) {
            const value = window.prompt('Symbole de la carte (ex: EURUSD, CAPITALCOM:DXY, NASDAQ:QQQ)');
            const nextCard = cardFromSymbol(value);
            if (!nextCard) return;
            const nextCards = cleanCards([...getQuoteCards(), nextCard]);
            setQuoteCards(nextCards);
            savePrefs({ quoteCards: nextCards });
            renderQuoteSlots({ cards: nextCards, currentSymbol: getCurrentSymbol?.() || '' });
            refreshQuotesNow?.();
            return;
        }

        const card = event.target.closest('.qcard[data-symbol]');
        const symbol = card?.dataset.symbol;
        if (symbol) {
            onSymbolSelect(symbol);
        }
    });
}
