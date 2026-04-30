from __future__ import annotations

from datetime import datetime, timedelta, timezone
import asyncio
import hashlib
import re
from typing import Optional

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from app.config import PARIS
from app.services.accounts import utc_now


ALERTS_CRITICAL = [
    "FED", "POWELL", "FOMC", "RATE", "TAUX", "CPI", "NFP", "INFLATION",
    "WAR", "URGENT", "BREAKING", "TRUMP", "GOLD", "XAU", "IRAN", "ISRAEL",
    "ECB", "BOJ", "BOE", "GDP", "RECESSION", "CRASH", "HACK", "ATTACK",
]

NEWS_SOURCES = {
    "INVESTING": {"url": "https://www.investing.com/rss/news.rss", "kind": "rss"},
    "REUTERS": {"url": "https://news.google.com/rss/search?q=finance+source:reuters&hl=en-US&gl=US&ceid=US:en", "kind": "rss"},
    "FOREXLIVE": {"url": "https://www.forexlive.com/feed/news", "kind": "rss"},
    "BLOOMBERG": {"url": "https://news.google.com/rss/search?q=markets+source:bloomberg&hl=en-US&gl=US&ceid=US:en", "kind": "rss"},
    "CNBC": {"url": "https://news.google.com/rss/search?q=markets+source:cnbc&hl=en-US&gl=US&ceid=US:en", "kind": "rss"},
    "FED": {"url": "https://www.federalreserve.gov/feeds/press_monetary.xml", "kind": "rss"},
    "TREASURY": {"url": "https://home.treasury.gov/news/press-releases", "kind": "html_treasury"},
    "DOL": {"url": "https://www.dol.gov/rss/releases.xml", "kind": "rss"},
}

_news_cache: dict = {"data": [], "ts": 0.0}
NEWS_CACHE_TTL = 30
NEWS_MAX_AGE_HOURS = 72
NEWS_DEDUP_WINDOW_SECONDS = 2 * 60 * 60
OFFICIAL_NEWS_SOURCES = {"FED", "TREASURY", "DOL"}


def clean_news_title(title: str) -> str:
    clean = " ".join((title or "").split())
    if " - " in clean:
        head, tail = clean.rsplit(" - ", 1)
        if tail.strip().lower() in {"reuters", "bloomberg", "cnbc", "investing.com", "forexlive"}:
            clean = head.strip()
    return clean


def news_fingerprint(title: str) -> str:
    clean = clean_news_title(title).lower()
    clean = re.sub(r"https?://\S+", " ", clean)
    clean = re.sub(r"[^a-z0-9%$]+", " ", clean)
    stopwords = {
        "the", "a", "an", "to", "of", "and", "or", "for", "in", "on", "as",
        "by", "with", "from", "at", "is", "are", "be", "will", "says", "say",
    }
    tokens = [token for token in clean.split() if len(token) > 2 and token not in stopwords]
    return " ".join(tokens[:18])


def news_similarity(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def stable_news_id(title: str) -> str:
    fingerprint = news_fingerprint(title) or clean_news_title(title).lower()
    return hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:16]


def _format_news_item(name: str, title: str, link: str, dt: datetime) -> dict:
    clean_title = clean_news_title(title)
    title_upper = clean_title.upper()
    classification = classify_news_item(name, title_upper)
    item_id = stable_news_id(clean_title)
    return {
        "id": item_id,
        "s": name,
        "t": clean_title,
        "l": link,
        "time": dt.astimezone(PARIS).strftime("%H:%M:%S"),
        "ts": dt.timestamp(),
        "crit": any(keyword in title_upper for keyword in ALERTS_CRITICAL),
        "duplicate_count": 1,
        "related_sources": [name],
        **classification,
    }


def classify_news_item(source: str, title_upper: str) -> dict:
    categories = []
    score = 0

    if any(keyword in title_upper for keyword in ("FED", "FOMC", "POWELL", "RATE", "MONETARY POLICY")):
        categories.append("FED")
        score += 5
    if any(keyword in title_upper for keyword in ("CPI", "PCE", "NFP", "PAYROLLS", "INFLATION", "UNEMPLOYMENT", "JOBLESS", "GDP", "PMI", "RETAIL SALES")):
        categories.append("MACRO")
        score += 4
    if any(keyword in title_upper for keyword in ("IRAN", "ISRAEL", "GAZA", "UKRAINE", "RUSSIA", "CHINA", "MISSILE", "ATTACK", "SANCTION", "WAR", "OIL")):
        categories.append("GEO")
        score += 4
    if any(keyword in title_upper for keyword in ("GOLD", "XAU", "BULLION", "TREASURY YIELD", "DOLLAR")):
        categories.append("XAU")
        score += 3
    if source in OFFICIAL_NEWS_SOURCES:
        categories.append("OFFICIAL")
        score += 4
    if any(keyword in title_upper for keyword in ("BREAKING", "URGENT", "EXCLUSIVE", "STATEMENT", "HOLDS RATES", "RATE DECISION", "PRESS CONFERENCE")):
        categories.append("MOVING")
        score += 3

    if not categories:
        categories.append("MARKETS")
        score += 1

    if score >= 7:
        priority = "high"
    elif score >= 4:
        priority = "medium"
    else:
        priority = "low"

    return {
        "priority": priority,
        "tags": list(dict.fromkeys(categories)),
        "news_score": score,
        "market_moving": priority == "high" or "MOVING" in categories or source in OFFICIAL_NEWS_SOURCES,
    }


