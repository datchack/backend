import { formatLayerScore, formatSignedPercent, formatValue } from './terminal-formatters.js';

export function renderBiasCard(context) {
    const card = document.getElementById('bias-card');
    const scoreEl = document.getElementById('bias-score');
    const labelEl = document.getElementById('bias-label');
    const actionEl = document.getElementById('bias-action');
    const toneEl = document.getElementById('bias-tone');
    const layersEl = document.getElementById('bias-layers');
    const reasonsEl = document.getElementById('bias-reasons');
    const confidenceEl = document.getElementById('confidence-badge');
    const volEl = document.getElementById('volatility-badge');
    const sessionEl = document.getElementById('session-active');
    const statusContext = document.getElementById('status-context');
    const snapshotBias = document.getElementById('snapshot-bias');
    const snapshotSession = document.getElementById('snapshot-session');
    const snapshotVol = document.getElementById('snapshot-vol');
    const titleEl = document.getElementById('bias-card-title');
    const driverTitleEl = document.getElementById('driver-card-title');
    const watchTitleEl = document.getElementById('watch-card-title');

    if (!card || !scoreEl || !labelEl || !actionEl || !toneEl || !layersEl || !reasonsEl || !confidenceEl || !volEl || !sessionEl) return;

    const toneClass = context.bias === 'Bullish' ? 'bullish' : context.bias === 'Bearish' ? 'bearish' : 'neutral';
    card.classList.remove('bullish', 'bearish', 'neutral');
    card.classList.add(toneClass);

    scoreEl.textContent = `${context.score > 0 ? '+' : ''}${Number(context.score).toFixed(1)}`;
    scoreEl.className = `desk-pill ${toneClass}`;
    labelEl.textContent = context.bias.toUpperCase();
    labelEl.className = `bias-label ${toneClass}`;
    actionEl.textContent = context.action || 'WAIT';
    actionEl.className = `bias-action ${context.action === 'NO TRADE' ? 'neutral' : toneClass}`;
    if (titleEl) titleEl.textContent = `${context.bias_name || context.title || 'MARKET'} BIAS`;
    if (driverTitleEl) driverTitleEl.textContent = `${context.bias_name || context.title || 'MARKET'} DRIVERS`;
    if (watchTitleEl) watchTitleEl.textContent = `${context.bias_name || context.title || 'MARKET'} WATCH`;

    const target = context.target || context.gold;
    const targetLabel = context.target_label || context.bias_name || 'Market';
    toneEl.textContent = `${(context.action_reason || context.tone).toUpperCase()} - ${context.summary || (target ? `${targetLabel} ${formatSignedPercent(target.change_pct)}` : 'Market feed live')}`;
    const layers = context.layers || {};
    const eventRisk = layers.event_risk || {};
    const eventMinutes = ['High', 'Elevated'].includes(eventRisk.level) && eventRisk.minutes !== null && eventRisk.minutes !== undefined
        ? ` ${eventRisk.minutes}m`
        : '';
    layersEl.innerHTML = `
        <span class="bias-layer ${String(layers.macro?.label || '').toLowerCase()}">MACRO ${layers.macro?.label || '-'} ${formatLayerScore(layers.macro?.score)}</span>
        <span class="bias-layer ${String(layers.momentum?.label || '').toLowerCase()}">MOMO ${layers.momentum?.label || '-'} ${formatLayerScore(layers.momentum?.score)}</span>
        <span class="bias-layer ${String(eventRisk.level || '').toLowerCase()}">EVENT ${eventRisk.level || '-'}${eventMinutes}</span>
    `;
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
        statusContext.textContent = `${context.bias_name || 'Bias'}: ${context.action || context.bias} (${context.score > 0 ? '+' : ''}${Number(context.score).toFixed(1)}) - ${context.confidence || 0}%`;
    }
}

export function renderDrivers(context) {
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

export function renderWatchlist(context, { selectedKeys = null, onSymbolSelect = null } = {}) {
    const root = document.getElementById('watchlist-grid');
    if (!root) return;

    const base = context.available_watchlist || context.watchlist || [];
    const selected = Array.isArray(selectedKeys) && selectedKeys.length
        ? base.filter((item) => selectedKeys.includes(item.key))
        : (context.watchlist || base);

    root.innerHTML = selected.map((item) => {
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
                'TLT': 'NASDAQ:TLT',
                'EURUSD=X': 'FX:EURUSD',
                'GBPUSD=X': 'FX:GBPUSD',
                'JPY=X': 'FX:USDJPY',
                'BTC-USD': 'BITSTAMP:BTCUSD',
            };
            onSymbolSelect?.(tvMap[symbol] || symbol);
        });
    });
}

export function renderMarketContext(context, options = {}) {
    renderBiasCard(context);
    renderDrivers(context);
    renderWatchlist(context, options);
}
