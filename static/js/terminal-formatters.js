export function formatQuotePrice(value, decimals = 2) {
    const number = Number(value);
    if (!Number.isFinite(number)) return '--';
    return number.toLocaleString('fr-FR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

export function formatQuoteChange(value, pct) {
    const change = Number(value);
    const changePct = Number(pct);
    if (!Number.isFinite(change) || !Number.isFinite(changePct)) return '--';
    const sign = change > 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${changePct.toFixed(2)}%)`;
}

export function formatValue(value, unit = '') {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    const text = typeof value === 'number' ? value.toLocaleString('en-US', { maximumFractionDigits: 3 }) : String(value);
    return unit ? `${text}${unit}` : text;
}

export function formatSignedPercent(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return '-';
    }
    const num = Number(value);
    return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`;
}

export function formatLayerScore(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return '';
    }
    const num = Number(value);
    return `${num > 0 ? '+' : ''}${num.toFixed(1)}`;
}

export function parseComparable(value) {
    if (value === null || value === undefined || value === '') {
        return NaN;
    }
    return Number.parseFloat(String(value).replace(/[^\d.-]/g, ''));
}

export function isLowerBetterCalendarEvent(title = '') {
    const lowerTitle = title.toLowerCase();
    const lowerIsBetterKeywords = [
        'unemployment',
        'jobless',
        'claims',
        'claimant',
        'layoffs',
        'layoff',
        'challenger job cuts',
        'inventories',
        'stock change',
        'deficit',
        'debt',
        'delinquency',
        'bankruptcy',
        'bankruptcies',
        'default',
    ];
    return lowerIsBetterKeywords.some((keyword) => lowerTitle.includes(keyword));
}

export function getActualVsPreviousTone(event) {
    const actual = parseComparable(event.actual);
    const previous = parseComparable(event.previous);
    if (Number.isNaN(actual) || Number.isNaN(previous) || actual === previous) {
        return '';
    }

    const higherIsBetter = !isLowerBetterCalendarEvent(event.title || '');
    const good = higherIsBetter ? actual > previous : actual < previous;
    return good ? 'good' : 'bad';
}

export function getCalendarBiasClass(event) {
    const actual = parseComparable(event.actual);
    const forecast = parseComparable(event.forecast);
    if (Number.isNaN(actual) || Number.isNaN(forecast)) {
        return '';
    }

    const lowerIsBetter = isLowerBetterCalendarEvent(event.title || '');
    const betterThanForecast = lowerIsBetter ? actual < forecast : actual > forecast;

    if (actual === forecast) {
        return '';
    }
    return betterThanForecast ? 'cal-green' : 'cal-red';
}

export function getDateKeyFromTs(ts, timeZone = 'Europe/Paris') {
    const formatter = new Intl.DateTimeFormat('en-CA', {
        timeZone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
    });
    return formatter.format(new Date(ts * 1000));
}

export function getDateKeyFromIso(isoString, timeZone = 'Europe/Paris') {
    const date = new Date(isoString);
    return getDateKeyFromTs(Math.floor(date.getTime() / 1000), timeZone);
}

export function addDays(date, days) {
    const next = new Date(date);
    next.setDate(next.getDate() + days);
    return next;
}

export function sourceClass(source) {
    return String(source || '').replace(/[^A-Z0-9_-]/gi, '_');
}
