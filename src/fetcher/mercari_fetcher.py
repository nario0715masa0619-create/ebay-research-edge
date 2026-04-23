"""
Mercari data fetching module.

This module provides the MercariFetcher class for retrieving price data
from Mercari Japan marketplace.

Classes:
    MercariFetcher: Fetches and converts Mercari listing data.

Global Variables:
    logger: Logging object for this module.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid
import random

from src.config.config import config
from src.models.data_models import MarketRecord, SourceSite

logger = logging.getLogger(__name__)

# Pokemon card product names for dummy data
POKEMON_CARDS = [
    "Pokemon Card Charizard EX Holo",
    "Pokemon Card Blastoise VMAX Secret",
    "Pokemon Card Venusaur EX",
    "Pokemon Card Pikachu Promo",
    "Pokemon Card Dragonite EX Holo",
]

MERCARI_PRICE_RANGE = (1500, 8000)  # JPY


class MercariFetcher:
    """
    Fetches domestic price data from Mercari Japan.
    
    Attributes:
        config (Config): Configuration object.
        use_dummy_data (bool): Whether to use dummy data instead of real API.
    
    Methods:
        fetch_listings: Fetch listings for a keyword.
        convert_to_market_records: Convert raw listings to MarketRecord format.
    
    Example:
        >>> fetcher = MercariFetcher(use_dummy_data=True)
        >>> listings = fetcher.fetch_listings("pokemon card")
        >>> records = fetcher.convert_to_market_records(listings)
    """
    
    def __init__(self, use_dummy_data: bool = True):
        """
        Initialize the Mercari fetcher.
        
        Args:
            use_dummy_data (bool): If True, generate dummy data. If False, use real API (TODO).
        """
        self.config = config
        self.use_dummy_data = use_dummy_data
        self.api_key = None
        
        logger.info(f"MercariFetcher initialized (use_dummy_data={use_dummy_data})")
    
    def fetch_listings(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch listings from Mercari for a given keyword.
        
        Args:
            keyword (str): Search keyword (e.g., 'ポケモンカード').
            limit (int): Maximum number of results. Default: 100.
        
        Returns:
            List[Dict[str, Any]]: List of listing dictionaries with keys:
                - item_id (str)
                - title (str)
                - price (float)
                - seller_name (str)
                - sold_date (str, ISO format)
                - listing_url (str)
                - condition (str)
        
        Raises:
            ValueError: If keyword is empty.
        
        Notes:
            Currently uses dummy data. Future implementation will support:
            1. Web scraping via BeautifulSoup
            2. Mercari official API (if approved)
            3. CSV import
        """
        if not keyword:
            raise ValueError("Keyword cannot be empty")
        
        logger.info(f"Fetching Mercari listings for: {keyword}")
        
        if self.use_dummy_data:
            return self._generate_dummy_listings(keyword, limit)
        else:
            logger.warning("Real Mercari API not yet implemented")
            return []
    
    def _generate_dummy_listings(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """
        Generate dummy Mercari listings for testing.
        
        Args:
            keyword (str): Search keyword.
            limit (int): Number of listings to generate.
        
        Returns:
            List[Dict]: Dummy listing data.
        """
        listings = []
        mercari_keywords = self.config.mercari_keywords
        exclude_keywords = self.config.mercari_exclude_keywords
        
        # Filter products by keyword
        matching_products = [
            p for p in POKEMON_CARDS
            if any(kw.lower() in p.lower() or keyword.lower() in p.lower()
                   for kw in mercari_keywords)
        ]
        
        if not matching_products:
            matching_products = POKEMON_CARDS
        
        for i in range(limit):
            product = random.choice(matching_products)
            
            # Skip if contains exclude keywords
            if any(excl.lower() in product.lower() for excl in exclude_keywords):
                continue
            
            listing = {
                'item_id': f"mercari_{uuid.uuid4().hex[:8]}",
                'title': product,
                'price': random.randint(*MERCARI_PRICE_RANGE),
                'seller_name': f"seller_{random.randint(1000, 9999)}",
                'sold_date': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'listing_url': f"https://jp.mercari.com/item/{uuid.uuid4().hex[:16]}",
                'condition': random.choice(['新品未使用', '未使用に近い', '目立つ傷や汚れなし', '傷や汚れあり']),
            }
            listings.append(listing)
        
        logger.info(f"Generated {len(listings)} dummy Mercari listings")
        return listings
    
    def convert_to_market_records(self, raw_listings: List[Dict[str, Any]]) -> List[MarketRecord]:
        """
        Convert Mercari listings to MarketRecord format.
        
        Args:
            raw_listings (List[Dict]): Raw Mercari listing data.
        
        Returns:
            List[MarketRecord]: List of MarketRecord objects.
        
        Notes:
            - All Mercari items are treated as active (not sold).
            - Currency is always JPY.
            - Shipping is estimated or omitted (Mercari seller typically covers).
        """
        records = []
        
        for listing in raw_listings:
            try:
                record = MarketRecord(
                    record_id=f"rec_{uuid.uuid4().hex[:8]}",
                    item_id=listing.get('item_id'),
                    source_site=SourceSite.MERCARI,
                    search_keyword='pokemon card',
                    original_title=listing.get('title', ''),
                    normalized_title=listing.get('title', ''),
                    price=float(listing.get('price', 0)),
                    shipping=0.0,
                    currency='JPY',
                    total_price=float(listing.get('price', 0)),
                    sold_flag=False,
                    active_flag=True,
                    sold_date=None,
                    listing_url=listing.get('listing_url'),
                    fetched_at=datetime.now(),
                )
                records.append(record)
            except Exception as e:
                logger.warning(f"Failed to convert listing {listing.get('item_id')}: {e}")
                continue
        
        logger.info(f"Converted {len(records)} Mercari listings to MarketRecord")
        return records
