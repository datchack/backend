export const PREFS_KEY = 'tt_prefs_v1';
export const CALENDAR_REFRESH_MS = 60000;
export const NEWS_REFRESH_MS = 8000;
export const CONTEXT_REFRESH_MS = 15000;
export const QUOTES_REFRESH_MS = 5000;
export const IMPACT_LEVELS = ['High', 'Medium', 'Low'];
export const DEFAULT_ACCOUNT_MODE = 'register';
export const DEFAULT_MARKET_PROFILE = 'xauusd';

export const MARKET_PROFILES = {
    xauusd: { id: 'xauusd', label: 'XAU/USD', symbol: 'OANDA:XAUUSD', countries: ['US'] },
    usdjpy: { id: 'usdjpy', label: 'USD/JPY', symbol: 'FX:USDJPY', countries: ['US', 'JP'] },
    eurusd: { id: 'eurusd', label: 'EUR/USD', symbol: 'FX:EURUSD', countries: ['US', 'EU'] },
    gbpusd: { id: 'gbpusd', label: 'GBP/USD', symbol: 'FX:GBPUSD', countries: ['US', 'GB'] },
    nasdaq: { id: 'nasdaq', label: 'NASDAQ', symbol: 'NASDAQ:QQQ', countries: ['US'] },
    btcusd: { id: 'btcusd', label: 'BTC/USD', symbol: 'BITSTAMP:BTCUSD', countries: ['US'] },
};

export const CALENDAR_COUNTRY_OPTIONS = ['US', 'EU', 'JP', 'GB', 'CN', 'CA', 'AU', 'DE', 'FR'];

export const WIDGET_OPTIONS = [
    { key: 'ticker', label: 'Ticker' },
    { key: 'quotes', label: 'Quotes' },
    { key: 'calendar', label: 'Calendar' },
    { key: 'chart', label: 'Chart' },
    { key: 'bias', label: 'Bias' },
    { key: 'news', label: 'News' },
];

export const DEFAULT_WIDGETS = {
    ticker: true,
    quotes: true,
    calendar: true,
    chart: true,
    bias: true,
    news: true,
};

export const DEFAULT_LAYOUT = {
    leftWidth: 340,
    rightWidth: 340,
    insightWidth: 320,
    collapsed: {
        left: false,
        right: false,
        chart: false,
        insight: false,
    },
};

export const MARKETS = {
    NY: { tz: 'America/New_York', label: 'NEW YORK', open: [9, 30], close: [16, 0] },
    LDN: { tz: 'Europe/London', label: 'LONDON', open: [8, 0], close: [16, 30] },
    TKY: { tz: 'Asia/Tokyo', label: 'TOKYO', open: [9, 0], close: [15, 0] },
    SYD: { tz: 'Australia/Sydney', label: 'SYDNEY', open: [10, 0], close: [16, 0] },
};
