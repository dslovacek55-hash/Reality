import asyncio
import logging
import re

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Sreality category mappings
CATEGORY_MAIN = {1: "byt", 2: "dum", 3: "pozemek", 4: "komercni"}
CATEGORY_TYPE = {1: "prodej", 2: "pronajem"}

# Reverse mappings for API params
PROPERTY_TYPES = {"byt": 1, "dum": 2, "pozemek": 3, "komercni": 4}
TRANSACTION_TYPES = {"prodej": 1, "pronajem": 2}

SIZE_PATTERN = re.compile(r"(\d+)\s*m[²2]")
DISPOSITIONS = [
    "5+kk", "5+1", "4+kk", "4+1", "3+kk", "3+1",
    "2+kk", "2+1", "1+kk", "1+1", "6+",
]


class SrealityScraper(BaseScraper):
    source = "sreality"
    base_url = "https://www.sreality.cz/api/cs/v2"

    async def scrape(self) -> list[dict]:
        all_listings = []

        # Scrape both sale and rent for apartments and houses
        for cat_type in [1, 2]:  # sale, rent
            for cat_main in [1, 2]:  # apartments, houses
                listings = await self._scrape_category(cat_main, cat_type)
                all_listings.extend(listings)

        return all_listings

    async def _scrape_category(
        self, category_main: int, category_type: int
    ) -> list[dict]:
        listings = []
        page = 0
        per_page = 100

        while True:
            url = (
                f"{self.base_url}/estates"
                f"?category_main_cb={category_main}"
                f"&category_type_cb={category_type}"
                f"&per_page={per_page}"
                f"&page={page}"
            )

            try:
                resp = await self.fetch_with_retry(url)
                data = resp.json()
            except Exception as e:
                logger.error(f"[sreality] Error fetching page {page}: {e}")
                break

            estates = data.get("_embedded", {}).get("estates", [])
            if not estates:
                break

            for estate in estates:
                estate["_category_main_cb"] = category_main
                estate["_category_type_cb"] = category_type
                listings.append(estate)

            result_size = data.get("result_size", 0)
            fetched = (page + 1) * per_page
            if fetched >= result_size or fetched >= 500:
                break

            page += 1
            await asyncio.sleep(1.5)

        logger.info(
            f"[sreality] Category main={category_main} type={category_type}: "
            f"{len(listings)} listings"
        )
        return listings

    def parse_listing(self, raw: dict) -> dict:
        hash_id = raw.get("hash_id", raw.get("id", ""))
        seo = raw.get("seo", {})
        locality = seo.get("locality", "")
        name = raw.get("name", "")

        gps = raw.get("gps", {})
        lat = gps.get("lat")
        lon = gps.get("lon")

        price = raw.get("price")
        if isinstance(price, dict):
            price = price.get("value_raw")

        images = []
        for img in raw.get("_links", {}).get("images", [])[:5]:
            href = img.get("href", "")
            if href:
                images.append(href)

        cat_main = raw.get("_category_main_cb", 1)
        cat_type = raw.get("_category_type_cb", 1)

        city = ""
        district = ""
        if locality:
            parts = locality.split(" - ")
            if len(parts) >= 2:
                city = parts[0].strip()
                district = parts[1].strip()
            else:
                city = locality

        return {
            "external_id": str(hash_id),
            "url": f"https://www.sreality.cz/detail/{hash_id}",
            "title": name,
            "description": raw.get("description", ""),
            "property_type": CATEGORY_MAIN.get(cat_main, "byt"),
            "transaction_type": CATEGORY_TYPE.get(cat_type, "prodej"),
            "disposition": self._extract_disposition(raw),
            "price": price,
            "size_m2": self._extract_size(raw),
            "rooms": None,
            "latitude": lat,
            "longitude": lon,
            "city": city,
            "district": district,
            "address": locality,
            "images": images,
            "raw_data": {"hash_id": hash_id, "seo": seo},
        }

    def _extract_disposition(self, raw: dict) -> str | None:
        """Try to extract disposition from name or labels."""
        name = raw.get("name", "")
        for d in DISPOSITIONS:
            if d in name:
                return d
        return None

    def _extract_size(self, raw: dict) -> float | None:
        """Try to extract size from name (e.g., '67 m²')."""
        name = raw.get("name", "")
        match = SIZE_PATTERN.search(name)
        if match:
            return float(match.group(1))
        return None
