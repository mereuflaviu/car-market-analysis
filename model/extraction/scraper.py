import requests
import logging
import time
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent.parent
EXTRACTION_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_CSV = DATA_DIR / "raw_scraped_car_listings.csv"

LOGS_DIR = EXTRACTION_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOGS_DIR}/scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

car_features = [
    "make",
    "model",
    "year",
    "body_type",
    "mileage",
    "door_count",
    "nr_seats",
    "color",
    "fuel_type",
    "engine_capacity",
    "engine_power",
    "gearbox",
    "transmission",
    "pollution_standard",
    "price",
]


class AutovitScraper:
    url: str = "https://www.autovit.ro/autoturisme/second"
    headers: dict = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0'
    }
    limit_max_num_pages: int = 1000
    data_filepath: Path = OUTPUT_CSV

    def __init__(self, max_listings: int = 2000, delay: float = 0.5):
        self.max_listings = max_listings
        self.delay = delay
        self.data = []
        # initialize with the data in the csv file if it exists
        if self.data_filepath.exists() and self.data_filepath.stat().st_size != 0:
            try:
                self.data = pd.read_csv(self.data_filepath).to_dict(orient='records')
                logger.info(f"Loaded {len(self.data)} existing listings from {self.data_filepath}")
            except Exception as e:
                logger.error(f"Error loading existing data from {self.data_filepath}: {e}")

        self.session = requests.Session()
    
    def get_page(self, url: str, params: dict = None):
        """
        Fetch a listing web page and return the BeautifulSoup object.
        Raise exception on error.
        """
        try:
            response = self.session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')

        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_features_from_listing(self, listing_article):
        """
        Extract car details from a single listing element.
        Return a dictionary with car details or None if extraction fails.
        """
        # get the url of the listing, it has to start with https://www.autovit.ro/autoturisme/anunt/
        link_tag = listing_article.find('a', href=True)
        if not link_tag or not link_tag['href'].startswith('https://www.autovit.ro/autoturisme/anunt/'):
            return None

        # check if url has been scraped already
        if self.data and any(item.get('url') == link_tag['href'] for item in self.data):
            logger.info("Listing already scraped - skipping")
            return None

        # navigate to the listing page to extract details
        listing_soup = self.get_page(link_tag['href'])
        if not listing_soup:
            logger.info("Failed to fetch listing page - skipping")
            return None
        
        car_features_data = {}
        
        # extract the feature values from the div elements with data-testid="<feature_name>"
        for feature_name in car_features[:-1:]:  # exclude price, handled separately
            feature_div = listing_soup.find('div', {'data-testid': feature_name})
            if not feature_div or len(feature_div.find_all('p')) <= 1:
                logger.info(f"Missing feature {feature_name} - skipping listing")
                return None
            
            p_tags = feature_div.find_all('p')
            car_features_data[feature_name] = p_tags[1].get_text(strip=True)

        # get the price from span with class "offer-price__number"
        price_tag = listing_soup.find('span', class_='offer-price__number')
        price_currency = listing_soup.find('span', class_='offer-price__currency')
        if not price_currency or price_currency.get_text(strip=True).upper() != 'EUR':
            logger.info("Price not in EUR - skipping listing")
            return None
    
        car_features_data['price'] = price_tag.get_text(strip=True) if price_tag else None
        car_features_data['url'] = link_tag['href']

        # logger.info("Extracted features:")
        # logger.info(json.dumps(car_features_data, indent=4, ensure_ascii=False))
        return car_features_data

    def get_listings_from_page(self, page_number: int):
        try:
            soup = self.get_page(self.url, params = {'page': page_number})
            if not soup:
                return []

            # Find all car listing articles
            car_listings = soup.find_all('article')
            counter = 0
            
            for listing in car_listings:
                if len(self.data) >= self.max_listings:
                    break
                
                car_features = self.extract_features_from_listing(listing)
                if car_features:
                    self.data.append(car_features)
                    counter += 1
                    logger.info(f"#################### | Collected {len(self.data)}/{self.max_listings}")
            
            time.sleep(self.delay)  # Respect server - rate limiting
            return counter
            
        except Exception as e:
            logger.error(f"Error scraping page {page_number}: {e}")
            return 0

    def scrape(self):
        """
        Scrape pages to collect car listings until the number of listings reaches max_listings.
        """
        logger.info(f"Starting scraper")
        logger.info(f"Target number of listings: {self.max_listings}")

        page_number = 1
        saved_count = len(self.data)

        while len(self.data) < self.max_listings:
            logger.info(f"Scraping page {page_number}...")

            listings_collected = self.get_listings_from_page(page_number)
            if listings_collected == 0:
                logger.info("No more listings found or an error occurred. Stopping.")
                break

            page_number += 1

            # append the next batch of data to the csv file
            self.append_data_to_csv(self.data[saved_count:])
            saved_count = len(self.data)

            if page_number > self.limit_max_num_pages:
                logger.warning(f"Limit of {self.limit_max_num_pages} pages reached - stopping")
                break

        if len(self.data) >= saved_count:
            self.append_data_to_csv(self.data[saved_count:])

        logger.info(f"Scraping complete - Total listings collected: {len(self.data)}")

    def append_data_to_csv(self, data):
        df = pd.DataFrame(data)
        df.to_csv(self.data_filepath, mode='a', header=not self.data_filepath.exists(), index=False)
        logger.info(f"Batch {len(self.data) - len(data) + 1}-{len(self.data)} saved to {self.data_filepath}")


if __name__ == "__main__":
    scraper = AutovitScraper()
    scraper.scrape()
