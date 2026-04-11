"""
Extended scraper for autovit.ro – basic features + full equipment list.

Equipment is extracted from the __NEXT_DATA__ JSON blob (Next.js SSR).
Path: props.pageProps.advert.equipment  →  list of {key, label, values:[{key,label}]}

Each item's `key` is matched against EQUIPMENT_KEY_MAP.
For multi-value fields (upholstery, climate), the item `label` is also checked.

Equipment features stored as binary columns (1 = present, 0 = absent).
"""

import json
import unicodedata
import requests
import logging
import time
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent.parent
EXTRACTION_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_CSV = DATA_DIR / "raw_scraped_extended.csv"

LOGS_DIR = EXTRACTION_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/scraper_extended.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Basic structured features (extracted via data-testid divs)
# ---------------------------------------------------------------------------
BASIC_FEATURES = [
    "make", "model", "year", "body_type", "mileage", "door_count", "nr_seats",
    "color", "fuel_type", "engine_capacity", "engine_power",
    "gearbox", "transmission", "pollution_standard",
]

# ---------------------------------------------------------------------------
# Equipment mapping.
#
# EQUIPMENT_KEY_MAP  – direct autovit item `key` → our column name.
#   Most features: presence of the key means the feature exists.
#
# EQUIPMENT_LABEL_MAP – for "type" keys whose VALUE is in the label text:
#   (item_key, label_substring_lowercase) → our column name.
#   Used for upholstery_type, air_conditioning_type, cruisecontrol_type, etc.
# ---------------------------------------------------------------------------

# Columns present in the output CSV (defines final column order too)
EQUIPMENT_COLUMNS: list[str] = [
    # Multimedia
    "apple_carplay", "android_auto", "bluetooth", "wireless_charging",
    "navigation", "internet", "usb_port", "head_up_display",
    # Climate
    "ac", "climatronic", "climatronic_2zone", "climatronic_3zone", "climatronic_4zone",
    # Roof
    "panoramic_roof", "electric_sunroof", "manual_sunroof", "rear_glass_sunroof",
    # Upholstery
    "upholstery_alcantara", "upholstery_leather_mix", "upholstery_leather", "upholstery_fabric",
    # Seats
    "electric_driver_seat", "heated_driver_seat", "heated_passenger_seat",
    "ventilated_front_seats", "ventilated_rear_seats", "memory_seat",
    # Interior
    "front_armrest", "sport_steering_wheel", "paddle_shifters",
    # Access / convenience
    "keyless_entry", "keyless_go", "heated_windshield",
    "air_suspension", "sport_suspension",
    # Cruise
    "predictive_acc", "cruise_control", "adaptive_cruise",
    # Lights
    "bi_xenon", "laser_lights", "led_lights", "xenon", "dynamic_lights", "follow_me_home",
    # Parking / safety
    "front_park_sensors", "rear_park_sensors", "park_assist", "auto_park",
    "camera_360", "rear_camera", "folding_mirrors", "blind_spot",
    "lane_assist", "distance_control", "autonomous_driving", "isofix",
]

# Direct key → column (autovit item key maps 1-to-1 to our column)
EQUIPMENT_KEY_MAP: dict[str, str] = {
    "apple_carplay":                        "apple_carplay",
    "android_auto":                         "android_auto",
    "bluetooth":                            "bluetooth",
    "wireless_charging":                    "wireless_charging",
    "navigation":                           "navigation",
    "gps_navigation":                       "navigation",
    "internet_access":                      "internet",
    "usb":                                  "usb_port",
    "usb_port":                             "usb_port",
    "head_up_display":                      "head_up_display",
    # Roof
    "panoramic_roof":                       "panoramic_roof",
    "sunroof_electric":                     "electric_sunroof",
    "sunroof":                              "electric_sunroof",
    "sunroof_manual":                       "manual_sunroof",
    "rear_window_electric_sunroof":         "rear_glass_sunroof",
    # Seats
    "electric_seat_driver":                 "electric_driver_seat",
    "heated_seat_driver":                   "heated_driver_seat",
    "heated_seat_passenger":                "heated_passenger_seat",
    "ventilated_seats_front":               "ventilated_front_seats",
    "ventilated_seats_rear":                "ventilated_rear_seats",
    "seat_memory":                          "memory_seat",
    # Interior
    "armrest_front":                        "front_armrest",
    "sport_steering_wheel":                 "sport_steering_wheel",
    "steering_wheel_gear_change":           "paddle_shifters",
    # Access / convenience
    "keyless_entry":                        "keyless_entry",
    "keyless_start":                        "keyless_go",
    "windscreen_heating":                   "heated_windshield",
    "air_suspension":                       "air_suspension",
    "sport_suspension":                     "sport_suspension",
    # Lights
    "bi_xenon_headlights":                  "bi_xenon",
    "laser_headlights":                     "laser_lights",
    "led_headlights":                       "led_lights",
    "xenon_headlights":                     "xenon",
    "adaptive_headlights":                  "dynamic_lights",
    "follow_me_home":                       "follow_me_home",
    # Parking / safety
    "park_distance_control_front":          "front_park_sensors",
    "park_distance_control_rear":           "rear_park_sensors",
    "parking_assist":                       "park_assist",
    "automatic_parking":                    "auto_park",
    "camera_360":                           "camera_360",
    "rear_view_camera":                     "rear_camera",
    "door_mirror_folding_electric":         "folding_mirrors",
    "blind_spot_monitoring":                "blind_spot",
    "lane_assist":                          "lane_assist",
    "adaptive_cruise_control":              "adaptive_cruise",
    "distance_warning":                     "distance_control",
    "autonomous_driving":                   "autonomous_driving",
    "child_seat_fixation":                  "isofix",
}

