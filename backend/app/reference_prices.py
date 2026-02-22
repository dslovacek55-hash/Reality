"""
Reference prices per m2 for Czech real estate.

Sources:
- CZSO (Czech Statistical Office) regional averages: csu.gov.cz, 2024/2025
- Prague district data: Deloitte Real Index Q3-Q4 2024, Trigema/CG/Skanska quarterly reports
- Katastralni uzemi to district mapping: Prague city administration

Used as external reference for price comparison.
"""

# Average apartment prices per m2 by region (kraj), CZK, prodej (sale)
CZSO_PRICES_PRODEJ: dict[str, int] = {
    "Praha": 140_000,  # city-wide average, overridden by district data below
    "Stredocesky": 58_000,
    "Jihocesky": 44_000,
    "Plzensky": 52_000,
    "Karlovarsky": 27_000,
    "Ustecky": 22_000,
    "Liberecky": 42_000,
    "Kralovehradecky": 43_000,
    "Pardubicky": 42_000,
    "Vysocina": 37_000,
    "Jihomoravsky": 78_000,
    "Olomoucky": 42_000,
    "Zlinsky": 41_000,
    "Moravskoslezsky": 32_000,
}

# Average rent per m2 per month by region, CZK
CZSO_PRICES_PRONAJEM: dict[str, int] = {
    "Praha": 380,
    "Stredocesky": 240,
    "Jihocesky": 210,
    "Plzensky": 220,
    "Karlovarsky": 170,
    "Ustecky": 160,
    "Liberecky": 210,
    "Kralovehradecky": 200,
    "Pardubicky": 195,
    "Vysocina": 185,
    "Jihomoravsky": 280,
    "Olomoucky": 200,
    "Zlinsky": 195,
    "Moravskoslezsky": 180,
}

# -------------------------------------------------------------------
# Prague district-level prices (Praha 1-22)
# Source: Deloitte Real Index Q3-Q4 2024, Trigema/CG/Skanska reports
# Based on realized transaction prices and new-build asking prices
# -------------------------------------------------------------------

PRAGUE_DISTRICT_PRICES_PRODEJ: dict[int, int] = {
    1: 200_000,
    2: 155_000,
    3: 120_000,
    4: 110_000,
    5: 125_000,
    6: 135_000,
    7: 140_000,
    8: 115_000,
    9: 105_000,
    10: 110_000,
    11: 90_000,   # Chodov area
    12: 95_000,   # Modrany area
    13: 95_000,   # Stodulky area
    14: 85_000,   # Cerny Most area
    15: 85_000,   # Horni Pocernice area
    16: 90_000,
    17: 85_000,
    18: 80_000,
    19: 80_000,
    20: 85_000,
    21: 80_000,
    22: 75_000,
}

PRAGUE_DISTRICT_PRICES_PRONAJEM: dict[int, int] = {
    1: 450,
    2: 400,
    3: 370,
    4: 340,
    5: 360,
    6: 370,
    7: 390,
    8: 350,
    9: 330,
    10: 340,
    11: 300,
    12: 310,
    13: 310,
    14: 290,
    15: 280,
    16: 300,
    17: 280,
    18: 270,
    19: 270,
    20: 280,
    21: 270,
    22: 260,
}

# -------------------------------------------------------------------
# Katastralni uzemi -> Prague district mapping
# Maps Prague neighborhoods/cadastral areas to their administrative district number
# -------------------------------------------------------------------

KATASTRAL_TO_DISTRICT: dict[str, int] = {
    # Praha 1
    "stare-mesto": 1, "stare mesto": 1, "nove-mesto": 1, "josefov": 1,
    "mala-strana": 1, "mala strana": 1, "hradcany": 1,
    # Praha 2
    "vinohrady": 2, "vysehrad": 2,
    # Praha 3
    "zizkov": 3,
    # Praha 4
    "nusle": 4, "podoli": 4, "branik": 4, "lhotka": 4, "krc": 4,
    "michle": 4, "kunratice": 4, "chodov": 4, "haje": 4, "modrany": 4,
    "komorany": 4, "hodkovicky": 4,
    # Praha 5
    "smichov": 5, "kosire": 5, "motol": 5, "radlice": 5,
    "hlubocepy": 5, "jinonice": 5, "stodulky": 5, "barrandov": 5,
    "butovice": 5, "slivenec": 5, "lipence": 5, "zlicin": 5,
    "reporyje": 5, "lochkov": 5,
    # Praha 6
    "dejvice": 6, "bubenec": 6, "vokovice": 6, "veleslavin": 6,
    "brevnov": 6, "stresovice": 6, "liboc": 6, "nebusice": 6,
    "suchdol": 6, "lysolaje": 6, "sedlec": 6, "ruzyne": 6,
    "predni-kopanina": 6,
    # Praha 7
    "holesovice": 7, "letna": 7, "troja": 7, "bubny": 7,
    # Praha 8
    "karlin": 8, "liben": 8, "kobylisy": 8, "bohnice": 8,
    "dablice": 8, "dolni-chabry": 8, "cimice": 8, "brezineves": 8,
    # Praha 9
    "vysocany": 9, "prosek": 9, "strizkov": 9, "hloubetin": 9,
    "kbely": 9, "letnany": 9, "cakovice": 9, "vinor": 9,
    "satalice": 9, "klanovice": 9,
    # Praha 10
    "vrsovice": 10, "strasnice": 10, "zabehlice": 10,
    "hostivar": 10, "uhrineves": 10, "malesice": 10,
    "dolni-mecholupy": 10, "petrovice": 10, "kresice": 10,
    "benice": 10, "kolarov": 10, "kralovice": 10,
}


