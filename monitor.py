#!/usr/bin/env python3
"""
Nieruchomości Monitor — znajdowanie okazji poniżej ceny rynkowej.
Rynki: Kraków, Warszawa, Wrocław, Gdańsk, Valencia, Ateny, Bukareszt.
Źródła: Otodom, OLX, Idealista (ograniczone).
"""

import json
import os
import re
import sys
import time
import random
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, quote_plus

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DEALS_JSON = BASE_DIR / "deals.json"
HISTORY_JSON = BASE_DIR / "history.json"
DEALS_HTML = BASE_DIR / "deals.html"
LOG_FILE = BASE_DIR / "deals.log"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
_handlers = [logging.StreamHandler(sys.stdout)]
try:
    _handlers.append(logging.FileHandler(LOG_FILE, encoding="utf-8"))
except Exception:
    pass  # log file not writable (e.g. read-only filesystem) — stdout only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_handlers,
)
log = logging.getLogger("monitor")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CFG = load_config()

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})


def polite_delay():
    """Losowe opóźnienie między requestami — nie obciążamy serwerów."""
    d = random.uniform(CFG.get("request_delay_min", 2), CFG.get("request_delay_max", 5))
    time.sleep(d)


def safe_get(url: str, timeout: int = 30) -> Optional[requests.Response]:
    """GET z obsługą błędów i retries."""
    for attempt in range(3):
        try:
            resp = SESSION.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 403:
                log.warning(f"403 Forbidden: {url} — serwer blokuje scraping")
                return None
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                log.warning(f"429 Rate limited: {url} — czekam {wait}s")
                time.sleep(wait)
                continue
            log.warning(f"HTTP {resp.status_code}: {url}")
            return None
        except requests.RequestException as e:
            log.error(f"Request error ({attempt+1}/3): {url} — {e}")
            if attempt < 2:
                time.sleep(5)
    return None


# ---------------------------------------------------------------------------
# Deal model
# ---------------------------------------------------------------------------
def make_deal(
    title: str,
    price: float,
    area: float,
    price_m2: float,
    location: str,
    url: str,
    source: str,
    market: str,
    image_url: str = "",
    description: str = "",
) -> dict:
    deal_id = hashlib.md5(url.encode()).hexdigest()[:12]
    return {
        "id": deal_id,
        "title": title,
        "price": price,
        "area": area,
        "price_m2": price_m2,
        "location": location,
        "url": url,
        "source": source,
        "market": market,
        "image_url": image_url,
        "description": description,
        "found_at": datetime.now().isoformat(),
        "okazja_score": 0,
        "okazja_reasons": [],
    }


def city_matches(city_name: str, market_key: str) -> bool:
    """Return True if the listing's city matches the expected market city."""
    allowed = CFG["markets"].get(market_key, {}).get("city_filter", [])
    if not allowed:
        return True  # no filter = accept all
    city_lower = city_name.lower()
    return any(a.lower() in city_lower or city_lower in a.lower() for a in allowed)


# ---------------------------------------------------------------------------
# Score deals
# ---------------------------------------------------------------------------
def score_deal(deal: dict, market_cfg: dict) -> dict:
    """Ocena okazji: im wyższy score tym lepszy deal."""
    score = 0
    reasons = []
    max_price = market_cfg["max_price_m2"]

    if deal["price_m2"] > 0 and max_price > 0:
        discount_pct = (1 - deal["price_m2"] / max_price) * 100
        deal["discount_pct"] = round(discount_pct, 1)

        if discount_pct >= CFG.get("alert_discount_pct", 30):
            score += 50
            reasons.append(f"MEGA OKAZJA: {discount_pct:.0f}% poniżej rynku")
        elif discount_pct >= CFG.get("min_discount_pct", 20):
            score += 30
            reasons.append(f"Dobra okazja: {discount_pct:.0f}% poniżej rynku")
        elif discount_pct >= 10:
            score += 10
            reasons.append(f"Poniżej rynku: {discount_pct:.0f}%")
    else:
        deal["discount_pct"] = 0

    # Keyword matching
    text = (deal.get("title", "") + " " + deal.get("description", "")).lower()
    all_keywords = (
        CFG.get("keywords_pl", [])
        + CFG.get("keywords_en", [])
        + CFG.get("keywords_es", [])
        + CFG.get("keywords_pt", [])
    )
    matched_kw = [kw for kw in all_keywords if kw in text]
    if matched_kw:
        score += 5 * len(matched_kw)
        reasons.append(f"Słowa kluczowe: {', '.join(matched_kw[:5])}")

    deal["okazja_score"] = score
    deal["okazja_reasons"] = reasons
    return deal


