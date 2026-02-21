import asyncio
import logging

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class BazosScraper(BaseScraper):
    source = "bazos"
    base_url = "https://www.bazos.cz/api/v1"

    async def scrape(self) -> list[dict]:
        all_listings = []
        offset = 0
        limit = 20  # Always use limit=20 per API requirement

        while True:
            url = (
                f"{self.base_url}/ads.php"
                f"?section=RE"
                f"&offset={offset}"
                f"&limit={limit}"
                f"&sort=date"
            )

            try:
                resp = await self.client.get(url)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(f"[bazos] Error fetching offset {offset}: {e}")
                break

            ads = data if isinstance(data, list) else data.get("ads", data.get("items", []))
            if not ads:
                break

            all_listings.extend(ads)

            if len(ads) < limit or len(all_listings) >= 500:
                break

            offset += limit
            await asyncio.sleep(2.0)  # Respectful delay for Bazos

        logger.info(f"[bazos] Fetched {len(all_listings)} listings")
        return all_listings

    def parse_listing(self, raw: dict) -> dict:
        ad_id = str(raw.get("id", raw.get("ad_id", "")))

        # Extract price from text or field
        price = raw.get("price")
        if isinstance(price, str):
            import re
            nums = re.findall(r"[\d\s]+", price.replace("\xa0", ""))
            if nums:
                price = float(nums[0].replace(" ", ""))
            else:
                price = None

        # Extract location
        locality = raw.get("locality", raw.get("location", ""))
        city = ""
        district = ""
        if locality:
            parts = locality.split(",")
            city = parts[0].strip()
            if len(parts) > 1:
                district = parts[1].strip()

        # Images
        images = []
        img = raw.get("image", raw.get("img", raw.get("photo", "")))
        if img:
            images = [img] if isinstance(img, str) else img[:5]

        # Determine transaction type from title/category
        title = raw.get("title", raw.get("name", ""))
        transaction_type = "prodej"
        title_lower = title.lower()
        if "pronájem" in title_lower or "pronajem" in title_lower:
            transaction_type = "pronajem"

        return {
            "external_id": ad_id,
            "url": raw.get("url", f"https://www.bazos.cz/inzerat/{ad_id}"),
            "title": title,
            "description": raw.get("description", raw.get("text", "")),
            "property_type": self._guess_property_type(title),
            "transaction_type": transaction_type,
            "disposition": self._extract_disposition(title),
            "price": price,
            "size_m2": self._extract_size(title + " " + raw.get("description", "")),
            "rooms": None,
            "latitude": raw.get("lat", raw.get("latitude")),
            "longitude": raw.get("lon", raw.get("longitude")),
            "city": city,
            "district": district,
            "address": locality,
            "images": images,
            "raw_data": {"bazos_id": ad_id},
        }

    def _guess_property_type(self, title: str) -> str:
        title_lower = title.lower()
        if "byt" in title_lower:
            return "byt"
        elif "dům" in title_lower or "dum" in title_lower or "rodinný" in title_lower:
            return "dum"
        elif "pozemek" in title_lower or "parcela" in title_lower:
            return "pozemek"
        return "byt"

    def _extract_disposition(self, text: str) -> str | None:
        import re
        dispositions = [
            "5+kk", "5+1", "4+kk", "4+1", "3+kk", "3+1",
            "2+kk", "2+1", "1+kk", "1+1",
        ]
        for d in dispositions:
            if d in text:
                return d
        return None

    def _extract_size(self, text: str) -> float | None:
        import re
        match = re.search(r"(\d+)\s*m[²2]", text)
        if match:
            return float(match.group(1))
        return None