# Map major Czech cities to their regions
CITY_TO_REGION: dict[str, str] = {
    # Praha
    "praha": "Praha",
    # Stredocesky kraj
    "kladno": "Stredocesky", "mlada-boleslav": "Stredocesky", "pribram": "Stredocesky",
    "kolin": "Stredocesky", "kutna-hora": "Stredocesky", "benesov": "Stredocesky",
    "beroun": "Stredocesky", "melnik": "Stredocesky", "nymburk": "Stredocesky",
    "rakovnik": "Stredocesky", "brandys-nad-labem": "Stredocesky",
    # Jihocesky kraj
    "ceske-budejovice": "Jihocesky", "tabor": "Jihocesky", "pisek": "Jihocesky",
    "strakonice": "Jihocesky", "jindrichuv-hradec": "Jihocesky",
    "cesky-krumlov": "Jihocesky", "prachatice": "Jihocesky",
    # Plzensky kraj
    "plzen": "Plzensky", "klatovy": "Plzensky", "rokycany": "Plzensky",
    "domazlice": "Plzensky", "tachov": "Plzensky",
    # Karlovarsky kraj
    "karlovy-vary": "Karlovarsky", "cheb": "Karlovarsky", "sokolov": "Karlovarsky",
    "marianske-lazne": "Karlovarsky", "frantiskovy-lazne": "Karlovarsky",
    # Ustecky kraj
    "usti-nad-labem": "Ustecky", "most": "Ustecky", "teplice": "Ustecky",
    "chomutov": "Ustecky", "decin": "Ustecky", "litomerice": "Ustecky",
    "louny": "Ustecky", "litvinov": "Ustecky",
    # Liberecky kraj
    "liberec": "Liberecky", "jablonec-nad-nisou": "Liberecky",
    "ceska-lipa": "Liberecky", "semily": "Liberecky", "turnov": "Liberecky",
    # Kralovehradecky kraj
    "hradec-kralove": "Kralovehradecky", "trutnov": "Kralovehradecky",
    "nachod": "Kralovehradecky", "jicin": "Kralovehradecky",
    "rychnov-nad-kneznou": "Kralovehradecky",
    # Pardubicky kraj
    "pardubice": "Pardubicky", "chrudim": "Pardubicky",
    "svitavy": "Pardubicky", "usti-nad-orlici": "Pardubicky",
    # Vysocina
    "jihlava": "Vysocina", "trebic": "Vysocina", "zdar-nad-sazavou": "Vysocina",
    "havlickuv-brod": "Vysocina", "pelhrimov": "Vysocina",
    # Jihomoravsky kraj
    "brno": "Jihomoravsky", "znojmo": "Jihomoravsky", "hodonin": "Jihomoravsky",
    "breclav": "Jihomoravsky", "vyskov": "Jihomoravsky", "blansko": "Jihomoravsky",
    # Olomoucky kraj
    "olomouc": "Olomoucky", "prostejov": "Olomoucky", "prerov": "Olomoucky",
    "sumperk": "Olomoucky", "jesenik": "Olomoucky",
    # Zlinsky kraj
    "zlin": "Zlinsky", "kromeriz": "Zlinsky", "uherske-hradiste": "Zlinsky",
    "vsetin": "Zlinsky", "valasske-mezirici": "Zlinsky",
    # Moravskoslezsky kraj
    "ostrava": "Moravskoslezsky", "opava": "Moravskoslezsky",
    "frydek-mistek": "Moravskoslezsky", "karvina": "Moravskoslezsky",
    "novy-jicin": "Moravskoslezsky", "havirov": "Moravskoslezsky",
    "trinec": "Moravskoslezsky", "bruntal": "Moravskoslezsky",
}


