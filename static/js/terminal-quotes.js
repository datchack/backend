import { QUOTES_REFRESH_MS } from './terminal-config.js';
import { formatQuoteChange, formatQuotePrice } from './terminal-formatters.js';
import { fetchMarketQuotes } from './terminal-market-api.js';

let quotesRefreshTimer = null;
let quoteSocket = null;
let quoteSocketReconnectTimer = null;

function getQuoteSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/market-quotes`;
}

function renderQuoteCards(items = [], currentSymbol = '') {
    const byKey = new Map(items.map((item) => [item.key, item]));
    document.querySelectorAll('.qcard').forEach((card) => {
        const quote = byKey.get(card.dataset.quoteKey);
        if (!quote) return;

        const change = Number(quote.change || 0);
        const nextPrice = Number(quote.price);
        const prevPrice = Number(card.dataset.price);
        const tickTone = Number.isFinite(prevPrice) && Number.isFinite(nextPrice) && nextPrice !== prevPrice
            ? nextPrice > prevPrice ? 'tick-up' : 'tick-down'
            : '';
        const tone = change > 0 ? 'up' : change < 0 ? 'down' : 'flat';
        card.classList.remove('loading', 'up', 'down', 'flat', 'tick-up', 'tick-down');
        card.classList.add(tone);
        if (tickTone) {
            window.setTimeout(() => {
                card.classList.remove('tick-up', 'tick-down');
                card.classList.add(tickTone);
            }, 0);
        }
        card.dataset.price = Number.isFinite(nextPrice) ? String(nextPrice) : '';
        card.dataset.symbol = quote.tv_symbol || card.dataset.symbol;
        card.classList.toggle('active', card.dataset.symbol === currentSymbol);
        card.innerHTML = `
            <span class="quote-accent"></span>
            <span class="quote-card-head">
                <span>
                    <strong>${quote.label || quote.symbol}</strong>
                    <em>${quote.name || ''}</em>
                </span>
                <span class="quote-source">${quote.source || 'FMP'}</span>
            </span>
            <span class="quote-price">${formatQuotePrice(quote.price, quote.decimals ?? 2)}</span>
            <span class="quote-change">${formatQuoteChange(quote.change, quote.change_pct)}</span>
        `;
    });
}

function connectQuoteStream({ hasAccess, getCurrentSymbol }) {
    if (!hasAccess() || quoteSocket?.readyState === WebSocket.OPEN || quoteSocket?.readyState === WebSocket.CONNECTING) {
        return;
    }

    window.clearTimeout(quoteSocketReconnectTimer);
    quoteSocket = new WebSocket(getQuoteSocketUrl());

    quoteSocket.addEventListener('message', (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload.type === 'snapshot') {
                renderQuoteCards(payload.items || [], getCurrentSymbol());
            } else if (payload.type === 'quote' && payload.item) {
                renderQuoteCards([payload.item], getCurrentSymbol());
            }
        } catch (error) {
            console.error(error);
        }
    });

    quoteSocket.addEventListener('close', () => {
        quoteSocket = null;
        if (hasAccess()) {
            quoteSocketReconnectTimer = window.setTimeout(() => connectQuoteStream({ hasAccess, getCurrentSymbol }), 3000);
        }
    });

    quoteSocket.addEventListener('error', () => {
        quoteSocket?.close();
    });
}

async function getMarketQuotes({ hasAccess, getCurrentSymbol }) {
    if (!hasAccess()) return;

    try {
        const payload = await fetchMarketQuotes();
        renderQuoteCards(payload.items || [], getCurrentSymbol());
    } catch (error) {
        console.error(error);
        document.querySelectorAll('.qcard.loading').forEach((card) => {
            card.innerHTML = `<span class="quote-loading">${card.dataset.quoteKey || 'QUOTE'} indisponible</span>`;
        });
    }
}

export function startQuotesRefresh(options) {
    window.clearInterval(quotesRefreshTimer);
    getMarketQuotes(options);
    connectQuoteStream(options);
    quotesRefreshTimer = window.setInterval(() => {
        getMarketQuotes(options);
        connectQuoteStream(options);
    }, QUOTES_REFRESH_MS);
}

export function bindQuoteCards(changeChart) {
    const header = document.querySelector('.header');
    if (!header) return;

    header.addEventListener('click', (event) => {
        const card = event.target.closest('.qcard');
        const symbol = card?.dataset.symbol;
        if (symbol) {
            changeChart(symbol);
        }
    });
}
