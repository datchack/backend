async function readJsonResponse(response, fallbackMessage) {
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.detail || fallbackMessage);
    }
    return payload;
}

export async function fetchMarketQuotes() {
    const response = await fetch('/api/market-quotes', { cache: 'no-store' });
    return readJsonResponse(response, 'Quotes unavailable');
}

export async function fetchCalendarFeed(profile, countries) {
    const response = await fetch(`/api/calendar?profile=${profile}&countries=${countries}`, { cache: 'no-store' });
    return readJsonResponse(response, 'Calendar unavailable');
}

export async function fetchMarketContext(profile, countries) {
    const response = await fetch(`/api/context?profile=${profile}&countries=${countries}`, { cache: 'no-store' });
    return readJsonResponse(response, 'Context unavailable');
}

export async function fetchNewsFeed(profile) {
    const response = await fetch(`/api/news?profile=${profile}`);
    return readJsonResponse(response, 'News unavailable');
}