def normalize_city(city: str) -> str:
    """Normalize city name for lookup: lowercase, strip, replace spaces with dashes."""
    import unicodedata
    # Remove diacritics for matching
    nfkd = unicodedata.normalize("NFKD", city.lower().strip())
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return ascii_str.replace(" ", "-")


# Display-friendly names for base cities (Czech with diacritics)
CITY_DISPLAY_NAMES: dict[str, str] = {
    "praha": "Praha", "brno": "Brno", "ostrava": "Ostrava", "plzen": "Plzeň",
    "liberec": "Liberec", "olomouc": "Olomouc", "pardubice": "Pardubice",
    "zlin": "Zlín", "jihlava": "Jihlava", "kladno": "Kladno", "most": "Most",
    "teplice": "Teplice", "chomutov": "Chomutov", "opava": "Opava",
    "cheb": "Cheb", "sokolov": "Sokolov", "tabor": "Tábor", "pisek": "Písek",
    "znojmo": "Znojmo", "blansko": "Blansko", "beroun": "Beroun",
    "nymburk": "Nymburk", "turnov": "Turnov", "trutnov": "Trutnov",
    "chrudim": "Chrudim", "svitavy": "Svitavy", "semily": "Semily",
    "strakonice": "Strakonice", "prachatice": "Prachatice", "klatovy": "Klatovy",
    "rokycany": "Rokycany", "louny": "Louny",
    "ceske-budejovice": "České Budějovice", "hradec-kralove": "Hradec Králové",
    "karlovy-vary": "Karlovy Vary", "usti-nad-labem": "Ústí nad Labem",
    "mlada-boleslav": "Mladá Boleslav", "cesky-krumlov": "Český Krumlov",
    "jindrichuv-hradec": "Jindřichův Hradec", "kutna-hora": "Kutná Hora",
    "marianske-lazne": "Mariánské Lázně", "frantiskovy-lazne": "Františkovy Lázně",
    "jablonec-nad-nisou": "Jablonec nad Nisou", "ceska-lipa": "Česká Lípa",
    "rychnov-nad-kneznou": "Rychnov nad Kněžnou",
    "usti-nad-orlici": "Ústí nad Orlicí", "zdar-nad-sazavou": "Žďár nad Sázavou",
    "havlickuv-brod": "Havlíčkův Brod", "pelhrimov": "Pelhřimov",
    "frydek-mistek": "Frýdek-Místek", "novy-jicin": "Nový Jičín",
    "uherske-hradiste": "Uherské Hradiště", "valasske-mezirici": "Valašské Meziříčí",
    "brandys-nad-labem": "Brandýs nad Labem", "pribram": "Příbram",
    "kolin": "Kolín", "benesov": "Benešov", "melnik": "Mělník",
    "rakovnik": "Rakovník", "domazlice": "Domažlice", "tachov": "Tachov",
    "decin": "Děčín", "litomerice": "Litoměřice", "litvinov": "Litvínov",
    "prerov": "Přerov", "prostejov": "Prostějov", "sumperk": "Šumperk",
    "jesenik": "Jeseník", "kromeriz": "Kroměříž", "vsetin": "Vsetín",
    "hodonin": "Hodonín", "breclav": "Břeclav", "vyskov": "Vyškov",
    "karvina": "Karviná", "havirov": "Havířov", "trinec": "Třinec",
    "bruntal": "Bruntál", "nachod": "Náchod", "jicin": "Jičín",
    "trebic": "Třebíč",
}

# Pre-sorted keys (longest first) for prefix matching
_CITY_KEYS_BY_LEN = sorted(CITY_TO_REGION.keys(), key=len, reverse=True)


def get_base_city(city_str: str) -> str:
    """Extract the base city name from a full city string.

    E.g. 'praha-karlin-krizikova' → 'praha'
         'ceske-budejovice-ceske-budejovice-6' → 'ceske-budejovice'
    """
    norm = normalize_city(city_str)
    for key in _CITY_KEYS_BY_LEN:
        if norm == key or norm.startswith(key + "-"):
            return key
    return norm.split("-")[0] if "-" in norm else norm


def get_city_display_name(base_city: str) -> str:
    """Get a display-friendly name for a base city."""
    if base_city in CITY_DISPLAY_NAMES:
        return CITY_DISPLAY_NAMES[base_city]
    return base_city.replace("-", " ").title()