def generate_justification(deal: dict, market_cfg: dict) -> str:
    """Generate human-readable justification for why this is a good deal."""
    parts = []
    discount = deal.get("discount_pct", 0)
    price_m2 = deal.get("price_m2", 0)
    area = deal.get("area", 0)
    price = deal.get("price", 0)
    currency = market_cfg.get("currency", "PLN")
    reasons = deal.get("okazja_reasons", [])

    if discount >= 25:
        parts.append(f"Cena {discount:.0f}% poniżej maksimum rynkowego dla tej lokalizacji — to znaczące odchylenie sugerujące presję sprzedażową lub ukryty potencjał.")
    elif discount >= 15:
        parts.append(f"Cena {discount:.0f}% poniżej typowych stawek rynkowych — solidny margines na negocjacje lub natychmiastowy zysk na odsprzedaży.")

    if area > 0 and price_m2 > 0:
        if currency == "PLN" and price_m2 < 7000:
            parts.append(f"Stawka {price_m2:,.0f} PLN/m² należy do najtańszych w segmencie.")
        elif currency == "EUR" and price_m2 < 1500:
            parts.append(f"Stawka {price_m2:,.0f} EUR/m² to poziom pre-boomowy — rzadko spotykany.")

    if area >= 70:
        parts.append(f"Duży metraż ({area:.0f} m²) daje elastyczność: można podzielić na 2 lokale lub wynająć pokojami.")

    kw_text = (deal.get("title", "") + " " + deal.get("description", "")).lower()
    if "komornik" in kw_text or "egzekucja" in kw_text or "licytacja" in kw_text:
        parts.append("Sprzedaż egzekucyjna/komornicza — ceny typowo 20-40% poniżej rynku, ale wymaga due diligence prawnego.")
    elif "pilne" in kw_text or "szybka sprzedaż" in kw_text or "urgent" in kw_text:
        parts.append("Pilna sprzedaż — właściciel pod presją czasową, znaczny margines negocjacyjny.")
    elif "przetarg" in kw_text or "auction" in kw_text or "subasta" in kw_text:
        parts.append("Oferta przetargowa — często 15-30% poniżej wartości rynkowej przy braku konkurencji.")
    elif "bezpośrednio" in kw_text or "właściciel" in kw_text or "particular" in kw_text:
        parts.append("Sprzedaż bezpośrednia od właściciela — brak prowizji agenta (~3%), możliwość agresywnych negocjacji.")

    if not parts:
        if discount > 0:
            parts.append(f"Cena {discount:.0f}% poniżej maksimum rynkowego — warto sprawdzić stan techniczny i negocjować.")
        else:
            parts.append("Oferta w przedziale cenowym — porównaj ze średnimi w dzielnicy przed decyzją.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Otodom scraper
# ---------------------------------------------------------------------------
OTODOM_SEARCH_URLS = {
    "krakow_centrum": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow/krakow/krakow?distanceRadius=0&locations=%5Bcity%5D%5B6%5D%5B25%5D&viewType=listing",
    "krakow_inne": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow?viewType=listing",
    "warszawa_centrum": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?distanceRadius=0&viewType=listing",
    "warszawa_inne": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/mazowieckie/warszawa?viewType=listing",
    "warszawa_inwestycyjne": "https://www.otodom.pl/pl/wyniki/sprzedaz/lokal/mazowieckie/warszawa?viewType=listing",
    "krakow_inwestycyjne": "https://www.otodom.pl/pl/wyniki/sprzedaz/lokal/malopolskie/krakow?viewType=listing",
    "wroclaw_centrum": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/dolnoslaskie/wroclaw/wroclaw/wroclaw?viewType=listing",
    "gdansk_centrum": "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/pomorskie/gdansk/gdansk/gdansk?viewType=listing",
    "krakow_dzialki": "https://www.otodom.pl/pl/wyniki/sprzedaz/dzialka/malopolskie/krakow?viewType=listing",
    "warszawa_dzialki": "https://www.otodom.pl/pl/wyniki/sprzedaz/dzialka/mazowieckie/warszawa?viewType=listing",
    "pl_kamienice": "https://www.otodom.pl/pl/wyniki/sprzedaz/inne/cala-polska?viewType=listing",
}


def scrape_otodom(market_key: str) -> list[dict]:
    """Scrape Otodom listings. Otodom renders via JS, so we parse the __NEXT_DATA__ JSON."""
    base_url = OTODOM_SEARCH_URLS.get(market_key)
    if not base_url:
        return []

    deals = []
    max_pages = CFG.get("max_pages", 3)

    for page in range(1, max_pages + 1):
        url = f"{base_url}&page={page}" if page > 1 else base_url
        log.info(f"[Otodom] {market_key} strona {page}: {url}")

        resp = safe_get(url)
        if not resp:
            break

        try:
            soup = BeautifulSoup(resp.text, "html.parser")

            # Otodom uses Next.js — data is in __NEXT_DATA__ script tag
            next_data_tag = soup.find("script", {"id": "__NEXT_DATA__"})
            if next_data_tag:
                data = json.loads(next_data_tag.string)
                listings = _extract_otodom_next_data(data, market_key)
                deals.extend(listings)
                log.info(f"  -> znaleziono {len(listings)} ofert (Next.js JSON)")
            else:
                # Fallback: parse HTML directly
                listings = _extract_otodom_html(soup, market_key)
                deals.extend(listings)
                log.info(f"  -> znaleziono {len(listings)} ofert (HTML fallback)")

        except Exception as e:
            log.error(f"[Otodom] Błąd parsowania {market_key} strona {page}: {e}")

        polite_delay()

    return deals


def _extract_otodom_next_data(data: dict, market_key: str) -> list[dict]:
    """Extract listings from Otodom __NEXT_DATA__ JSON."""
    deals = []
    try:
        # Navigate the Next.js data structure
        props = data.get("props", {}).get("pageProps", {})

        # Try different paths where listings might be
        search_data = props.get("data", {}).get("searchAds", {})
        items = search_data.get("items", [])

        if not items:
            # Alternative path
            items = props.get("data", {}).get("searchAds", {}).get("items", [])

        for item in items:
            try:
                title = item.get("title", "")
                price_obj = item.get("totalPrice", {}) or {}
                price = price_obj.get("value", 0)
                if not price:
                    # Try alternative field
                    price = item.get("totalPrice", 0)
                    if isinstance(price, dict):
                        price = 0

                area = item.get("areaInSquareMeters", 0)
                if not area:
                    area = 0

                price_m2 = price / area if area > 0 else 0

                location_obj = item.get("location", {}) or {}
                address = location_obj.get("address", {}) or {}
                city = address.get("city", {}) or {}
                city_name = city.get("name", "") if isinstance(city, dict) else str(city)

                # City filter — skip listings from wrong city
                if not city_matches(city_name, market_key):
                    log.debug(f"  Pomijam ofertę z {city_name!r} (oczekiwano: {CFG['markets'].get(market_key,{}).get('city_filter',[])})")
                    continue

                district = address.get("district", {}) or {}
                district_name = district.get("name", "") if isinstance(district, dict) else str(district)
                location = f"{district_name}, {city_name}".strip(", ")

                slug = item.get("slug", "")
                item_id = item.get("id", "")
                listing_url = f"https://www.otodom.pl/pl/oferta/{slug}" if slug else ""

                images = item.get("images", []) or []
                image_url = ""
                if images:
                    if isinstance(images[0], dict):
                        image_url = images[0].get("medium", "") or images[0].get("small", "")
                    elif isinstance(images[0], str):
                        image_url = images[0]

                deal = make_deal(
                    title=title,
                    price=float(price) if price else 0,
                    area=float(area) if area else 0,
                    price_m2=round(float(price_m2), 0) if price_m2 else 0,
                    location=location,
                    url=listing_url,
                    source="otodom",
                    market=market_key,
                    image_url=image_url,
                )
                if deal["price"] > 0 and deal["area"] > 0:
                    deals.append(deal)
            except Exception as e:
                log.debug(f"  Pomijam ofertę: {e}")
                continue

    except Exception as e:
        log.error(f"Błąd ekstrakcji Otodom Next.js data: {e}")

    return deals


def _extract_otodom_html(soup: BeautifulSoup, market_key: str) -> list[dict]:
    """Fallback HTML parser for Otodom."""
    deals = []

    # Try various selectors that Otodom has used
    listing_selectors = [
        'article[data-cy="listing-item"]',
        'li[data-cy="listing-item"]',
        'a[data-cy="listing-item-link"]',
        'div[data-testid="listing-card"]',
        'article',
    ]

    articles = []
    for sel in listing_selectors:
        articles = soup.select(sel)
        if articles:
            break

    for art in articles[:30]:  # Limit per page
        try:
            # Title
            title_el = art.select_one("h3, h2, [data-cy='listing-item-title']")
            title = title_el.get_text(strip=True) if title_el else ""

            # Price
            price_el = art.select_one("[data-cy='listing-item-price'], span[class*='price']")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price = _parse_price(price_text)

            # Area
            area = 0
            spans = art.select("span, dd")
            for sp in spans:
                txt = sp.get_text(strip=True)
                m = re.search(r'(\d+[,.]?\d*)\s*m[²2]', txt)
                if m:
                    area = float(m.group(1).replace(",", "."))
                    break

            # URL
            link = art.select_one("a[href*='/oferta/']") or art.find("a", href=True)
            href = link["href"] if link else ""
            if href and not href.startswith("http"):
                href = f"https://www.otodom.pl{href}"

            # Location
            loc_el = art.select_one("[data-testid='advert-card-address'], p[class*='location']")
            location = loc_el.get_text(strip=True) if loc_el else ""

            # Image
            img = art.select_one("img[src*='http']")
            image_url = img["src"] if img else ""

            price_m2 = price / area if area > 0 else 0

            deal = make_deal(
                title=title or "Bez tytułu",
                price=price,
                area=area,
                price_m2=round(price_m2, 0),
                location=location,
                url=href,
                source="otodom",
                market=market_key,
                image_url=image_url,
            )
            if deal["price"] > 0 and deal["area"] > 0:
                deals.append(deal)

        except Exception as e:
            log.debug(f"  Pomijam element HTML: {e}")
            continue

    return deals


# ---------------------------------------------------------------------------
# OLX scraper
# ---------------------------------------------------------------------------
OLX_SEARCH_URLS = {
    "krakow_centrum": "https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/krakow/?search%5Bdistrict_id%5D=38",
    "krakow_inne": "https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/krakow/",
    "warszawa_centrum": "https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/warszawa/?search%5Bdistrict_id%5D=301",
    "warszawa_inne": "https://www.olx.pl/nieruchomosci/mieszkania/sprzedaz/warszawa/",
}


def scrape_olx(market_key: str) -> list[dict]:
    """Scrape OLX nieruchomości. OLX also uses server-rendered HTML + JSON."""
    base_url = OLX_SEARCH_URLS.get(market_key)
    if not base_url:
        return []

    deals = []
    max_pages = CFG.get("max_pages", 3)

    for page in range(1, max_pages + 1):
        url = f"{base_url}&page={page}" if "?" in base_url else f"{base_url}?page={page}"
        log.info(f"[OLX] {market_key} strona {page}: {url}")

        resp = safe_get(url)
        if not resp:
            break

        try:
            soup = BeautifulSoup(resp.text, "html.parser")

            # OLX stores data in script tags too
            script_tag = soup.find("script", {"id": "olx-init-config"})
            if script_tag:
                listings = _extract_olx_json(script_tag.string, market_key)
                deals.extend(listings)
                log.info(f"  -> znaleziono {len(listings)} ofert (JSON)")
            else:
                # Try __NEXT_DATA__ (newer OLX uses Next.js)
                next_tag = soup.find("script", {"id": "__NEXT_DATA__"})
                if next_tag:
                    data = json.loads(next_tag.string)
                    listings = _extract_olx_next_data(data, market_key)
                    deals.extend(listings)
                    log.info(f"  -> znaleziono {len(listings)} ofert (Next.js)")
                else:
                    # HTML fallback
                    listings = _extract_olx_html(soup, market_key)
                    deals.extend(listings)
                    log.info(f"  -> znaleziono {len(listings)} ofert (HTML fallback)")

        except Exception as e:
            log.error(f"[OLX] Błąd parsowania {market_key} strona {page}: {e}")

        polite_delay()

    return deals


def _extract_olx_next_data(data: dict, market_key: str) -> list[dict]:
    """Parse OLX Next.js data."""
    deals = []
    try:
        props = data.get("props", {}).get("pageProps", {})

        # Try known paths
        ads = props.get("ads", [])
        if not ads:
            listing_data = props.get("listingData", {})
            ads = listing_data.get("ads", [])

        for ad in ads:
            try:
                title = ad.get("title", "")
                url = ad.get("url", "")

                # Price
                price = 0
                params = ad.get("params", [])
                if isinstance(params, list):
                    for p in params:
                        if p.get("key") == "price":
                            val = p.get("value", {})
                            price = float(val.get("value", 0)) if isinstance(val, dict) else float(val or 0)
                        if p.get("key") == "m":
                            val = p.get("value", {})
                            area_str = val.get("key", "0") if isinstance(val, dict) else str(val or "0")

                # Try price from other fields
                if not price:
                    price_obj = ad.get("price", {})
                    if isinstance(price_obj, dict):
                        price_str = price_obj.get("regularPrice", {}).get("value", "0")
                        price = _parse_price(str(price_str))

                area = 0
                if isinstance(params, list):
                    for p in params:
                        key = p.get("key", "")
                        if key in ("m", "area", "size"):
                            val = p.get("value", {})
                            if isinstance(val, dict):
                                area = float(val.get("key", "0").replace(",", "."))
                            else:
                                area = float(str(val).replace(",", ".").replace(" ", ""))

                location = ad.get("location", {}).get("cityName", "")
                district = ad.get("location", {}).get("districtName", "")
                if not city_matches(location, market_key):
                    continue
                if district:
                    location = f"{district}, {location}"

                photos = ad.get("photos", [])
                image_url = photos[0] if photos else ""
                if isinstance(image_url, dict):
                    image_url = image_url.get("link", "")

                price_m2 = price / area if area > 0 else 0

                deal = make_deal(
                    title=title,
                    price=price,
                    area=area,
                    price_m2=round(price_m2, 0),
                    location=location,
                    url=url,
                    source="olx",
                    market=market_key,
                    image_url=image_url,
                )
                if deal["price"] > 0 and deal["area"] > 0:
                    deals.append(deal)
            except Exception as e:
                log.debug(f"  OLX Next.js pomijam: {e}")

    except Exception as e:
        log.error(f"OLX Next.js extraction error: {e}")

    return deals


def _extract_olx_json(script_content: str, market_key: str) -> list[dict]:
    """Parse OLX olx-init-config — contains __PRERENDERED_STATE__ with double-encoded JSON."""
    deals = []
    try:
        # Extract __PRERENDERED_STATE__ variable (double-encoded JSON string)
        m = re.search(
            r'window\.__PRERENDERED_STATE__\s*=\s*"(.+?)";',
            script_content,
            re.DOTALL,
        )
        if not m:
            log.debug("OLX: nie znaleziono __PRERENDERED_STATE__")
            return deals

        encoded = m.group(1)
        decoded = encoded.encode().decode("unicode_escape")
        data = json.loads(decoded)

        ads = data.get("listing", {}).get("listing", {}).get("ads", [])
        for ad in ads:
            try:
                title = ad.get("title", "")
                url = ad.get("url", "")

                # Price from price object
                price = 0
                price_obj = ad.get("price", {})
                if isinstance(price_obj, dict):
                    reg = price_obj.get("regularPrice", {})
                    if isinstance(reg, dict):
                        price = float(reg.get("value", 0))

                # Area and price_per_m from params list
                area = 0
                price_m2 = 0
                for param in ad.get("params", []):
                    key = param.get("key", "")
                    if key == "m":
                        nv = param.get("normalizedValue", "0")
                        area = float(str(nv).replace(",", "."))
                    elif key == "price_per_m":
                        nv = param.get("normalizedValue", "0")
                        price_m2 = float(str(nv).replace(",", "."))

                if price_m2 == 0 and area > 0 and price > 0:
                    price_m2 = price / area

                # Location
                loc = ad.get("location", {})
                district = loc.get("districtName", "")
                city = loc.get("cityName", "")
                location = f"{district}, {city}".strip(", ")

                # Photos
                photos = ad.get("photos", [])
                image_url = photos[0] if photos else ""

                deal = make_deal(
                    title=title,
                    price=price,
                    area=area,
                    price_m2=round(price_m2, 0),
                    location=location,
                    url=url,
                    source="olx",
                    market=market_key,
                    image_url=image_url,
                )
                if deal["price"] > 0 and deal["area"] > 0:
                    deals.append(deal)
            except Exception as e:
                log.debug(f"OLX pomijam oferte: {e}")
                continue

    except Exception as e:
        log.debug(f"OLX JSON parse error: {e}")
    return deals


def _extract_olx_html(soup: BeautifulSoup, market_key: str) -> list[dict]:
    """Fallback HTML parser for OLX."""
    deals = []
    cards = soup.select("div[data-cy='l-card'], div.listing-grid-container div.css-1sw7q4x")

    for card in cards[:30]:
        try:
            link = card.select_one("a[href]")
            href = link["href"] if link else ""
            if href and not href.startswith("http"):
                href = f"https://www.olx.pl{href}"

            title_el = card.select_one("h6, h4, a")
            title = title_el.get_text(strip=True) if title_el else ""

            price_el = card.select_one("p[data-testid='ad-price']")
            price = _parse_price(price_el.get_text(strip=True)) if price_el else 0

            # Area from params
            area = 0
            param_spans = card.select("span")
            for sp in param_spans:
                txt = sp.get_text(strip=True)
                m = re.search(r'(\d+[,.]?\d*)\s*m[²2]', txt)
                if m:
                    area = float(m.group(1).replace(",", "."))
                    break

            location = ""
            loc_el = card.select_one("p[data-testid='location-date']")
            if loc_el:
                location = loc_el.get_text(strip=True).split(" - ")[0]

            img = card.select_one("img[src*='http']")
            image_url = img["src"] if img else ""

            price_m2 = price / area if area > 0 else 0
            deal = make_deal(
                title=title or "Bez tytułu",
                price=price, area=area, price_m2=round(price_m2, 0),
                location=location, url=href, source="olx", market=market_key,
                image_url=image_url,
            )
            if deal["price"] > 0 and deal["area"] > 0:
                deals.append(deal)
        except Exception:
            continue

    return deals


# ---------------------------------------------------------------------------
# Idealista scraper (limited — they block heavily)
# ---------------------------------------------------------------------------
IDEALISTA_URLS = {
    "barcelona": "https://www.idealista.com/venta-viviendas/barcelona-barcelona/",
    "lizbona": "https://www.idealista.pt/comprar-casas/lisboa/",
    # Spain
    "alicante": "https://www.idealista.com/venta-viviendas/alicante-alicante/",
    "malaga":   "https://www.idealista.com/venta-viviendas/malaga-malaga/",
    "valencia": "https://www.idealista.com/venta-viviendas/valencia-valencia/",
}


def scrape_idealista(market_key: str) -> list[dict]:
    """
    Idealista agresywnie blokuje scrapery (Captcha, fingerprinting).
    Próbujemy pobrać co się da, ale oczekujemy 403/captcha.
    """
    base_url = IDEALISTA_URLS.get(market_key)
    if not base_url:
        return []

    deals = []
    log.info(f"[Idealista] {market_key}: {base_url}")
    log.info("  [!] Idealista blokuje scrapery — wyniki mogą być puste")

    # Use a more browser-like session
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        resp = SESSION.get(base_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            log.warning(f"  Idealista zwróciła {resp.status_code} — prawdopodobnie captcha/blokada")
            return deals

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select("article.item, div.item-info-container")

        for art in articles[:20]:
            try:
                title_el = art.select_one("a.item-link")
                title = title_el.get_text(strip=True) if title_el else ""
                href = title_el["href"] if title_el else ""
                if href and not href.startswith("http"):
                    domain = "https://www.idealista.com" if "barcelona" in market_key else "https://www.idealista.pt"
                    href = f"{domain}{href}"

                price_el = art.select_one("span.item-price")
                price = _parse_price(price_el.get_text(strip=True)) if price_el else 0

                detail_els = art.select("span.item-detail")
                area = 0
                for de in detail_els:
                    txt = de.get_text(strip=True)
                    m = re.search(r'(\d+)\s*m[²2]', txt)
                    if m:
                        area = float(m.group(1))
                        break

                img = art.select_one("img[src*='http']")
                image_url = img.get("src", "") if img else ""

                price_m2 = price / area if area > 0 else 0
                deal = make_deal(
                    title=title, price=price, area=area, price_m2=round(price_m2, 0),
                    location=market_key.replace("_", " ").title(),
                    url=href, source="idealista", market=market_key,
                    image_url=image_url,
                )
                if deal["price"] > 0 and deal["area"] > 0:
                    deals.append(deal)
            except Exception:
                continue

        log.info(f"  -> znaleziono {len(deals)} ofert")

    except Exception as e:
        log.error(f"[Idealista] Błąd: {e}")

    return deals


# ---------------------------------------------------------------------------
# storia.ro scraper (Bucharest) — uses __NEXT_DATA__ like Otodom
# ---------------------------------------------------------------------------
STORIA_URLS = {
    "bucharest": "https://www.storia.ro/ro/rezultate/vanzare/apartament/bucuresti",
}

def scrape_storia(market_key: str) -> list[dict]:
    """Scrape storia.ro via __NEXT_DATA__ JSON (same structure as Otodom/Next.js)."""
    base_url = STORIA_URLS.get(market_key)
    if not base_url:
        return []
    deals = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    for page in range(1, 3):
        url = f"{base_url}?page={page}" if page > 1 else base_url
        log.info(f"[Storia] {market_key} page {page}: {url}")
        resp = SESSION.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            log.warning(f"  Storia HTTP {resp.status_code}")
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not tag:
            log.warning("  Storia: brak __NEXT_DATA__")
            break
        try:
            data = json.loads(tag.string)
            items = data.get("props", {}).get("pageProps", {}).get("data", {}).get("searchAds", {}).get("items", [])
            log.info(f"  Storia items: {len(items)}")
            for item in items:
                try:
                    price_obj = item.get("totalPrice") or {}
                    price = float(price_obj.get("value", 0) or 0)
                    area = float(item.get("areaInSquareMeters") or 0)
                    if price <= 0:
                        continue
                    slug = item.get("slug", "")
                    url_deal = f"https://www.storia.ro/ro/oferta/{slug}" if slug else ""
                    title = item.get("title") or item.get("estate") or "Apartament București"
                    city_obj = (item.get("location") or {}).get("address", {}).get("city", {})
                    city = city_obj.get("name", "București") if isinstance(city_obj, dict) else "București"
                    price_m2 = round(price / area, 0) if area > 0 else 0
                    img_list = item.get("images") or []
                    image_url = img_list[0].get("medium") if img_list and isinstance(img_list[0], dict) else ""
                    deal = make_deal(
                        title=title, price=price, area=area, price_m2=price_m2,
                        location=city, url=url_deal, source="storia",
                        market=market_key, image_url=image_url or "",
                    )
                    deals.append(deal)
                except Exception:
                    continue
        except Exception as e:
            log.error(f"  Storia parse error: {e}")
        polite_delay()
    log.info(f"[Storia] -> {len(deals)} ofert")
    return deals


# ---------------------------------------------------------------------------
# imot.bg scraper (Sofia/Bulgaria)
# ---------------------------------------------------------------------------
IMOT_URLS = {
    "sofia": "https://www.imot.bg/pcgi/imot.cgi?act=11&slink=bycghp&f1=1&f2=Sofia",
}

def scrape_imot(market_key: str) -> list[dict]:
    """Scrape imot.bg for Bulgarian market. Uses windows-1251 encoding."""
    base_url = IMOT_URLS.get(market_key)
    if not base_url:
        return []
    deals = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "bg-BG,bg;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    log.info(f"[Imot.bg] {market_key}: {base_url}")
    try:
        resp = SESSION.get(base_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            log.warning(f"  Imot HTTP {resp.status_code}")
            return deals
        html = resp.content.decode("windows-1251", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.item")
        if not cards:
            cards = soup.select("table.tableListResult tr[class]")
        log.info(f"  Imot cards: {len(cards)}")
        for card in cards[:25]:
            try:
                link_el = card.select_one("div.zaglavie a, a.lnk1, h3 a, td a")
                if not link_el:
                    continue
                title = link_el.get_text(strip=True)
                href = link_el.get("href", "")
                if href.startswith("//"):
                    href = "https:" + href
                elif href and not href.startswith("http"):
                    href = "https://www.imot.bg" + href
                price_el = card.select_one("div.price, .cena, strong")
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = _parse_price(price_text)
                area = 0
                for el in card.select("span, div, td"):
                    m = re.search(r'(\d+)\s*(?:кв\.м|m²|кв\.м\.)', el.get_text())
                    if m:
                        area = float(m.group(1))
                        break
                if price <= 0:
                    continue
                price_m2 = round(price / area, 0) if area > 0 else 0
                deal = make_deal(
                    title=title or "Апартамент София",
                    price=price, area=area, price_m2=price_m2,
                    location="Sofia", url=href,
                    source="imot", market=market_key,
                )
                deals.append(deal)
            except Exception:
                continue
    except Exception as e:
        log.error(f"[Imot.bg] Błąd: {e}")
    log.info(f"[Imot.bg] -> {len(deals)} ofert")
    return deals


# ---------------------------------------------------------------------------
# xe.gr / imobiliare stubs — blocked, kept for compatibility
# ---------------------------------------------------------------------------
def scrape_imobiliare(market_key):
    log.info(f"[Imobiliare] Using storia.ro instead for {market_key}")
    return scrape_storia(market_key)

def scrape_xe_gr(market_key):
    log.warning(f"[xe.gr] Zablokowane przez AWS WAF — pomijam {market_key}")
    return []


# ---------------------------------------------------------------------------
# Price parser
# ---------------------------------------------------------------------------
def _parse_price(text: str) -> float:
    """Parse price from text like '450 000 zł', '250.000 €', etc."""
    if not text:
        return 0
    # Remove currency symbols and whitespace
    cleaned = re.sub(r'[^\d,.]', ' ', text).strip()
    # Handle European number format (1.234.567 or 1 234 567)
    parts = cleaned.split()
    if len(parts) > 1:
        # Join parts — likely thousands separator is space
        cleaned = "".join(parts)
    # Handle dots as thousands sep (e.g. 250.000)
    if cleaned.count(".") > 1:
        cleaned = cleaned.replace(".", "")
    elif "." in cleaned and "," in cleaned:
        # 1.234,56 format
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        # Could be 250,000 or 250,50
        if len(cleaned.split(",")[-1]) == 3:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return 0


# ---------------------------------------------------------------------------
# History tracking
# ---------------------------------------------------------------------------
def load_history() -> dict:
    if HISTORY_JSON.exists():
        with open(HISTORY_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(history: dict):
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def update_history(deals: list[dict], history: dict) -> dict:
    """Track price changes over time."""
    now = datetime.now().isoformat()
    for deal in deals:
        did = deal["id"]
        if did not in history:
            history[did] = {
                "url": deal["url"],
                "title": deal["title"],
                "prices": [{"price": deal["price"], "date": now}],
                "first_seen": now,
            }
        else:
            last_price = history[did]["prices"][-1]["price"]
            if deal["price"] != last_price:
                history[did]["prices"].append({"price": deal["price"], "date": now})
                # Price drop -> bonus score
                if deal["price"] < last_price:
                    drop_pct = (1 - deal["price"] / last_price) * 100
                    deal["okazja_score"] += 20
                    deal["okazja_reasons"].append(f"Spadek ceny o {drop_pct:.0f}%!")
    return history


# ---------------------------------------------------------------------------
# HTML Dashboard generator
# ---------------------------------------------------------------------------
def generate_html(deals: list[dict]):
    """Generate a standalone HTML dashboard."""
    deals_sorted = sorted(deals, key=lambda d: d.get("okazja_score", 0), reverse=True)
    markets = sorted(set(d["market"] for d in deals))
    market_labels = {k: v.get("label", k) for k, v in CFG["markets"].items()}

    cards_html = ""
    for d in deals_sorted:
        discount = d.get("discount_pct", 0)
        if discount >= 30:
            card_class = "card great-deal"
            badge = "MEGA OKAZJA"
            badge_class = "badge-great"
        elif discount >= 20:
            card_class = "card good-deal"
            badge = "OKAZJA"
            badge_class = "badge-good"
        elif discount >= 10:
            card_class = "card interesting"
            badge = "Ciekawe"
            badge_class = "badge-interesting"
        else:
            card_class = "card"
            badge = ""
            badge_class = ""

        currency = CFG["markets"].get(d["market"], {}).get("currency", "PLN")
        reasons_html = "<br>".join(d.get("okazja_reasons", []))
        justification = d.get("justification", "")
        img_html = f'<img src="{d["image_url"]}" alt="" loading="lazy" onerror="this.style.display=\'none\'">' if d.get("image_url") else '<div class="no-image">Brak zdjęcia</div>'

        cards_html += f"""
        <div class="{card_class}" data-market="{d['market']}" data-discount="{discount}" data-price="{d['price']}" data-date="{d['found_at']}">
            <div class="card-image">{img_html}</div>
            <div class="card-body">
                {f'<span class="badge {badge_class}">{badge}</span>' if badge else ''}
                <h3 class="card-title"><a href="{d['url']}" target="_blank">{d['title'][:80]}</a></h3>
                <div class="card-details">
                    <div class="price">{d['price']:,.0f} {currency}</div>
                    <div class="metrics">
                        <span>{d['area']:.0f} m² | {d['price_m2']:,.0f} {currency}/m²</span>
                        {f'<span class="discount">-{discount:.0f}% vs rynek</span>' if discount > 0 else ''}
                    </div>
                    <div class="location">{d['location']}</div>
                    <div class="source">{d['source'].upper()} | Score: {d.get('okazja_score', 0)}</div>
                    {f'<div class="reasons">{reasons_html}</div>' if reasons_html else ''}
                    {f'<div class="justification">{justification}</div>' if justification else ''}
                </div>
            </div>
        </div>"""

    filter_buttons = '<button class="filter-btn active" data-market="all">Wszystkie</button>'
    for mk in markets:
        label = market_labels.get(mk, mk)
        count = sum(1 for d in deals_sorted if d["market"] == mk)
        filter_buttons += f'<button class="filter-btn" data-market="{mk}">{label} ({count})</button>'

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Monitor Nieruchomości — Okazje</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0f0f0f; color: #e0e0e0; font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; }}
h1 {{ text-align: center; margin-bottom: 8px; color: #fff; font-size: 1.8rem; }}
.subtitle {{ text-align: center; color: #888; margin-bottom: 20px; font-size: 0.9rem; }}
.stats {{ display: flex; gap: 20px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }}
.stat {{ background: #1a1a1a; padding: 12px 24px; border-radius: 8px; text-align: center; }}
.stat-value {{ font-size: 1.5rem; font-weight: bold; color: #4ade80; }}
.stat-label {{ font-size: 0.8rem; color: #888; }}
.filters {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 16px; flex-wrap: wrap; }}
.filter-btn {{ background: #1a1a1a; border: 1px solid #333; color: #ccc; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }}
.filter-btn:hover, .filter-btn.active {{ background: #2563eb; border-color: #2563eb; color: #fff; }}
.sort-bar {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 20px; }}
.sort-btn {{ background: #1a1a1a; border: 1px solid #333; color: #aaa; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }}
.sort-btn:hover, .sort-btn.active {{ background: #333; color: #fff; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; max-width: 1400px; margin: 0 auto; }}
.card {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; }}
.card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
.card.great-deal {{ border-color: #22c55e; box-shadow: 0 0 12px rgba(34,197,94,0.15); }}
.card.good-deal {{ border-color: #eab308; box-shadow: 0 0 12px rgba(234,179,8,0.1); }}
.card.interesting {{ border-color: #3b82f6; }}
.card-image {{ height: 180px; overflow: hidden; background: #111; display: flex; align-items: center; justify-content: center; }}
.card-image img {{ width: 100%; height: 100%; object-fit: cover; }}
.no-image {{ color: #555; font-size: 0.9rem; }}
.card-body {{ padding: 14px; }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-bottom: 8px; }}
.badge-great {{ background: #166534; color: #4ade80; }}
.badge-good {{ background: #713f12; color: #facc15; }}
.badge-interesting {{ background: #1e3a5f; color: #60a5fa; }}
.card-title {{ font-size: 0.95rem; margin-bottom: 8px; line-height: 1.3; }}
.card-title a {{ color: #e0e0e0; text-decoration: none; }}
.card-title a:hover {{ color: #60a5fa; }}
.price {{ font-size: 1.3rem; font-weight: bold; color: #fff; margin-bottom: 4px; }}
.metrics {{ font-size: 0.85rem; color: #aaa; margin-bottom: 4px; }}
.discount {{ color: #4ade80; font-weight: 600; margin-left: 8px; }}
.location {{ font-size: 0.8rem; color: #888; margin-bottom: 4px; }}
.source {{ font-size: 0.75rem; color: #666; }}
.reasons {{ font-size: 0.8rem; color: #facc15; margin-top: 6px; padding-top: 6px; border-top: 1px solid #2a2a2a; }}
.justification {{ font-size: 0.78rem; color: #a0a0b8; margin-top: 6px; padding-top: 6px; border-top: 1px solid #2a2a2a; line-height: 1.45; }}
.empty {{ text-align: center; padding: 60px; color: #666; }}
footer {{ text-align: center; margin-top: 40px; color: #555; font-size: 0.8rem; }}
</style>
</head>
<body>
<h1>Monitor Nieruchomości</h1>
<p class="subtitle">Ostatnia aktualizacja: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Okazje poniżej ceny rynkowej</p>

<div class="stats">
    <div class="stat"><div class="stat-value">{len(deals_sorted)}</div><div class="stat-label">Wszystkich ofert</div></div>
    <div class="stat"><div class="stat-value">{sum(1 for d in deals_sorted if d.get('discount_pct',0) >= 30)}</div><div class="stat-label">Mega okazje (&gt;30%)</div></div>
    <div class="stat"><div class="stat-value">{sum(1 for d in deals_sorted if d.get('discount_pct',0) >= 20)}</div><div class="stat-label">Dobre okazje (&gt;20%)</div></div>
</div>

<div class="filters">{filter_buttons}</div>

<div class="sort-bar">
    <button class="sort-btn active" data-sort="score">Score ↓</button>
    <button class="sort-btn" data-sort="discount">Rabat ↓</button>
    <button class="sort-btn" data-sort="price-asc">Cena ↑</button>
    <button class="sort-btn" data-sort="price-desc">Cena ↓</button>
    <button class="sort-btn" data-sort="date">Najnowsze</button>
</div>

<div class="grid" id="dealsGrid">
{cards_html if cards_html else '<div class="empty"><h2>Brak ofert</h2><p>Uruchom monitor aby pobrać oferty</p></div>'}
</div>

<footer>Nieruchomości Monitor v1.0 | Dane z Otodom, OLX, Idealista | Użytek prywatny</footer>

<script>
// Filtering
document.querySelectorAll('.filter-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const market = btn.dataset.market;
        document.querySelectorAll('.card').forEach(card => {{
            card.style.display = (market === 'all' || card.dataset.market === market) ? '' : 'none';
        }});
    }});
}});

// Sorting
document.querySelectorAll('.sort-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
        document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const grid = document.getElementById('dealsGrid');
        const cards = Array.from(grid.querySelectorAll('.card'));
        const sort = btn.dataset.sort;
        cards.sort((a, b) => {{
            if (sort === 'score') return parseFloat(b.dataset.discount) - parseFloat(a.dataset.discount);
            if (sort === 'discount') return parseFloat(b.dataset.discount) - parseFloat(a.dataset.discount);
            if (sort === 'price-asc') return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
            if (sort === 'price-desc') return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
            if (sort === 'date') return b.dataset.date.localeCompare(a.dataset.date);
            return 0;
        }});
        cards.forEach(c => grid.appendChild(c));
    }});
}});
</script>
</body>
</html>"""

    with open(DEALS_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    log.info(f"Dashboard zapisany: {DEALS_HTML}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    log.info("=" * 60)
    log.info("NIERUCHOMOŚCI MONITOR — START")
    log.info("=" * 60)

    all_deals = []
    history = load_history()

    for market_key, market_cfg in CFG["markets"].items():
        if not market_cfg.get("enabled", True):
            log.info(f"[SKIP] {market_key} — wyłączony")
            continue

        log.info(f"\n--- {market_cfg.get('label', market_key)} ---")

        for source in market_cfg.get("sources", []):
            try:
                if source == "otodom":
                    deals = scrape_otodom(market_key)
                elif source == "olx":
                    deals = scrape_olx(market_key)
                elif source in ("idealista", "idealista_es", "idealista_pt"):
                    deals = scrape_idealista(market_key)
                elif source in ("imobiliare", "storia_ro"):
                    deals = scrape_storia(market_key)
                elif source == "imot_bg":
                    deals = scrape_imot(market_key)
                elif source == "xe_gr":
                    deals = scrape_xe_gr(market_key)
                else:
                    log.warning(f"Nieznane źródło: {source}")
                    continue

                # Score each deal
                for deal in deals:
                    score_deal(deal, market_cfg)
                    deal["justification"] = generate_justification(deal, market_cfg)

                all_deals.extend(deals)
                log.info(f"  [{source}] -> {len(deals)} ofert")

            except Exception as e:
                log.error(f"  [{source}] BŁĄD: {e}")

    # Update history & detect price drops
    history = update_history(all_deals, history)
    save_history(history)

    # Filter to only interesting deals (any discount or keyword match)
    interesting = [d for d in all_deals if d.get("okazja_score", 0) > 0 or d.get("discount_pct", 0) > 0]
    # Also keep ALL deals for the dashboard (but sort by score)
    log.info(f"\n{'='*60}")
    log.info(f"PODSUMOWANIE: {len(all_deals)} ofert, {len(interesting)} ciekawych")

    great_deals = [d for d in all_deals if d.get("discount_pct", 0) >= 30]
    good_deals = [d for d in all_deals if 20 <= d.get("discount_pct", 0) < 30]
    log.info(f"  Mega okazje (>30%): {len(great_deals)}")
    log.info(f"  Dobre okazje (>20%): {len(good_deals)}")

    # Save deals
    output = {
        "timestamp": datetime.now().isoformat(),
        "total": len(all_deals),
        "interesting": len(interesting),
        "deals": all_deals,
    }
    with open(DEALS_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    log.info(f"Deals zapisane: {DEALS_JSON}")

    # Generate HTML dashboard
    generate_html(all_deals)

    # Trigger notifications for great deals
    if great_deals:
        try:
            from notify import send_notifications
            send_notifications(great_deals)
        except ImportError:
            log.info("Moduł notify niedostępny — pomijam powiadomienia")
        except Exception as e:
            log.error(f"Błąd powiadomień: {e}")

    log.info("MONITOR — KONIEC")
    return all_deals


if __name__ == "__main__":
    import sys
    if "--run-once" in sys.argv:
        # Just run and exit
        main()
        sys.exit(0)
    main()