def news_item_rank(item: dict) -> tuple[int, float]:
    source_rank = {
        "FED": 7,
        "DOL": 6,
        "TREASURY": 6,
        "REUTERS": 5,
        "BLOOMBERG": 5,
        "FOREXLIVE": 4,
        "CNBC": 3,
        "INVESTING": 2,
    }.get(str(item.get("s") or ""), 1)
    return int(item.get("news_score") or 0) + source_rank, float(item.get("ts") or 0)


def dedupe_news_items(items: list[dict]) -> list[dict]:
    clusters: list[dict] = []

    for item in sorted(items, key=lambda row: row.get("ts", 0), reverse=True):
        fingerprint = news_fingerprint(item.get("t") or "")
        matched = None
        for cluster in clusters:
            if abs(float(cluster["best"].get("ts", 0)) - float(item.get("ts", 0))) > NEWS_DEDUP_WINDOW_SECONDS:
                continue
            if fingerprint and fingerprint == cluster["fingerprint"]:
                matched = cluster
                break
            if fingerprint and news_similarity(fingerprint, cluster["fingerprint"]) >= 0.82:
                matched = cluster
                break

        if matched is None:
            clusters.append({"fingerprint": fingerprint, "items": [item], "best": item})
            continue

        matched["items"].append(item)
        if news_item_rank(item) > news_item_rank(matched["best"]):
            matched["best"] = item

    deduped = []
    for cluster in clusters:
        best = dict(cluster["best"])
        sources = list(dict.fromkeys(str(item.get("s") or "") for item in cluster["items"] if item.get("s")))
        tags = []
        for item in cluster["items"]:
            tags.extend(item.get("tags") or [])
        best["id"] = stable_news_id(best.get("t") or "")
        best["duplicate_count"] = len(cluster["items"])
        best["related_sources"] = sources
        best["tags"] = list(dict.fromkeys(tags))
        best["crit"] = any(item.get("crit") for item in cluster["items"])
        best["market_moving"] = any(item.get("market_moving") for item in cluster["items"])
        best["news_score"] = max(int(item.get("news_score") or 0) for item in cluster["items"])
        if any(item.get("priority") == "high" for item in cluster["items"]):
            best["priority"] = "high"
        elif any(item.get("priority") == "medium" for item in cluster["items"]):
            best["priority"] = "medium"
        else:
            best["priority"] = "low"
        deduped.append(best)

    deduped.sort(key=lambda item: (float(item.get("ts") or 0), int(item.get("news_score") or 0)), reverse=True)
    return deduped


def score_news_for_profile(item: dict, profile: dict) -> int:
    title = str(item.get("t", "")).lower()
    tags = set(item.get("tags") or [])
    score = 0

    for keyword in profile.get("keywords", []):
        if keyword.lower() in title:
            score += 3

    for tag in profile.get("tags", []):
        if tag in tags:
            score += 2

    if item.get("priority") == "high":
        score += 1
    if item.get("crit"):
        score += 1

    return score


def personalize_news_items(items: list[dict], profile: dict) -> list[dict]:
    cutoff_ts = (utc_now() - timedelta(hours=NEWS_MAX_AGE_HOURS)).timestamp()
    recent_items = [item for item in items if float(item.get("ts", 0)) >= cutoff_ts]
    personalized = []

    relevant_items = []
    fallback_items = []
    for item in recent_items:
        score = score_news_for_profile(item, profile)
        next_item = {**item, "profile_score": score}
        if score > 0:
            next_item["priority"] = "high" if score >= 7 else "medium" if score >= 3 else next_item.get("priority", "low")
            next_item["market_moving"] = next_item.get("market_moving") or score >= 7
            relevant_items.append(next_item)
        elif item.get("priority") == "high" or item.get("crit"):
            fallback_items.append(next_item)

    if relevant_items:
        personalized = relevant_items + fallback_items
    else:
        personalized = [{**item, "profile_score": 0} for item in recent_items]

    personalized.sort(key=lambda item: item.get("ts", 0), reverse=True)
    return personalized[:80]


def _parse_rss_items(name: str, text: str) -> list[dict]:
    try:
        feed = feedparser.parse(text)
    except Exception:
        return []

    items: list[dict] = []
    for entry in feed.entries[:8]:
        published = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if not published:
            continue

        try:
            dt = datetime(*published[:6], tzinfo=timezone.utc)
        except Exception:
            continue

        title = getattr(entry, "title", "") or ""
        link = getattr(entry, "link", "") or ""
        if not title or not link:
            continue

        items.append(_format_news_item(name, title, link, dt))

    return items


def _parse_treasury_items(name: str, text: str) -> list[dict]:
    soup = BeautifulSoup(text, "html.parser")
    items: list[dict] = []

    for headline in soup.select("h3.featured-stories__headline")[:8]:
        link_el = headline.find("a", href=True)
        if not link_el:
            continue

        time_el = headline.find_previous("time", class_="datetime")
        if not time_el:
            continue

        raw_dt = time_el.get("datetime", "")
        try:
            dt = datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))
        except ValueError:
            continue

        title = link_el.get_text(" ", strip=True)
        href = link_el["href"]
        link = href if href.startswith("http") else f"https://home.treasury.gov{href}"

        if not title or not link:
            continue

        items.append(_format_news_item(name, title, link, dt))

    return items


async def _fetch_source(session: aiohttp.ClientSession, name: str, config: dict | str) -> list[dict]:
    if isinstance(config, str):
        url = config
        kind = "rss"
    else:
        url = config.get("url", "")
        kind = config.get("kind", "rss")

    if not url:
        return []

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
    except Exception:
        return []

    if kind == "html_treasury":
        return await asyncio.to_thread(_parse_treasury_items, name, text)

    return await asyncio.to_thread(_parse_rss_items, name, text)