# For "type" fields where the label tells us which sub-option is present.
# Key: (autovit item key,  label substring lowercase)  →  our column
EQUIPMENT_LABEL_MAP: dict[tuple[str, str], str] = {
    # Air conditioning type
    ("air_conditioning_type", "aer conditionat"):       "ac",
    ("air_conditioning_type", "climatronic 2 zone"):    "climatronic_2zone",
    ("air_conditioning_type", "climatronic 3 zone"):    "climatronic_3zone",
    ("air_conditioning_type", "climatronic 4 zone"):    "climatronic_4zone",
    ("air_conditioning_type", "climatronic"):           "climatronic",
    # Upholstery type
    ("upholstery_type", "alcantara"):                   "upholstery_alcantara",
    ("upholstery_type", "mixta piele"):                 "upholstery_leather_mix",
    ("upholstery_type", "tapiterie piele"):             "upholstery_leather",
    ("upholstery_type", "piele"):                       "upholstery_leather",
    ("upholstery_type", "stofa"):                       "upholstery_fabric",
    # Cruise control type
    ("cruisecontrol_type", "adaptive cruise control predictive"): "predictive_acc",
    ("cruisecontrol_type", "adaptiv"):                  "adaptive_cruise",
    ("cruisecontrol_type", "pilot automat"):            "cruise_control",
}


