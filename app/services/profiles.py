from typing import Optional


MARKET_PROFILES = {
    "xauusd": {
        "id": "xauusd",
        "label": "XAU/USD",
        "symbol": "OANDA:XAUUSD",
        "calendar_countries": ["US"],
        "keywords": ["gold", "xau", "bullion", "fed", "fomc", "powell", "cpi", "inflation", "nfp", "yields", "dollar", "dxy", "war"],
        "tags": ["XAU", "FED", "MACRO", "GEO", "OFFICIAL"],
    },
    "xagusd": {
        "id": "xagusd",
        "label": "XAG/USD",
        "symbol": "OANDA:XAGUSD",
        "calendar_countries": ["US"],
        "keywords": ["silver", "xag", "metals", "gold", "fed", "fomc", "powell", "cpi", "inflation", "yields", "dollar", "dxy"],
        "tags": ["XAU", "FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "usdjpy": {
        "id": "usdjpy",
        "label": "USD/JPY",
        "symbol": "FX:USDJPY",
        "calendar_countries": ["US", "JP"],
        "keywords": ["yen", "jpy", "japan", "boj", "ueda", "intervention", "fed", "fomc", "powell", "yields", "treasury", "dollar"],
        "tags": ["FED", "MACRO", "OFFICIAL"],
    },
    "eurusd": {
        "id": "eurusd",
        "label": "EUR/USD",
        "symbol": "FX:EURUSD",
        "calendar_countries": ["US", "EU"],
        "keywords": ["euro", "eur", "ecb", "lagarde", "fed", "fomc", "inflation", "cpi", "pmi", "dollar"],
        "tags": ["FED", "MACRO", "OFFICIAL"],
    },
    "gbpusd": {
        "id": "gbpusd",
        "label": "GBP/USD",
        "symbol": "FX:GBPUSD",
        "calendar_countries": ["US", "GB"],
        "keywords": ["pound", "sterling", "gbp", "boe", "bailey", "uk", "britain", "fed", "inflation", "cpi", "gilts"],
        "tags": ["FED", "MACRO", "OFFICIAL"],
    },
    "usdcny": {
        "id": "usdcny",
        "label": "USD/CNY",
        "symbol": "FX:USDCNY",
        "calendar_countries": ["US", "CN"],
        "keywords": ["yuan", "cny", "china", "pboc", "dollar", "fed", "trade", "asia", "exports", "growth"],
        "tags": ["FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "usdcad": {
        "id": "usdcad",
        "label": "USD/CAD",
        "symbol": "FX:USDCAD",
        "calendar_countries": ["US", "CA"],
        "keywords": ["canada", "cad", "boc", "oil", "wti", "employment", "inflation", "fed", "dollar"],
        "tags": ["FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "audusd": {
        "id": "audusd",
        "label": "AUD/USD",
        "symbol": "FX:AUDUSD",
        "calendar_countries": ["US", "AU", "CN"],
        "keywords": ["aussie", "aud", "australia", "rba", "china", "commodities", "iron ore", "risk", "fed"],
        "tags": ["FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "usdchf": {
        "id": "usdchf",
        "label": "USD/CHF",
        "symbol": "FX:USDCHF",
        "calendar_countries": ["US", "CH"],
        "keywords": ["swiss", "chf", "snb", "franc", "safe haven", "risk", "fed", "dollar", "inflation"],
        "tags": ["FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "usdhkd": {
        "id": "usdhkd",
        "label": "USD/HKD",
        "symbol": "FX:USDHKD",
        "calendar_countries": ["US", "HK", "CN"],
        "keywords": ["hong kong", "hkd", "hkma", "peg", "liquidity", "china", "dollar", "fed", "asia"],
        "tags": ["FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "nzdusd": {
        "id": "nzdusd",
        "label": "NZD/USD",
        "symbol": "FX:NZDUSD",
        "calendar_countries": ["US", "NZ", "CN"],
        "keywords": ["kiwi", "nzd", "new zealand", "rbnz", "china", "risk", "commodities", "fed", "dollar"],
        "tags": ["FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "eurjpy": {
        "id": "eurjpy",
        "label": "EUR/JPY",
        "symbol": "FX:EURJPY",
        "calendar_countries": ["EU", "JP"],
        "keywords": ["euro", "eur", "yen", "jpy", "ecb", "boj", "lagarde", "ueda", "risk", "yields"],
        "tags": ["MACRO", "MARKETS", "OFFICIAL"],
    },
    "eurgbp": {
        "id": "eurgbp",
        "label": "EUR/GBP",
        "symbol": "FX:EURGBP",
        "calendar_countries": ["EU", "GB"],
        "keywords": ["euro", "eur", "pound", "gbp", "sterling", "ecb", "boe", "lagarde", "bailey", "uk", "europe"],
        "tags": ["MACRO", "MARKETS", "OFFICIAL"],
    },
    "gbpjpy": {
        "id": "gbpjpy",
        "label": "GBP/JPY",
        "symbol": "FX:GBPJPY",
        "calendar_countries": ["GB", "JP"],
        "keywords": ["pound", "gbp", "sterling", "yen", "jpy", "boe", "boj", "bailey", "ueda", "risk", "volatility"],
        "tags": ["MACRO", "MARKETS", "OFFICIAL"],
    },
    "nasdaq": {
        "id": "nasdaq",
        "label": "NASDAQ",
        "symbol": "NASDAQ:QQQ",
        "calendar_countries": ["US"],
        "keywords": ["nasdaq", "qqq", "tech", "ai", "semiconductor", "earnings", "fed", "yields", "rates", "risk", "nvidia"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "btcusd": {
        "id": "btcusd",
        "label": "BTC/USD",
        "symbol": "BITSTAMP:BTCUSD",
        "calendar_countries": ["US"],
        "keywords": ["bitcoin", "btc", "crypto", "etf", "sec", "fed", "liquidity", "dollar", "rates", "risk"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
}

MARKET_PROFILES.update({
    "xptusd": {
        "id": "xptusd",
        "label": "XPT/USD",
        "symbol": "OANDA:XPTUSD",
        "calendar_countries": ["US"],
        "keywords": ["platinum", "xpt", "metals", "auto", "dollar", "fed", "yields", "commodities"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "xpdusd": {
        "id": "xpdusd",
        "label": "XPD/USD",
        "symbol": "OANDA:XPDUSD",
        "calendar_countries": ["US"],
        "keywords": ["palladium", "xpd", "metals", "auto", "dollar", "fed", "yields", "commodities"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "spx": {
        "id": "spx",
        "label": "S&P 500",
        "symbol": "SP:SPX",
        "calendar_countries": ["US"],
        "keywords": ["s&p", "spx", "stocks", "earnings", "fed", "yields", "risk", "inflation"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "dow": {
        "id": "dow",
        "label": "Dow Jones",
        "symbol": "DJ:DJI",
        "calendar_countries": ["US"],
        "keywords": ["dow", "djia", "stocks", "industrials", "fed", "risk", "earnings"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "russell": {
        "id": "russell",
        "label": "Russell 2000",
        "symbol": "TVC:RUT",
        "calendar_countries": ["US"],
        "keywords": ["russell", "small caps", "iwm", "fed", "yields", "risk", "growth"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "dax": {
        "id": "dax",
        "label": "DAX 40",
        "symbol": "XETR:DAX",
        "calendar_countries": ["DE", "EU"],
        "keywords": ["dax", "germany", "europe", "ecb", "euro", "pmi", "stocks"],
        "tags": ["MACRO", "MARKETS", "OFFICIAL"],
    },
    "cac": {
        "id": "cac",
        "label": "CAC 40",
        "symbol": "EURONEXT:PX1",
        "calendar_countries": ["FR", "EU"],
        "keywords": ["cac", "france", "europe", "ecb", "euro", "stocks"],
        "tags": ["MACRO", "MARKETS", "OFFICIAL"],
    },
    "ftse": {
        "id": "ftse",
        "label": "FTSE 100",
        "symbol": "TVC:UKX",
        "calendar_countries": ["GB"],
        "keywords": ["ftse", "uk", "britain", "boe", "pound", "stocks", "commodities"],
        "tags": ["MACRO", "MARKETS", "OFFICIAL"],
    },
    "nikkei": {
        "id": "nikkei",
        "label": "Nikkei 225",
        "symbol": "TVC:NI225",
        "calendar_countries": ["JP"],
        "keywords": ["nikkei", "japan", "boj", "yen", "jpy", "asia", "stocks"],
        "tags": ["MACRO", "MARKETS", "OFFICIAL"],
    },
    "hsi": {
        "id": "hsi",
        "label": "Hang Seng",
        "symbol": "HSI:HSI",
        "calendar_countries": ["HK", "CN"],
        "keywords": ["hang seng", "hong kong", "china", "asia", "hsi", "stocks", "property"],
        "tags": ["MACRO", "MARKETS"],
    },
    "vix": {
        "id": "vix",
        "label": "VIX",
        "symbol": "TVC:VIX",
        "calendar_countries": ["US"],
        "keywords": ["vix", "volatility", "risk", "fear", "stocks", "fed", "hedging"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "usoil": {
        "id": "usoil",
        "label": "WTI Oil",
        "symbol": "TVC:USOIL",
        "calendar_countries": ["US"],
        "keywords": ["oil", "wti", "crude", "opec", "energy", "inventories", "inflation"],
        "tags": ["MACRO", "MARKETS"],
    },
    "ukoil": {
        "id": "ukoil",
        "label": "Brent Oil",
        "symbol": "TVC:UKOIL",
        "calendar_countries": ["US", "GB"],
        "keywords": ["brent", "oil", "crude", "opec", "energy", "geopolitics", "inflation"],
        "tags": ["MACRO", "MARKETS", "GEO"],
    },
    "natgas": {
        "id": "natgas",
        "label": "Natural Gas",
        "symbol": "TVC:NATGAS",
        "calendar_countries": ["US"],
        "keywords": ["natural gas", "natgas", "lng", "energy", "weather", "inventories"],
        "tags": ["MACRO", "MARKETS"],
    },
    "copper": {
        "id": "copper",
        "label": "Copper",
        "symbol": "COMEX:HG1!",
        "calendar_countries": ["US", "CN"],
        "keywords": ["copper", "china", "growth", "commodities", "industrial metals", "pmi"],
        "tags": ["MACRO", "MARKETS"],
    },
    "spy": {
        "id": "spy",
        "label": "SPY",
        "symbol": "AMEX:SPY",
        "calendar_countries": ["US"],
        "keywords": ["spy", "s&p", "stocks", "fed", "earnings", "risk"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "qqq": {
        "id": "qqq",
        "label": "QQQ",
        "symbol": "NASDAQ:QQQ",
        "calendar_countries": ["US"],
        "keywords": ["qqq", "nasdaq", "tech", "ai", "fed", "yields", "earnings"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
    "tlt": {
        "id": "tlt",
        "label": "TLT",
        "symbol": "NASDAQ:TLT",
        "calendar_countries": ["US"],
        "keywords": ["tlt", "treasury", "bonds", "yields", "fed", "rates", "duration"],
        "tags": ["FED", "MACRO", "MARKETS", "OFFICIAL"],
    },
    "iwm": {
        "id": "iwm",
        "label": "IWM",
        "symbol": "AMEX:IWM",
        "calendar_countries": ["US"],
        "keywords": ["iwm", "russell", "small caps", "risk", "fed", "growth"],
        "tags": ["FED", "MACRO", "MARKETS"],
    },
})

for crypto_id, label, symbol, name in [
    ("ethusd", "ETH/USD", "BITSTAMP:ETHUSD", "ethereum"),
    ("solusd", "SOL/USD", "COINBASE:SOLUSD", "solana"),
    ("xrpusd", "XRP/USD", "BITSTAMP:XRPUSD", "xrp"),
    ("bnbusd", "BNB/USD", "BINANCE:BNBUSD", "bnb"),
    ("adausd", "ADA/USD", "COINBASE:ADAUSD", "cardano"),
    ("dogeusd", "DOGE/USD", "COINBASE:DOGEUSD", "dogecoin"),
    ("avaxusd", "AVAX/USD", "COINBASE:AVAXUSD", "avalanche"),
    ("linkusd", "LINK/USD", "COINBASE:LINKUSD", "chainlink"),
    ("ltcusd", "LTC/USD", "COINBASE:LTCUSD", "litecoin"),
]:
    MARKET_PROFILES[crypto_id] = {
        "id": crypto_id,
        "label": label,
        "symbol": symbol,
        "calendar_countries": ["US"],
        "keywords": [name, label.split("/")[0].lower(), "crypto", "bitcoin", "btc", "etf", "sec", "fed", "liquidity", "risk"],
        "tags": ["FED", "MACRO", "MARKETS"],
    }


def get_market_profile(profile_id: Optional[str]) -> dict:
    key = (profile_id or "xauusd").strip().lower()
    return MARKET_PROFILES.get(key, MARKET_PROFILES["xauusd"])


def parse_country_filter(raw: Optional[str], fallback: list[str]) -> list[str]:
    if not raw:
        return fallback
    countries = [
        country.strip().upper()
        for country in raw.split(",")
        if country.strip()
    ]
    return countries[:8] or fallback