def _extract_prague_district_number(city: str) -> int | None:
    """Try to extract a Prague district number from a city string.

    Handles patterns like:
    - "Praha 5"
    - "Praha 10 - Uhrineves"
    - "praha-smichov-holeckova"
    - "praha-vinohrady-namesti..."
    """
    import re
    normalized = normalize_city(city)

    # Pattern 1: "praha-5", "praha-10", "praha 5 - nusle"
    m = re.match(r"praha[\s-]+(\d{1,2})", normalized)
    if m:
        return int(m.group(1))

    # Pattern 2: "praha-<katastral>-<street>" or "praha-<katastral>"
    # Remove "praha-" prefix and check the next part against KATASTRAL_TO_DISTRICT
    if normalized.startswith("praha-"):
        rest = normalized[6:]  # after "praha-"
        # Try matching the first part (before next dash) as katastralni uzemi
        parts = rest.split("-")
        # Try progressively longer combinations
        for length in range(1, min(len(parts) + 1, 4)):
            candidate = "-".join(parts[:length])
            if candidate in KATASTRAL_TO_DISTRICT:
                return KATASTRAL_TO_DISTRICT[candidate]

    return None


def get_region_for_city(city: str) -> str | None:
    """Find the region (kraj) for a given city name."""
    normalized = normalize_city(city)

    # Direct match
    if normalized in CITY_TO_REGION:
        return CITY_TO_REGION[normalized]

    # Partial match - city name contains a known city key
    for key, region in CITY_TO_REGION.items():
        if key in normalized or normalized in key:
            return region

    # Try matching start of the city name (e.g. "praha-vinohrady" -> "praha")
    for key, region in CITY_TO_REGION.items():
        if normalized.startswith(key) or key.startswith(normalized.split("-")[0]):
            return region

    return None


def get_reference_price_m2(city: str, transaction_type: str = "prodej") -> int | None:
    """Get reference price per m2 for a city.

    For Prague: uses district-level data from Deloitte Real Index.
    For other cities: uses CZSO regional averages.
    """
    # Try Prague district-level first
    district = _extract_prague_district_number(city)
    if district is not None:
        prices = PRAGUE_DISTRICT_PRICES_PRODEJ if transaction_type == "prodej" else PRAGUE_DISTRICT_PRICES_PRONAJEM
        if district in prices:
            return prices[district]

    # Fall back to CZSO regional data
    region = get_region_for_city(city)
    if not region:
        return None

    prices = CZSO_PRICES_PRODEJ if transaction_type == "prodej" else CZSO_PRICES_PRONAJEM
    return prices.get(region)


def get_reference_label(city: str) -> str | None:
    """Get a human-readable label for the reference source.

    For Prague districts: returns "Praha X (Deloitte)"
    For other cities: returns the region name + "(CSU)"
    """
    district = _extract_prague_district_number(city)
    if district is not None:
        return f"Praha {district} (Deloitte)"

    region = get_region_for_city(city)
    if region:
        return f"{region} (CSU)"
    return None


# Keep backward-compatible aliases (sync, for non-DB contexts)
def get_czso_price_m2(city: str, transaction_type: str = "prodej") -> int | None:
    return get_reference_price_m2(city, transaction_type)


def get_czso_region_name(city: str) -> str | None:
    return get_reference_label(city)


# ---------------------------------------------------------------------------
# Async reference price chain (uses DB for live benchmarks)
# Priority for prodej: KÚ median → RealityMix → Deloitte → CZSO
# Priority for pronajem: MF rental → KÚ median → RealityMix → Deloitte → CZSO
# ---------------------------------------------------------------------------

