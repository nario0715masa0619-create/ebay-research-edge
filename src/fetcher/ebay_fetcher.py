"""
eBay data fetching module with Trading API integration.
"""

import logging
import os
from typing import List, Dict, Any
from datetime import datetime
import uuid
from dotenv import load_dotenv

from src.config.config import config
from src.models.data_models import MarketRecord, SourceSite
from src.utils.ebay_api_client import eBayAPIClientXML
from tests.sample_data_generator import SampleDataGenerator

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class eBayFetcher:
    """Fetches sold listing data from eBay via Trading API."""

    def __init__(self, use_real_api: bool = True):
        """
        Initialize the eBay fetcher.

        Args:
            use_real_api (bool): If True, use real eBay API.
                                If False, use sample data (development mode).
        """
        self.use_real_api = use_real_api
        self.config = config

        if use_real_api:
            # Initialize real API client
            app_id = os.getenv("EBAY_APP_ID")
            dev_id = os.getenv("EBAY_DEV_ID")
            cert_id = os.getenv("EBAY_CERT_ID")
            user_token = os.getenv("EBAY_USER_TOKEN")

            if not all([app_id, dev_id, cert_id]):
                logger.warning("eBay API credentials not configured. Falling back to sample data.")
                self.use_real_api = False
                self.api_client = None
            else:
                self.api_client = eBayAPIClientXML(app_id, dev_id, cert_id, user_token)
                logger.info("eBayFetcher initialized in PRODUCTION mode (real API)")
        else:
            self.api_client = None
            logger.info("eBayFetcher initialized in DEVELOPMENT mode (sample data)")

    def fetch_sold_listings(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch sold listings from eBay for a given keyword.

        Args:
            keyword (str): Search keyword.
            limit (int): Maximum number of results to retrieve.

        Returns:
            List[Dict[str, Any]]: List of listing data dictionaries with category info.
        """
        logger.info(f"Fetching eBay sold listings for: {keyword}")

        if self.use_real_api and self.api_client:
            return self._fetch_from_api(keyword, limit)
        else:
            return self._fetch_from_sample_data(keyword, limit)

    def _fetch_from_api(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch from real eBay Trading API."""
        try:
            listings = self.api_client.search_sold_items(keyword, limit)
            logger.info(f"Fetched {len(listings)} listings from eBay API")
            return listings
        except Exception as e:
            logger.error(f"Error fetching from eBay API: {e}")
            logger.info("Falling back to sample data")
            return self._fetch_from_sample_data(keyword, limit)

    def _fetch_from_sample_data(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch from sample data (development mode)."""
        logger.debug(f"Fetching from sample data with keyword: {keyword}")

        generator = SampleDataGenerator()
        dataset = generator.generate_complete_dataset(
            item_count=10,
            ebay_records=50,
            mercari_records=0
        )

        ebay_records = dataset['ebay_records']

        keyword_lower = keyword.lower()
        filtered = [r for r in ebay_records
                   if keyword_lower in r.original_title.lower()]

        exclude_keywords = self.config.ebay_exclude_keywords
        for exclude in exclude_keywords:
            filtered = [r for r in filtered
                       if exclude.lower() not in r.original_title.lower()]

        results = []
        for record in filtered[:limit]:
            result_dict = {
                'itemId': record.record_id,
                'title': record.original_title,
                'price': {
                    'value': record.price,
                    'currency': record.currency
                },
                'shipping': {
                    'shippingCost': {
                        'value': record.shipping
                    }
                },
                'category_id': '29323',  # Default: Trading Cards
                'category_name': 'Trading Cards & Accessories',
                'soldDate': record.sold_date.isoformat() if record.sold_date else None,
                'itemWebUrl': record.listing_url,
                'condition': 'Used',
                'soldCount': 1
            }
            results.append(result_dict)

        logger.info(f"Fetched {len(results)} sample listings for keyword: {keyword}")
        return results

    def convert_to_market_records(self, raw_listings: List[Dict]) -> List[MarketRecord]:
        """
        Convert eBay API listings to internal MarketRecord format.

        Args:
            raw_listings (List[Dict]): Raw listing dictionaries from eBay.

        Returns:
            List[MarketRecord]: List of MarketRecord objects with category info.
        """
        records = []

        for listing in raw_listings:
            try:
                item_id = listing.get('itemId', f"ebay_{uuid.uuid4().hex[:8]}")
                title = listing.get('title', 'Unknown')

                price_data = listing.get('price', {})
                price = float(price_data.get('value', 0))
                currency = price_data.get('currency', 'USD')

                shipping_data = listing.get('shipping', {}).get('shippingCost', {})
                shipping = float(shipping_data.get('value', 0))

                total_price = price + shipping

                sold_date_str = listing.get('soldDate')
                sold_date = None
                if sold_date_str:
                    try:
                        sold_date = datetime.fromisoformat(sold_date_str.replace('Z', '+00:00'))
                    except:
                        sold_date = None

                # Extract category information
                category_id = listing.get('category_id', '29323')
                category_name = listing.get('category_name', 'Trading Cards & Accessories')

                record = MarketRecord(
                    record_id=f"ebay_{uuid.uuid4().hex[:8]}",
                    item_id=item_id,
                    source_site=SourceSite.EBAY,
                    search_keyword="pokemon card",
                    original_title=title,
                    normalized_title=title,
                    price=price,
                    shipping=shipping,
                    currency=currency,
                    total_price=total_price,
                    sold_flag=True,
                    active_flag=False,
                    sold_date=sold_date,
                    listing_url=listing.get('itemWebUrl', ''),
                    fetched_at=datetime.now()
                )
                
                # Store category info as custom attributes
                record.ebay_category_id = category_id
                record.ebay_category_name = category_name

                records.append(record)

            except Exception as e:
                logger.warning(f"Error converting listing {listing}: {e}")
                continue

        logger.info(f"Converted {len(records)} listings to MarketRecords")
        return records
