import asyncio
import logging

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://www.bezrealitky.cz/api/graphql"

SEARCH_QUERY = """
query ListAdverts($input: AdvertListInput!) {
  listAdverts(input: $input) {
    list {
      id
      uri
      title
      description
      mainImage
      images
      price
      currency
      surface
      disposition
      offerType
      estateType
      address {
        city
        cityPart
        street
        lat
        lng
      }
    }
    totalCount
  }
}
"""


class BezrealitkyScraper(BaseScraper):
    source = "bezrealitky"
    base_url = "https://www.bezrealitky.cz"

    async def scrape(self) -> list[dict]:
        all_listings = []

        for offer_type in ["PRODEJ", "PRONAJEM"]:
            for estate_type in ["BYT", "DUM"]:
                listings = await self._scrape_category(offer_type, estate_type)
                all_listings.extend(listings)

        logger.info(f"[bezrealitky] Fetched {len(all_listings)} total listings")
        return all_listings

    async def _scrape_category(
        self, offer_type: str, estate_type: str
    ) -> list[dict]:
        listings = []
        page = 1
        per_page = 50

        while True:
            variables = {
                "input": {
                    "offerType": offer_type,
                    "estateType": estate_type,
                    "page": page,
                    "limit": per_page,
                    "order": "TIMEORDER_DESC",
                }
            }

            try:
                resp = await self.client.post(
                    GRAPHQL_URL,
                    json={"query": SEARCH_QUERY, "variables": variables},
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Referer": "https://www.bezrealitky.cz/",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.error(
                    f"[bezrealitky] Error fetching {offer_type}/{estate_type} "
                    f"page {page}: {e}"
                )
                break

            result = data.get("data", {}).get("listAdverts", {})
            items = result.get("list", [])
            total = result.get("totalCount", 0)

            if not items:
                break

            for item in items:
                item["_offer_type"] = offer_type
                item["_estate_type"] = estate_type
                listings.append(item)

            fetched = page * per_page
            if fetched >= total or fetched >= 500:
                break

            page += 1
            await asyncio.sleep(2.0)

        return listings

    def parse_listing(self, raw: dict) -> dict:
        ad_id = str(raw.get("id", ""))
        address = raw.get("address", {}) or {}

        # Map offer type
        offer_type = raw.get("_offer_type", "PRODEJ")
        transaction_type = "prodej" if offer_type == "PRODEJ" else "pronajem"

        # Map estate type
        estate_type = raw.get("_estate_type", "BYT")
        property_type = "byt" if estate_type == "BYT" else "dum"

        # Images
        images = []
        main_img = raw.get("mainImage")
        if main_img:
            images.append(main_img)
        for img in (raw.get("images") or [])[:4]:
            if isinstance(img, str):
                images.append(img)
            elif isinstance(img, dict):
                images.append(img.get("url", ""))

        # Disposition mapping
        disposition = raw.get("disposition", "")
        disp_map = {
            "DISP_1_KK": "1+kk", "DISP_1_1": "1+1",
            "DISP_2_KK": "2+kk", "DISP_2_1": "2+1",
            "DISP_3_KK": "3+kk", "DISP_3_1": "3+1",
            "DISP_4_KK": "4+kk", "DISP_4_1": "4+1",
            "DISP_5_KK": "5+kk", "DISP_5_1": "5+1",
        }
        disposition_normalized = disp_map.get(disposition, disposition)

        city = address.get("city", "")
        district = address.get("cityPart", "")
        street = address.get("street", "")
        full_address = ", ".join(filter(None, [street, district, city]))

        uri = raw.get("uri", "")
        url = f"https://www.bezrealitky.cz/nemovitosti-byty-domy/{uri}" if uri else ""

        return {
            "external_id": ad_id,
            "url": url,
            "title": raw.get("title", ""),
            "description": raw.get("description", ""),
            "property_type": property_type,
            "transaction_type": transaction_type,
            "disposition": disposition_normalized,
            "price": raw.get("price"),
            "size_m2": raw.get("surface"),
            "rooms": None,
            "latitude": address.get("lat"),
            "longitude": address.get("lng"),
            "city": city,
            "district": district,
            "address": full_address,
            "images": images,
            "raw_data": {"bezrealitky_id": ad_id, "uri": uri},
        }