async def get_reference_price_async(
    session,
    city: str,
    transaction_type: str = "prodej",
    property_type: str | None = None,
) -> tuple[float | None, str | None]:
    """Get the best available reference price per m² and its label.

    Returns (price_m2, label) using a priority fallback chain.

    For prodej (sales):
      1. Own KÚ median from ku_price_stats (best match for this city)
      2. RealityMix district data from reference_benchmarks
      3. Static Deloitte district data
      4. Static CZSO regional data

    For pronajem (rentals) in Prague, MF KÚ-level data is checked first.
    """
    from sqlalchemy import text

    district = _extract_prague_district_number(city)

    # --- Layer 1: MF rental data (rentals only, KÚ-level) ---
    # Try to find MF data matching the KÚ name from the city string
    if transaction_type == "pronajem" and district is not None:
        try:
            # Try to extract KÚ name from city (e.g. "Praha 2 - Vinohrady" -> check "Vinohrady")
            normalized = normalize_city(city)
            ku_candidates = []
            if normalized.startswith("praha-"):
                rest = normalized[6:]
                parts = rest.split("-")
                # Skip the district number
                if parts and parts[0].isdigit():
                    parts = parts[1:]
                for length in range(1, min(len(parts) + 1, 4)):
                    candidate = "-".join(parts[:length])
                    if candidate and not candidate.isdigit():
                        ku_candidates.append(candidate)

            for candidate in ku_candidates:
                q = text("""
                    SELECT price_m2, region
                    FROM reference_benchmarks
                    WHERE source = 'mf_rental'
                      AND LOWER(region) LIKE :pattern
                      AND transaction_type = 'pronajem'
                    ORDER BY fetched_at DESC
                    LIMIT 1
                """)
                row = (await session.execute(q, {"pattern": f"%{candidate}%"})).first()
                if row and row.price_m2:
                    return float(row.price_m2), f"{row.region} (MF)"
        except Exception:
            pass

    # --- Layer 2: Own KÚ median from ku_price_stats ---
    # Extract KÚ name from city (e.g. "praha-branik-ke-krci" -> "branik")
    if district is not None:
        try:
            normalized = normalize_city(city)
            ku_part = None
            if normalized.startswith("praha-"):
                rest = normalized[6:]
                parts = rest.split("-")
                # Skip leading district numbers
                while parts and parts[0].isdigit():
                    parts = parts[1:]
                if parts:
                    for length in range(1, min(len(parts) + 1, 4)):
                        candidate = "-".join(parts[:length])
                        if candidate in KATASTRAL_TO_DISTRICT:
                            ku_part = candidate
                            break
                    if not ku_part and parts[0]:
                        ku_part = parts[0]

            params: dict = {"txn": transaction_type}
            type_clause = ""
            if property_type:
                type_clause = "AND ks.property_type = :ptype"
                params["ptype"] = property_type

            if ku_part:
                # Match KÚ name via diacritics-stripped LIKE
                params["ku_pattern"] = f"%{ku_part}%"
                q = text(f"""
                    SELECT ks.median_price_m2, ks.ku_nazev, ks.sample_count
                    FROM ku_price_stats ks
                    WHERE ks.transaction_type = :txn
                      {type_clause}
                      AND ks.sample_count >= 5
                      AND LOWER(TRANSLATE(ks.ku_nazev,
                          'áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ',
                          'acdeeinorstuuyzACDEEINORSTUUYZ')) LIKE :ku_pattern
                    ORDER BY ks.sample_count DESC
                    LIMIT 1
                """)
            else:
                # Fallback: find the most common KÚ for exact city
                params["city_exact"] = city
                q = text(f"""
                    SELECT ks.median_price_m2, ks.ku_nazev, ks.sample_count
                    FROM ku_price_stats ks
                    WHERE ks.transaction_type = :txn
                      {type_clause}
                      AND ks.sample_count >= 5
                      AND ks.ku_kod IN (
                          SELECT p.ku_kod FROM properties p
                          WHERE p.city = :city_exact AND p.ku_kod IS NOT NULL
                      )
                    ORDER BY ks.sample_count DESC
                    LIMIT 1
                """)

            row = (await session.execute(q, params)).first()
            if row and row.median_price_m2:
                return float(row.median_price_m2), f"{row.ku_nazev} (median, N={row.sample_count})"
        except Exception:
            pass

    # --- Layer 3: RealityMix district data ---
    if district is not None:
        try:
            region_name = f"Praha {district}"
            q = text("""
                SELECT price_m2, region
                FROM reference_benchmarks
                WHERE source = 'realitymix'
                  AND region = :region
                  AND transaction_type = :txn
                ORDER BY fetched_at DESC
                LIMIT 1
            """)
            row = (await session.execute(q, {"region": region_name, "txn": transaction_type})).first()
            if row and row.price_m2:
                return float(row.price_m2), f"{row.region} (RealityMix)"
        except Exception:
            pass

    # --- Layer 4: Static Deloitte district data ---
    if district is not None:
        prices = PRAGUE_DISTRICT_PRICES_PRODEJ if transaction_type == "prodej" else PRAGUE_DISTRICT_PRICES_PRONAJEM
        if district in prices:
            return float(prices[district]), f"Praha {district} (Deloitte)"

    # --- Layer 5: Static CZSO regional data ---
    region = get_region_for_city(city)
    if region:
        prices = CZSO_PRICES_PRODEJ if transaction_type == "prodej" else CZSO_PRICES_PRONAJEM
        price = prices.get(region)
        if price:
            return float(price), f"{region} (CSU)"

    return None, None
