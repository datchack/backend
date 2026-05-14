export const PREFS_KEY = 'tt_prefs_v1';
export const CALENDAR_REFRESH_MS = 60000;
export const NEWS_REFRESH_MS = 8000;
export const CONTEXT_REFRESH_MS = 15000;
export const QUOTES_REFRESH_MS = 5000;
export const IMPACT_LEVELS = ['High', 'Medium', 'Low'];
export const DEFAULT_ACCOUNT_MODE = 'register';
export const DEFAULT_MARKET_PROFILE = 'xauusd';

export const MARKET_PROFILES = {
    xauusd: { id: 'xauusd', label: 'XAU/USD', symbol: 'OANDA:XAUUSD', countries: ['US'], category: 'metals', featured: true, aliases: ['gold', 'or', 'xau', 'precious metals'], description: 'Gold macro profile' },
    xagusd: { id: 'xagusd', label: 'XAG/USD', symbol: 'OANDA:XAGUSD', countries: ['US'], category: 'metals', aliases: ['silver', 'argent', 'xag', 'precious metals'], description: 'Silver macro profile' },
    xptusd: { id: 'xptusd', label: 'XPT/USD', symbol: 'OANDA:XPTUSD', countries: ['US'], category: 'metals', aliases: ['platinum', 'platine', 'xpt'], description: 'Platinum and industrial metals' },
    xpdusd: { id: 'xpdusd', label: 'XPD/USD', symbol: 'OANDA:XPDUSD', countries: ['US'], category: 'metals', aliases: ['palladium', 'xpd'], description: 'Palladium and auto demand' },
    eurusd: { id: 'eurusd', label: 'EUR/USD', symbol: 'FX:EURUSD', countries: ['US', 'EU'], category: 'forex_major', featured: true, aliases: ['euro dollar', 'fiber', 'eurodollar'], description: 'Euro dollar benchmark' },
    usdjpy: { id: 'usdjpy', label: 'USD/JPY', symbol: 'FX:USDJPY', countries: ['US', 'JP'], category: 'forex_major', featured: true, aliases: ['dollar yen', 'yen', 'boj'], description: 'US yields and yen risk' },
    gbpusd: { id: 'gbpusd', label: 'GBP/USD', symbol: 'FX:GBPUSD', countries: ['US', 'GB'], category: 'forex_major', featured: true, aliases: ['cable', 'pound dollar', 'sterling'], description: 'Sterling and dollar profile' },
    usdcny: { id: 'usdcny', label: 'USD/CNY', symbol: 'FX:USDCNY', countries: ['US', 'CN'], category: 'forex_major', aliases: ['yuan', 'renminbi', 'china'], description: 'China yuan and dollar radar' },
    usdcad: { id: 'usdcad', label: 'USD/CAD', symbol: 'FX:USDCAD', countries: ['US', 'CA'], category: 'forex_major', aliases: ['loonie', 'canadian dollar', 'oil fx'], description: 'Dollar, Canada and oil' },
    audusd: { id: 'audusd', label: 'AUD/USD', symbol: 'FX:AUDUSD', countries: ['US', 'AU', 'CN'], category: 'forex_major', aliases: ['aussie', 'australian dollar', 'china proxy'], description: 'Aussie, China and risk' },
    usdchf: { id: 'usdchf', label: 'USD/CHF', symbol: 'FX:USDCHF', countries: ['US', 'CH'], category: 'forex_major', aliases: ['swissy', 'franc suisse', 'safe haven'], description: 'Swiss franc and risk-off' },
    usdhkd: { id: 'usdhkd', label: 'USD/HKD', symbol: 'FX:USDHKD', countries: ['US', 'HK'], category: 'forex_major', aliases: ['hong kong dollar', 'hkd peg'], description: 'Hong Kong dollar peg context' },
    nzdusd: { id: 'nzdusd', label: 'NZD/USD', symbol: 'FX:NZDUSD', countries: ['US', 'NZ', 'CN'], category: 'forex_major', aliases: ['kiwi', 'new zealand dollar'], description: 'Kiwi, China and risk' },
    eurjpy: { id: 'eurjpy', label: 'EUR/JPY', symbol: 'FX:EURJPY', countries: ['EU', 'JP'], category: 'forex_cross', aliases: ['euro yen', 'risk cross'], description: 'Euro yen cross' },
    eurgbp: { id: 'eurgbp', label: 'EUR/GBP', symbol: 'FX:EURGBP', countries: ['EU', 'GB'], category: 'forex_cross', aliases: ['euro sterling', 'ecb boe'], description: 'ECB versus BoE cross' },
    gbpjpy: { id: 'gbpjpy', label: 'GBP/JPY', symbol: 'FX:GBPJPY', countries: ['GB', 'JP'], category: 'forex_cross', aliases: ['sterling yen', 'dragon', 'volatility cross'], description: 'Sterling yen volatility' },
    spx: { id: 'spx', label: 'S&P 500', symbol: 'SP:SPX', countries: ['US'], category: 'indices', featured: true, aliases: ['sp500', 'us500', 's and p', 'standard poor'], description: 'US large cap benchmark' },
    nasdaq: { id: 'nasdaq', label: 'NASDAQ 100', symbol: 'NASDAQ:QQQ', countries: ['US'], category: 'indices', featured: true, aliases: ['nas100', 'us100', 'ndx', 'tech index'], description: 'US tech and yields' },
    dow: { id: 'dow', label: 'Dow Jones', symbol: 'DJ:DJI', countries: ['US'], category: 'indices', aliases: ['us30', 'djia', 'wall street'], description: 'US blue chip index' },
    russell: { id: 'russell', label: 'Russell 2000', symbol: 'TVC:RUT', countries: ['US'], category: 'indices', aliases: ['rut', 'small caps', 'us2000'], description: 'US small caps and risk appetite' },
    dax: { id: 'dax', label: 'DAX 40', symbol: 'XETR:DAX', countries: ['DE', 'EU'], category: 'indices', aliases: ['ger40', 'germany 40'], description: 'German equity benchmark' },
    cac: { id: 'cac', label: 'CAC 40', symbol: 'EURONEXT:PX1', countries: ['FR', 'EU'], category: 'indices', aliases: ['france 40', 'french index'], description: 'French equity benchmark' },
    ftse: { id: 'ftse', label: 'FTSE 100', symbol: 'TVC:UKX', countries: ['GB'], category: 'indices', aliases: ['uk100', 'footsie'], description: 'UK large cap benchmark' },
    nikkei: { id: 'nikkei', label: 'Nikkei 225', symbol: 'TVC:NI225', countries: ['JP'], category: 'indices', aliases: ['japan 225', 'jp225'], description: 'Japan equity benchmark' },
    hsi: { id: 'hsi', label: 'Hang Seng', symbol: 'HSI:HSI', countries: ['HK', 'CN'], category: 'indices', aliases: ['hong kong', 'hk50', 'china risk'], description: 'Hong Kong and China risk' },
    vix: { id: 'vix', label: 'VIX', symbol: 'TVC:VIX', countries: ['US'], category: 'indices', aliases: ['volatility', 'fear index'], description: 'US volatility index' },
    usoil: { id: 'usoil', label: 'WTI Oil', symbol: 'TVC:USOIL', countries: ['US'], category: 'commodities', aliases: ['wti', 'crude oil', 'petrole', 'oil'], description: 'US crude oil benchmark' },
    ukoil: { id: 'ukoil', label: 'Brent Oil', symbol: 'TVC:UKOIL', countries: ['US', 'GB'], category: 'commodities', aliases: ['brent', 'crude oil', 'petrole', 'oil'], description: 'Global crude oil benchmark' },
    natgas: { id: 'natgas', label: 'Natural Gas', symbol: 'TVC:NATGAS', countries: ['US'], category: 'commodities', aliases: ['gas', 'nat gas', 'gaz naturel'], description: 'US natural gas market' },
    copper: { id: 'copper', label: 'Copper', symbol: 'COMEX:HG1!', countries: ['US', 'CN'], category: 'commodities', aliases: ['cuivre', 'hg', 'industrial metals'], description: 'Growth and China demand proxy' },
    spy: { id: 'spy', label: 'SPY', symbol: 'AMEX:SPY', countries: ['US'], category: 'equity_etf', aliases: ['s&p etf', 'sp500 etf'], description: 'S&P 500 ETF proxy' },
    qqq: { id: 'qqq', label: 'QQQ', symbol: 'NASDAQ:QQQ', countries: ['US'], category: 'equity_etf', aliases: ['nasdaq etf', 'nas100 etf'], description: 'Nasdaq 100 ETF proxy' },
    tlt: { id: 'tlt', label: 'TLT', symbol: 'NASDAQ:TLT', countries: ['US'], category: 'equity_etf', aliases: ['bonds', 'treasury', 'duration', 'rates'], description: 'Long-duration US bonds ETF' },
    iwm: { id: 'iwm', label: 'IWM', symbol: 'AMEX:IWM', countries: ['US'], category: 'equity_etf', aliases: ['russell etf', 'small caps etf'], description: 'Russell 2000 ETF proxy' },
    btcusd: { id: 'btcusd', label: 'BTC/USD', symbol: 'BITSTAMP:BTCUSD', countries: ['US'], category: 'crypto', featured: true, aliases: ['bitcoin', 'btc'], description: 'Bitcoin liquidity profile' },
    ethusd: { id: 'ethusd', label: 'ETH/USD', symbol: 'BITSTAMP:ETHUSD', countries: ['US'], category: 'crypto', featured: true, aliases: ['ethereum', 'ether', 'eth'], description: 'Ethereum liquidity profile' },
    solusd: { id: 'solusd', label: 'SOL/USD', symbol: 'COINBASE:SOLUSD', countries: ['US'], category: 'crypto', aliases: ['solana', 'sol'], description: 'Solana beta profile' },
    xrpusd: { id: 'xrpusd', label: 'XRP/USD', symbol: 'BITSTAMP:XRPUSD', countries: ['US'], category: 'crypto', aliases: ['ripple', 'xrp'], description: 'XRP crypto profile' },
    bnbusd: { id: 'bnbusd', label: 'BNB/USD', symbol: 'BINANCE:BNBUSD', countries: ['US'], category: 'crypto', aliases: ['binance coin', 'bnb'], description: 'BNB crypto profile' },
    adausd: { id: 'adausd', label: 'ADA/USD', symbol: 'COINBASE:ADAUSD', countries: ['US'], category: 'crypto', aliases: ['cardano', 'ada'], description: 'Cardano crypto profile' },
    dogeusd: { id: 'dogeusd', label: 'DOGE/USD', symbol: 'COINBASE:DOGEUSD', countries: ['US'], category: 'crypto', aliases: ['dogecoin', 'doge'], description: 'Dogecoin crypto profile' },
    avaxusd: { id: 'avaxusd', label: 'AVAX/USD', symbol: 'COINBASE:AVAXUSD', countries: ['US'], category: 'crypto', aliases: ['avalanche', 'avax'], description: 'Avalanche crypto profile' },
    linkusd: { id: 'linkusd', label: 'LINK/USD', symbol: 'COINBASE:LINKUSD', countries: ['US'], category: 'crypto', aliases: ['chainlink', 'link'], description: 'Chainlink crypto profile' },
    ltcusd: { id: 'ltcusd', label: 'LTC/USD', symbol: 'COINBASE:LTCUSD', countries: ['US'], category: 'crypto', aliases: ['litecoin', 'ltc'], description: 'Litecoin crypto profile' },
};

