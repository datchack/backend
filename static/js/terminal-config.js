export const PREFS_KEY = 'tt_prefs_v1';
export const CALENDAR_REFRESH_MS = 60000;
export const NEWS_REFRESH_MS = 8000;
export const CONTEXT_REFRESH_MS = 15000;
export const QUOTES_REFRESH_MS = 5000;
export const IMPACT_LEVELS = ['High', 'Medium', 'Low'];
export const DEFAULT_ACCOUNT_MODE = 'register';
export const DEFAULT_MARKET_PROFILE = 'xauusd';

export const MARKET_PROFILES = {
    xauusd: { id: 'xauusd', label: 'XAU/USD', symbol: 'OANDA:XAUUSD', countries: ['US'], category: 'metals', featured: true, description: 'Gold macro profile' },
    xagusd: { id: 'xagusd', label: 'XAG/USD', symbol: 'OANDA:XAGUSD', countries: ['US'], category: 'metals', description: 'Silver macro profile' },
    eurusd: { id: 'eurusd', label: 'EUR/USD', symbol: 'FX:EURUSD', countries: ['US', 'EU'], category: 'forex_major', featured: true, description: 'Euro dollar benchmark' },
    usdjpy: { id: 'usdjpy', label: 'USD/JPY', symbol: 'FX:USDJPY', countries: ['US', 'JP'], category: 'forex_major', featured: true, description: 'US yields and yen risk' },
    gbpusd: { id: 'gbpusd', label: 'GBP/USD', symbol: 'FX:GBPUSD', countries: ['US', 'GB'], category: 'forex_major', featured: true, description: 'Sterling and dollar profile' },
    usdcny: { id: 'usdcny', label: 'USD/CNY', symbol: 'FX:USDCNY', countries: ['US', 'CN'], category: 'forex_major', description: 'China yuan and dollar radar' },
    usdcad: { id: 'usdcad', label: 'USD/CAD', symbol: 'FX:USDCAD', countries: ['US', 'CA'], category: 'forex_major', description: 'Dollar, Canada and oil' },
    audusd: { id: 'audusd', label: 'AUD/USD', symbol: 'FX:AUDUSD', countries: ['US', 'AU', 'CN'], category: 'forex_major', description: 'Aussie, China and risk' },
    usdchf: { id: 'usdchf', label: 'USD/CHF', symbol: 'FX:USDCHF', countries: ['US', 'CH'], category: 'forex_major', description: 'Swiss franc and risk-off' },
    usdhkd: { id: 'usdhkd', label: 'USD/HKD', symbol: 'FX:USDHKD', countries: ['US', 'HK'], category: 'forex_major', description: 'Hong Kong dollar peg context' },
    nzdusd: { id: 'nzdusd', label: 'NZD/USD', symbol: 'FX:NZDUSD', countries: ['US', 'NZ', 'CN'], category: 'forex_major', description: 'Kiwi, China and risk' },
    eurjpy: { id: 'eurjpy', label: 'EUR/JPY', symbol: 'FX:EURJPY', countries: ['EU', 'JP'], category: 'forex_cross', description: 'Euro yen cross' },
    eurgbp: { id: 'eurgbp', label: 'EUR/GBP', symbol: 'FX:EURGBP', countries: ['EU', 'GB'], category: 'forex_cross', description: 'ECB versus BoE cross' },
    gbpjpy: { id: 'gbpjpy', label: 'GBP/JPY', symbol: 'FX:GBPJPY', countries: ['GB', 'JP'], category: 'forex_cross', description: 'Sterling yen volatility' },
    nasdaq: { id: 'nasdaq', label: 'NASDAQ', symbol: 'NASDAQ:QQQ', countries: ['US'], category: 'indices', featured: true, description: 'US tech and yields' },
    btcusd: { id: 'btcusd', label: 'BTC/USD', symbol: 'BITSTAMP:BTCUSD', countries: ['US'], category: 'crypto', featured: true, description: 'Bitcoin liquidity profile' },
};

export const MARKET_CATEGORIES = [
    { id: 'favorites', label: 'Favoris' },
    { id: 'forex_major', label: 'Forex majeures' },
    { id: 'forex_cross', label: 'Forex crosses' },
    { id: 'metals', label: 'Métaux' },
    { id: 'indices', label: 'Indices' },
    { id: 'crypto', label: 'Crypto' },
];

export const CALENDAR_COUNTRY_OPTIONS = ['US', 'EU', 'JP', 'GB', 'CN', 'CA', 'AU', 'NZ', 'CH', 'HK', 'DE', 'FR'];

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
