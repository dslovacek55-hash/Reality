import asyncio
import logging

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.bezrealitky.cz/graphql/"

SEARCH_QUERY = """
query ListAdverts(
  $offerType: [OfferType],
  $estateType: [EstateType],
  $limit: Int,
  $offset: Int,
  $order: ResultOrder,
  $currency: Currency
) {
  listAdverts(
    offerType: $offerType,
    estateType: $estateType,
    limit: $limit,
    offset: $offset,
    order: $order,
    currency: $currency
  ) {
    list {
      id
      uri
      offerType
      estateType
      disposition
      price
      charges
      currency
      surface
      address(locale: CS)
      gps { lat lng }
      mainImage { url(filter: RECORD_MAIN) }
      publicImages(limit: 5) { url(filter: RECORD_THUMB) }
    }
    totalCount
  }
}
"""

DISPOSITION_MAP = {
    "DISP_1_KK": "1+kk", "DISP_1_1": "1+1",
    "DISP_2_KK": "2+kk", "DISP_2_1": "2+1",
    "DISP_3_KK": "3+kk", "DISP_3_1": "3+1",
    "DISP_4_KK": "4+kk", "DISP_4_1": "4+1",
    "DISP_5_KK": "5+kk", "DISP_5_1": "5+1",
}


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
        offset = 0
        limit = 50

        while True:
            variables = {
                "offerType": [offer_type],
                "estateType": [estate_type],
                "limit": limit,
                "offset": offset,
                "order": "TIMEORDER_DESC",
                "currency": "CZK",
            }

            try:
                resp = await self.fetch_with_retry(
                    GRAPHQL_URL,
                    method="POST",
                    json={"query": SEARCH_QUERY, "variables": variables},
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
                data = resp.json()
            except Exception as e:
                logger.error(
                    f"[bezrealitky] Error fetching {offer_type}/{estate_type} "
                    f"offset {offset}: {e}"
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

            offset += limit
            if offset >= total or offset >= 500:
                break

            await asyncio.sleep(2.0)

        return listings

    def parse_listing(self, raw: dict) -> dict:
        ad_id = str(raw.get("id", ""))

        # Map offer type
        offer_type = raw.get("_offer_type", raw.get("offerType", "PRODEJ"))
        transaction_type = "prodej" if offer_type == "PRODEJ" else "pronajem"

        # Map estate type
        estate_type = raw.get("_estate_type", raw.get("estateType", "BYT"))
        property_type = "byt" if estate_type == "BYT" else "dum"

        # Images — new structure uses nested objects
        images = []
        main_img = raw.get("mainImage")
        if isinstance(main_img, dict):
            url = main_img.get("url", "")
            if url:
                images.append(url)
        elif isinstance(main_img, str) and main_img:
            images.append(main_img)

        for img in (raw.get("publicImages") or [])[:4]:
            if isinstance(img, dict):
                url = img.get("url", "")
                if url:
                    images.append(url)
            elif isinstance(img, str) and img:
                images.append(img)

        # Disposition mapping
        disposition = raw.get("disposition", "")
        disposition_normalized = DISPOSITION_MAP.get(disposition, disposition)

        # Address — now a flat formatted string
        address_str = raw.get("address", "") or ""
        city = ""
        district = ""
        if address_str:
            parts = [p.strip() for p in address_str.split(",")]
            if len(parts) >= 2:
                city = parts[-1]
                district = parts[-2] if len(parts) >= 3 else ""
            else:
                city = parts[0]

        # GPS — separate object now
        gps = raw.get("gps") or {}
        lat = gps.get("lat")
        lng = gps.get("lng")

        uri = raw.get("uri", "")
        url = f"https://www.bezrealitky.cz/nemovitosti-byty-domy/{uri}" if uri else ""

        return {
            "external_id": ad_id,
            "url": url,
            "title": address_str,
            "description": "",
            "property_type": property_type,
            "transaction_type": transaction_type,
            "disposition": disposition_normalized,
            "price": raw.get("price"),
            "size_m2": raw.get("surface"),
            "rooms": None,
            "latitude": lat,
            "longitude": lng,
            "city": city,
            "district": district,
            "address": address_str,
            "images": images,
            "raw_data": {"bezrealitky_id": ad_id, "uri": uri},
        }
