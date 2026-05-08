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
