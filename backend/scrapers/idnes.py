import asyncio
import json
import logging
import re

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = "https://reality.idnes.cz"

CATEGORIES = [
    ("prodej", "byty", "byt", "prodej"),
    ("prodej", "domy", "dum", "prodej"),
    ("pronajem", "byty", "byt", "pronajem"),
    ("pronajem", "domy", "dum", "pronajem"),
]

SIZE_PATTERN = re.compile(r"(\d+)\s*m[²2]")
DISPOSITION_PATTERN = re.compile(r"\b(\d\+(?:kk|1)|6\+|atypick[yý])\b", re.IGNORECASE)
PRICE_PATTERN = re.compile(r"([\d\s]+)\s*Kč", re.IGNORECASE)
TOTAL_PATTERN = re.compile(r"([\d\s]+)\s*inzerát", re.IGNORECASE)

DISPOSITIONS_NORMALIZE = {
    "1+kk": "1+kk", "1+1": "1+1",
    "2+kk": "2+kk", "2+1": "2+1",
    "3+kk": "3+kk", "3+1": "3+1",
    "4+kk": "4+kk", "4+1": "4+1",
    "5+kk": "5+kk", "5+1": "5+1",
    "6+": "6+",
}


class IdnesScraper(BaseScraper):
    source = "idnes"
    base_url = BASE_URL

    async def scrape(self) -> list[dict]:
        all_listings = []

        for txn_slug, type_slug, prop_type, txn_type in CATEGORIES:
            listings = await self._scrape_category(txn_slug, type_slug, prop_type, txn_type)
            all_listings.extend(listings)

        logger.info(f"[idnes] Fetched {len(all_listings)} total listings")
        return all_listings

    async def _scrape_category(
        self, txn_slug: str, type_slug: str, prop_type: str, txn_type: str
    ) -> list[dict]:
        listings = []
        page = 0
        max_pages = 17  # ~500 listings at 30/page

        while page < max_pages:
            url = f"{BASE_URL}/s/{txn_slug}/{type_slug}/"
            if page > 0:
                url += f"?page={page}"

            try:
                resp = await self.fetch_with_retry(url, headers={
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "cs,en;q=0.9",
                })
                html = resp.text
            except Exception as e:
                logger.error(f"[idnes] Error fetching {txn_slug}/{type_slug} page {page}: {e}")
                break

            soup = BeautifulSoup(html, "lxml")
            items = soup.select(".c-products__item")

            # Filter out ads
            items = [i for i in items if "c-products__item-advertisment" not in i.get("class", [])]

            if not items:
                break

            for item in items:
                parsed = self._parse_card(item, prop_type, txn_type)
                if parsed:
                    listings.append(parsed)

            page += 1
            await asyncio.sleep(1.5)

        logger.info(f"[idnes] Category {txn_slug}/{type_slug}: {len(listings)} listings")
        return listings

    def _parse_card(self, card, prop_type: str, txn_type: str) -> dict | None:
        """Parse a listing card from the HTML."""
        # URL + external ID
        link = card.select_one(".c-products__link")
        if not link:
            return None

        detail_url = link.get("href", "")
        if detail_url and not detail_url.startswith("http"):
            detail_url = BASE_URL + detail_url

        # Extract MongoDB-style ID from URL
        url_parts = detail_url.rstrip("/").split("/")
        external_id = url_parts[-1] if url_parts else ""
        if not external_id or len(external_id) < 10:
            return None

        # Title
        title_el = card.select_one(".c-products__title")
        title_text = title_el.get_text(strip=True) if title_el else ""

        # Price
        price_el = card.select_one(".c-products__price")
        price_text = price_el.get_text(strip=True) if price_el else ""
        price = self._parse_price(price_text)

        # Location
        info_el = card.select_one(".c-products__info")
        address = info_el.get_text(strip=True) if info_el else ""

        city = ""
        district = ""
        if address:
            parts = [p.strip() for p in address.split(",")]
            if len(parts) >= 2:
                # Last part is usually the city: "Praha 5 - Radlice"
                city = parts[-1].strip()
                district = parts[0].strip() if len(parts) >= 2 else ""
            else:
                city = parts[0]

        # Image
        images = []
        img_el = card.select_one(".c-products__img img")
        if img_el:
            img_url = img_el.get("data-src") or img_el.get("src", "")
            if img_url and "data:image" not in img_url:
                images.append(img_url)

        # Disposition from title
        disposition = self._extract_disposition(title_text)

        # Size from title
        size_m2 = self._extract_size(title_text)

        return {
            "external_id": external_id,
            "url": detail_url,
            "title": title_text,
            "description": "",
            "property_type": prop_type,
            "transaction_type": txn_type,
            "disposition": disposition,
            "price": price,
            "size_m2": size_m2,
            "rooms": None,
            "latitude": None,
            "longitude": None,
            "city": city,
            "district": district,
            "address": address,
            "images": images,
            "raw_data": {"idnes_id": external_id},
        }

    def parse_listing(self, raw: dict) -> dict:
        """BaseScraper interface — raw dicts are already parsed by _parse_card."""
        return raw

    def _extract_disposition(self, text: str) -> str | None:
        match = DISPOSITION_PATTERN.search(text)
        if match:
            d = match.group(1).lower()
            return DISPOSITIONS_NORMALIZE.get(d, d)
        return None

    def _extract_size(self, text: str) -> float | None:
        match = SIZE_PATTERN.search(text)
        if match:
            return float(match.group(1))
        return None

    def _parse_price(self, text: str) -> int | None:
        match = PRICE_PATTERN.search(text)
        if match:
            num_str = match.group(1).replace("\xa0", "").replace(" ", "")
            try:
                return int(num_str)
            except ValueError:
                return None
        return None
