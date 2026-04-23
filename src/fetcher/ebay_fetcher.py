"""
eBay data fetching module.

This module provides the eBayFetcher class for retrieving sold listing data
from eBay (or sample data as a fallback during development).

Classes:
    eBayFetcher: Fetches and converts eBay sold listing data.

Global Variables:
    logger: Logging object for this module.
"""

import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random

from src.config.config import config
from src.models.data_models import MarketRecord, SourceSite
from tests.sample_data_generator import SampleDataGenerator

logger = logging.getLogger(__name__)


class eBayFetcher:
    """
    Fetches sold listing data from eBay.
    
    During development (API not available), uses sample data.
    Once eBay API is approved, switch to real API by setting use_real_api=True.
    
    Attributes:
        use_real_api (bool): If True, use real eBay API. If False, use sample data.
        api_key (str): eBay API key (from environment).
        api_secret (str): eBay API secret (from environment).
        config (Config): Configuration object.
    
    Example:
        >>> # Development mode (sample data)
        >>> fetcher = eBayFetcher(use_real_api=False)
        >>> listings = fetcher.fetch_sold_listings("pokemon card")
        
        >>> # Production mode (real API)
        >>> fetcher = eBayFetcher(use_real_api=True)
        >>> listings = fetcher.fetch_sold_listings("pokemon card")
    """
    
    def __init__(self, use_real_api: bool = False):
        """
        Initialize the eBay fetcher.
        
        Args:
            use_real_api (bool): If True, use real eBay API.
                                If False, use sample data (development mode).
        """
        self.use_real_api = use_real_api
        self.api_key = None  # TODO: Load from environment variable
        self.api_secret = None  # TODO: Load from environment variable
        self.config = config
        
        if use_real_api:
            logger.info("eBayFetcher initialized in PRODUCTION mode (real API)")
        else:
            logger.info("eBayFetcher initialized in DEVELOPMENT mode (sample data)")
    
    def fetch_sold_listings(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch sold listings from eBay for a given keyword.
        
        During development, returns filtered sample data.
        Once API is available, fetches from real eBay API.
        
        Args:
            keyword (str): Search keyword (e.g., "pokemon card charizard").
            limit (int): Maximum number of results to retrieve (default: 100).
        
        Returns:
            List[Dict[str, Any]]: List of listing data dictionaries.
                                 Structure matches eBay API item_summary response.
        
        Algorithm:
            1. If use_real_api=True:
               - Build API request with keyword and Sold filter
               - Execute API call
               - Parse and return results
            2. If use_real_api=False (development):
               - Generate sample data
               - Filter by keyword
               - Return filtered data
        
        Example:
            >>> fetcher = eBayFetcher(use_real_api=False)
            >>> listings = fetcher.fetch_sold_listings("pokemon card", limit=20)
            >>> len(listings)
            20
        
        Notes:
            - During development, keyword filtering is basic
            - Real API will have more sophisticated filtering
            - Results are always in consistent format
        """
        logger.info(f"Fetching eBay sold listings for: {keyword}")
        
        if self.use_real_api:
            return self._fetch_from_api(keyword, limit)
        else:
            return self._fetch_from_sample_data(keyword, limit)
    
    def _fetch_from_api(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch from real eBay API.
        
        Args:
            keyword (str): Search keyword.
            limit (int): Result limit.
        
        Returns:
            List[Dict[str, Any]]: API results.
        
        Notes:
            TODO: Implement when API is approved.
            Required steps:
            1. Authenticate with OAuth 2.0
            2. Build Browse API request with Sold filter
            3. Apply keyword and exclude_keywords filters
            4. Save raw response to data/raw/
            5. Parse and return results
        """
        logger.info("Fetching from real eBay API (not yet implemented)")
        # TODO: Implement real API call
        return []
    
    def _fetch_from_sample_data(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """
        Fetch from sample data (development mode).
        
        Generates sample data on-the-fly and filters by keyword.
        
        Args:
            keyword (str): Search keyword.
            limit (int): Result limit.
        
        Returns:
            List[Dict[str, Any]]: Filtered sample data in API format.
        
        Algorithm:
            1. Generate sample eBay records using SampleDataGenerator
            2. Filter records where keyword appears in title (case-insensitive)
            3. Apply exclude_keywords filter
            4. Convert to API format (Dict)
            5. Limit to requested count
            6. Return results
        """
        logger.debug(f"Fetching from sample data with keyword: {keyword}")
        
        # Generate sample data
        generator = SampleDataGenerator()
        # Generate more records for variety
        dataset = generator.generate_complete_dataset(
            item_count=10,
            ebay_records=50,
            mercari_records=0  # Only eBay for this method
        )
        
        ebay_records = dataset['ebay_records']
        
        # Filter by keyword (case-insensitive)
        keyword_lower = keyword.lower()
        filtered = [r for r in ebay_records 
                   if keyword_lower in r.original_title.lower()]
        
        # Apply exclude keywords from config
        exclude_keywords = self.config.ebay_exclude_keywords
        for exclude in exclude_keywords:
            filtered = [r for r in filtered 
                       if exclude.lower() not in r.original_title.lower()]
        
        # Convert to dict format (simulating API response)
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
                'soldDate': record.sold_date.isoformat() if record.sold_date else None,
                'itemWebUrl': record.listing_url,
                'condition': 'Used',  # Sample data
                'soldCount': 1  # Sample data
            }
            results.append(result_dict)
        
        logger.info(f"Fetched {len(results)} sample listings for keyword: {keyword}")
        return results
    
    def convert_to_market_records(self, raw_listings: List[Dict]) -> List[MarketRecord]:
        """
        Convert eBay API listings to internal MarketRecord format.
        
        Transforms raw eBay listing data (whether from real API or sample)
        into standardized MarketRecord objects.
        
        Args:
            raw_listings (List[Dict]): Raw listing dictionaries from eBay.
                                      Expected keys: itemId, title, price, shipping,
                                                     soldDate, itemWebUrl, etc.
        
        Returns:
            List[MarketRecord]: List of MarketRecord objects.
        
        Algorithm:
            1. For each raw_listing:
               a. Generate unique record_id
               b. Extract and map fields:
                  - original_title from listing title
                  - price from listing.price.value
                  - shipping from listing.shipping.shippingCost.value
                  - currency from listing.price.currency
                  - total_price = price + shipping
                  - sold_flag = True (we fetch sold items)
                  - active_flag = False (completed listings)
                  - sold_date from listing.soldDate
                  - listing_url from listing.itemWebUrl
               c. Create MarketRecord instance
               d. Add to results list
            2. Return results
        
        Example:
            >>> raw = [
            ...     {
            ...         'itemId': '123456789',
            ...         'title': 'Pokemon Card Charizard EX',
            ...         'price': {'value': 49.99, 'currency': 'USD'},
            ...         'shipping': {'shippingCost': {'value': 5.00}},
            ...         'soldDate': '2024-04-15T10:30:00',
            ...         'itemWebUrl': 'https://ebay.com/itm/123456789'
            ...     }
            ... ]
            >>> records = fetcher.convert_to_market_records(raw)
            >>> print(records[0].total_price)
            54.99
        """
        records = []
        
        for listing in raw_listings:
            try:
                # Extract data with safe defaults
                item_id = listing.get('itemId', f"ebay_{uuid.uuid4().hex[:8]}")
                title = listing.get('title', 'Unknown')
                
                # Price extraction
                price_data = listing.get('price', {})
                price = float(price_data.get('value', 0))
                currency = price_data.get('currency', 'USD')
                
                # Shipping extraction
                shipping_data = listing.get('shipping', {}).get('shippingCost', {})
                shipping = float(shipping_data.get('value', 0))
                
                total_price = price + shipping
                
                # Date extraction
                sold_date_str = listing.get('soldDate')
                sold_date = None
                if sold_date_str:
                    try:
                        sold_date = datetime.fromisoformat(sold_date_str.replace('Z', '+00:00'))
                    except:
                        sold_date = None
                
                # Create MarketRecord
                record = MarketRecord(
                    record_id=f"ebay_{uuid.uuid4().hex[:8]}",
                    item_id=item_id,
                    source_site=SourceSite.EBAY,
                    search_keyword="pokemon card",  # TODO: Pass as parameter
                    original_title=title,
                    normalized_title=title,  # Will be normalized later
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
                records.append(record)
            
            except Exception as e:
                logger.warning(f"Error converting listing {listing}: {e}")
                continue
        
        logger.info(f"Converted {len(records)} listings to MarketRecords")
        return records
