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