def _strip_diacritics(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


# ---------------------------------------------------------------------------
# Equipment extraction from __NEXT_DATA__
# ---------------------------------------------------------------------------

def _extract_equipment_from_advert(advert: dict) -> dict[str, int]:
    """
    Extract equipment flags from advert dict (already parsed from __NEXT_DATA__).

    advert.equipment structure:
      [ { "key": "comfort_and_addons", "values": [
            { "key": "heated_seat_driver", "label": "Incalzire scaun sofer" }, ...
          ]
        }, ... ]
    """
    equipment_list = advert.get("equipment")
    if not isinstance(equipment_list, list):
        return {col: 0 for col in EQUIPMENT_COLUMNS}

    present: set[str] = set()

    for category in equipment_list:
        for item in category.get("values", []):
            item_key = item.get("key", "")
            item_label = _strip_diacritics(item.get("label", ""))

            # 1. Direct key match
            col = EQUIPMENT_KEY_MAP.get(item_key)
            if col:
                present.add(col)
                continue

            # 2. Label-dependent type match (upholstery_type, ac type, cruise type)
            for (map_key, label_sub), map_col in EQUIPMENT_LABEL_MAP.items():
                if item_key == map_key and label_sub in item_label:
                    present.add(map_col)
                    break

    return {col: (1 if col in present else 0) for col in EQUIPMENT_COLUMNS}


# ---------------------------------------------------------------------------
# Main scraper class
# ---------------------------------------------------------------------------

class AutovitExtendedScraper:
    url: str = "https://www.autovit.ro/autoturisme/second"
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0"
    }
    limit_max_num_pages: int = 1000
    data_filepath: Path = OUTPUT_CSV

    def __init__(self, max_listings: int = 5000, delay: float = 0.7):
        self.max_listings = max_listings
        self.delay = delay
        self.data: list[dict] = []

        if self.data_filepath.exists() and self.data_filepath.stat().st_size != 0:
            try:
                self.data = pd.read_csv(self.data_filepath).to_dict(orient="records")
                logger.info(f"Loaded {len(self.data)} existing listings from {self.data_filepath}")
            except Exception as e:
                logger.error(f"Error loading existing data: {e}")

        self._scraped_urls: set[str] = {str(row.get("url", "")) for row in self.data}
        self.session = requests.Session()

    def _get_page(self, url: str, params: dict = None) -> BeautifulSoup | None:
        try:
            resp = self.session.get(url, headers=self.headers, params=params, timeout=20)
            resp.raise_for_status()
            return BeautifulSoup(resp.content, "html.parser")
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _extract_listing(self, listing_article) -> dict | None:
        link_tag = listing_article.find("a", href=True)
        if not link_tag or not link_tag["href"].startswith(
            "https://www.autovit.ro/autoturisme/anunt/"
        ):
            return None

        url = link_tag["href"]
        if url in self._scraped_urls:
            return None

        soup = self._get_page(url)
        if not soup:
            return None

        # ---- parse __NEXT_DATA__ once, use for everything -------------
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script or not script.string:
            logger.info("No __NEXT_DATA__ – skipping")
            return None
        try:
            page_data = json.loads(script.string)
            advert = page_data["props"]["pageProps"]["advert"]
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.info("Failed to parse __NEXT_DATA__ – skipping")
            return None

        # ---- price (skip non-EUR listings) ----------------------------
        price_info = advert.get("price", {})
        if not isinstance(price_info, dict):
            return None
        if price_info.get("currency", "").upper() != "EUR":
            logger.info("Price not in EUR – skipping")
            return None
        price_val = price_info.get("value")
        if not price_val:
            logger.info("No price value – skipping")
            return None

        # ---- basic features from advert.details -----------------------
        details: dict[str, str] = {
            d["key"]: d.get("value", "") or ""
            for d in advert.get("details", [])
            if d.get("key")
        }

        row: dict = {feat: details.get(feat) or None for feat in BASIC_FEATURES}
        row["price"] = price_val

        # ---- equipment boolean flags ----------------------------------
        row.update(_extract_equipment_from_advert(advert))
        row["url"] = url
        return row

    def _scrape_page(self, page_number: int) -> int:
        soup = self._get_page(self.url, params={"page": page_number})
        if not soup:
            return 0

        articles = soup.find_all("article")
        collected = 0

        for article in articles:
            if len(self.data) >= self.max_listings:
                break
            row = self._extract_listing(article)
            if row:
                self.data.append(row)
                self._scraped_urls.add(row["url"])
                collected += 1
                logger.info(f"### Collected {len(self.data)}/{self.max_listings}")

        time.sleep(self.delay)
        return collected

    def _append_to_csv(self, rows: list[dict]):
        if not rows:
            return
        df = pd.DataFrame(rows)
        write_header = not self.data_filepath.exists() or self.data_filepath.stat().st_size == 0
        df.to_csv(self.data_filepath, mode="a", header=write_header, index=False, encoding="utf-8")
        logger.info(f"Saved batch of {len(rows)} rows → {self.data_filepath}")

    def scrape(self, start_page: int = 1, max_consecutive_empty: int = 5):
        logger.info(f"Starting extended scraper | target={self.max_listings} | start_page={start_page}")
        page = start_page
        saved_count = len(self.data)
        consecutive_empty = 0

        while len(self.data) < self.max_listings:
            logger.info(f"Scraping page {page}…")
            collected = self._scrape_page(page)

            if collected == 0:
                consecutive_empty += 1
                logger.info(f"No new listings on page {page} ({consecutive_empty}/{max_consecutive_empty} consecutive empty)")
                if consecutive_empty >= max_consecutive_empty:
                    logger.info("Too many consecutive empty pages – stopping.")
                    break
            else:
                consecutive_empty = 0
                self._append_to_csv(self.data[saved_count:])
                saved_count = len(self.data)

            page += 1

            if page > self.limit_max_num_pages:
                logger.warning("Max pages limit reached.")
                break

        if len(self.data) > saved_count:
            self._append_to_csv(self.data[saved_count:])

        logger.info(f"Done – total listings: {len(self.data)}")

    # ------------------------------------------------------------------
    # Debug helper: dump __NEXT_DATA__ JSON from one listing to a file
    # ------------------------------------------------------------------
    def dump_next_data(self, listing_url: str, out_file: str = "debug_next_data.json"):
        """Call this manually to inspect the JSON structure of a listing."""
        soup = self._get_page(listing_url)
        if not soup:
            print("Failed to fetch page")
            return
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script:
            print("No __NEXT_DATA__ script found")
            # Print all script tag ids for inspection
            for s in soup.find_all("script"):
                print("  script id:", s.get("id"), "type:", s.get("type"))
            return
        out = Path(out_file)
        out.write_text(script.string, encoding="utf-8")
        print(f"Saved {len(script.string)} chars to {out.resolve()}")
        # Preview top-level structure
        data = json.loads(script.string)
        print("Top-level keys:", list(data.keys()))
        pp = data.get("props", {}).get("pageProps", {})
        print("pageProps keys:", list(pp.keys())[:15])


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Autovit extended scraper")
    parser.add_argument("--max", type=int, default=5000, help="Max listings (default 5000)")
    parser.add_argument("--delay", type=float, default=0.7, help="Delay between requests in seconds")
    parser.add_argument("--start-page", type=int, default=1, help="Page number to start from (default 1)")
    parser.add_argument("--max-empty", type=int, default=5, help="Stop after N consecutive pages with no new listings (default 5)")
    parser.add_argument(
        "--debug-url", type=str, default=None,
        help="Dump __NEXT_DATA__ JSON from a single listing URL and exit"
    )
    args = parser.parse_args()

    scraper = AutovitExtendedScraper(max_listings=args.max, delay=args.delay)

    if args.debug_url:
        scraper.dump_next_data(args.debug_url)
    else:
        scraper.scrape(start_page=args.start_page, max_consecutive_empty=args.max_empty)