export const MARKET_CATEGORIES = [
    { id: 'favorites', label: 'Favoris' },
    { id: 'forex_major', label: 'Forex majeures' },
    { id: 'forex_cross', label: 'Forex crosses' },
    { id: 'metals', label: 'Métaux' },
    { id: 'commodities', label: 'Commodities' },
    { id: 'indices', label: 'Indices' },
    { id: 'equity_etf', label: 'ETF' },
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

export const WORKSPACE_PRESETS = {
    gold_macro: {
        id: 'gold_macro',
        label: 'Gold macro',
        description: 'XAU, dollar, yields, silver, oil et indices US',
        marketProfile: 'xauusd',
        symbol: 'OANDA:XAUUSD',
        calendarCountries: ['US', 'EU', 'GB', 'JP'],
        quoteCards: [
            { symbol: 'OANDA:XAUUSD', label: 'XAU/USD' },
            { symbol: 'FX:EURUSD', label: 'EUR/USD' },
            { symbol: 'FX:USDJPY', label: 'USD/JPY' },
            { symbol: 'OANDA:XAGUSD', label: 'XAG/USD' },
            { symbol: 'NASDAQ:TLT', label: 'TLT' },
            { symbol: 'TVC:USOIL', label: 'WTI' },
            { symbol: 'SP:SPX', label: 'S&P 500' },
            { symbol: 'NASDAQ:QQQ', label: 'QQQ' },
        ],
    },
    forex_majors: {
        id: 'forex_majors',
        label: 'Forex majors',
        description: 'Les paires FX les plus liquides',
        marketProfile: 'eurusd',
        symbol: 'FX:EURUSD',
        calendarCountries: ['US', 'EU', 'GB', 'JP'],
        quoteCards: [
            { symbol: 'FX:EURUSD', label: 'EUR/USD' },
            { symbol: 'FX:GBPUSD', label: 'GBP/USD' },
            { symbol: 'FX:USDJPY', label: 'USD/JPY' },
            { symbol: 'FX:USDCHF', label: 'USD/CHF' },
            { symbol: 'FX:USDCAD', label: 'USD/CAD' },
            { symbol: 'FX:AUDUSD', label: 'AUD/USD' },
            { symbol: 'FX:NZDUSD', label: 'NZD/USD' },
            { symbol: 'FX:EURJPY', label: 'EUR/JPY' },
        ],
    },
    crypto_watch: {
        id: 'crypto_watch',
        label: 'Crypto watch',
        description: 'Crypto majeures et beta actifs',
        marketProfile: 'btcusd',
        symbol: 'BITSTAMP:BTCUSD',
        calendarCountries: ['US'],
        quoteCards: [
            { symbol: 'BITSTAMP:BTCUSD', label: 'BTC/USD' },
            { symbol: 'BITSTAMP:ETHUSD', label: 'ETH/USD' },
            { symbol: 'COINBASE:SOLUSD', label: 'SOL/USD' },
            { symbol: 'BITSTAMP:XRPUSD', label: 'XRP/USD' },
            { symbol: 'BINANCE:BNBUSD', label: 'BNB/USD' },
            { symbol: 'COINBASE:ADAUSD', label: 'ADA/USD' },
            { symbol: 'COINBASE:AVAXUSD', label: 'AVAX/USD' },
            { symbol: 'COINBASE:LINKUSD', label: 'LINK/USD' },
        ],
    },
    us_indices: {
        id: 'us_indices',
        label: 'Indices US',
        description: 'S&P, Nasdaq, Dow, small caps, vol et duration',
        marketProfile: 'nasdaq',
        symbol: 'NASDAQ:QQQ',
        calendarCountries: ['US'],
        quoteCards: [
            { symbol: 'SP:SPX', label: 'S&P 500' },
            { symbol: 'NASDAQ:QQQ', label: 'QQQ' },
            { symbol: 'DJ:DJI', label: 'Dow Jones' },
            { symbol: 'TVC:RUT', label: 'Russell' },
            { symbol: 'TVC:VIX', label: 'VIX' },
            { symbol: 'NASDAQ:TLT', label: 'TLT' },
            { symbol: 'AMEX:SPY', label: 'SPY' },
            { symbol: 'AMEX:IWM', label: 'IWM' },
        ],
    },
    commodities: {
        id: 'commodities',
        label: 'Commodities',
        description: 'Métaux, énergie et proxy croissance',
        marketProfile: 'usoil',
        symbol: 'TVC:USOIL',
        calendarCountries: ['US', 'CN', 'GB'],
        quoteCards: [
            { symbol: 'TVC:USOIL', label: 'WTI Oil' },
            { symbol: 'TVC:UKOIL', label: 'Brent Oil' },
            { symbol: 'TVC:NATGAS', label: 'Natural Gas' },
            { symbol: 'COMEX:HG1!', label: 'Copper' },
            { symbol: 'OANDA:XAUUSD', label: 'XAU/USD' },
            { symbol: 'OANDA:XAGUSD', label: 'XAG/USD' },
            { symbol: 'OANDA:XPTUSD', label: 'XPT/USD' },
            { symbol: 'OANDA:XPDUSD', label: 'XPD/USD' },
        ],
    },
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
