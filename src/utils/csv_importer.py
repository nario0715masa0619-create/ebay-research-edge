"""
CSV importer module for multi-source data import.

This module provides utilities to import CSV files from various sources
(Amazon, Yahoo Auction, Yahoo Shopping, Yahoo Fril, Rakuten) and convert
them to a standardized MarketRecord format.

Classes:
    CSVImporter: Main importer class with source-specific parsers.

Global Variables:
    logger: Logging object for this module.
"""

import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from pathlib import Path

from src.models.data_models import MarketRecord, SourceSite
from src.config.config import config

logger = logging.getLogger(__name__)


class CSVImporter:
    """
    Imports CSV files from various sources and converts to MarketRecord format.
    
    Attributes:
        config (Config): Configuration object.
        source_site (SourceSite): Data source type.
    
    Methods:
        import_csv: Main method to import CSV file.
        parse_amazon_csv: Parse Amazon CSV format.
        parse_yahoo_auction_csv: Parse Yahoo Auction CSV format.
        parse_yahoo_shopping_csv: Parse Yahoo Shopping CSV format.
        parse_yahoo_fril_csv: Parse Yahoo Fril CSV format.
        parse_rakuten_csv: Parse Rakuten CSV format.
    """
    
    def __init__(self):
        """Initialize the CSV importer."""
        self.config = config
        logger.info("CSVImporter initialized")
    
    def import_csv(self, file_path: str, source_site: str) -> List[MarketRecord]:
        """
        Import CSV file and convert to MarketRecord list.
        
        Args:
            file_path (str): Path to CSV file.
            source_site (str): Source site name (amazon, yahoo_auction, etc).
        
        Returns:
            List[MarketRecord]: List of converted records.
        
        Raises:
            FileNotFoundError: If CSV file does not exist.
            ValueError: If source_site is not recognized.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        logger.info(f"Importing CSV from {source_site}: {file_path}")
        
        try:
            if source_site.lower() == "amazon":
                raw_listings = self._parse_amazon_csv(file_path)
            elif source_site.lower() == "yahoo_auction":
                raw_listings = self._parse_yahoo_auction_csv(file_path)
            elif source_site.lower() == "yahoo_shopping":
                raw_listings = self._parse_yahoo_shopping_csv(file_path)
            elif source_site.lower() == "yahoo_fril":
                raw_listings = self._parse_yahoo_fril_csv(file_path)
            elif source_site.lower() == "rakuten":
                raw_listings = self._parse_rakuten_csv(file_path)
            else:
                raise ValueError(f"Unknown source site: {source_site}")
            
            records = self._convert_to_market_records(raw_listings, source_site)
            logger.info(f"Imported {len(records)} records from {file_path}")
            
            return records
        
        except Exception as e:
            logger.error(f"Error importing CSV: {e}", exc_info=True)
            raise
    
    def _parse_amazon_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse Amazon CSV format.
        
        Expected columns: 商品名, 価格, 送料, URL
        """
        listings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    title = row.get('商品名') or row.get('Product') or row.get('Title') or ''
                    price_str = row.get('価格') or row.get('Price') or '0'
                    shipping_str = row.get('送料') or row.get('Shipping') or '0'
                    url = row.get('URL') or row.get('Url') or ''
                    
                    price = self._parse_price(price_str)
                    shipping = self._parse_price(shipping_str)
                    
                    listings.append({
                        'title': title,
                        'price': price,
                        'shipping': shipping,
                        'url': url,
                    })
            
            logger.info(f"Parsed {len(listings)} listings from Amazon CSV")
            return listings
        
        except Exception as e:
            logger.error(f"Error parsing Amazon CSV: {e}")
            return []
    
    def _parse_yahoo_auction_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Yahoo Auction CSV format."""
        listings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    title = row.get('タイトル') or row.get('Title') or ''
                    price_str = row.get('落札価格') or row.get('Price') or '0'
                    shipping_str = row.get('送料') or row.get('Shipping') or '0'
                    url = row.get('URL') or row.get('Url') or ''
                    
                    price = self._parse_price(price_str)
                    shipping = self._parse_price(shipping_str)
                    
                    listings.append({
                        'title': title,
                        'price': price,
                        'shipping': shipping,
                        'url': url,
                    })
            
            logger.info(f"Parsed {len(listings)} listings from Yahoo Auction CSV")
            return listings
        
        except Exception as e:
            logger.error(f"Error parsing Yahoo Auction CSV: {e}")
            return []
    
    def _parse_yahoo_shopping_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Yahoo Shopping CSV format."""
        return self._parse_yahoo_auction_csv(file_path)
    
    def _parse_yahoo_fril_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Yahoo Fril CSV format."""
        return self._parse_yahoo_auction_csv(file_path)
    
    def _parse_rakuten_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Parse Rakuten CSV format."""
        return self._parse_amazon_csv(file_path)
    
    def _parse_price(self, price_str: str) -> float:
        """
        Parse price string and return float.
        
        Handles: 1,234円, ¥1234, etc.
        """
        if not price_str or price_str.strip() == '':
            return 0.0
        
        price_str = price_str.replace('円', '').replace('¥', '').replace('$', '').replace(',', '').strip()
        
        try:
            return float(price_str)
        except ValueError:
            logger.warning(f"Could not parse price: {price_str}")
            return 0.0
    
    def _convert_to_market_records(self, raw_listings: List[Dict], source_site: str) -> List[MarketRecord]:
        """Convert parsed listings to MarketRecord format."""
        records = []
        source_enum = SourceSite[source_site.upper()]
        
        for listing in raw_listings:
            try:
                record = MarketRecord(
                    record_id=f"csv_{uuid.uuid4().hex[:8]}",
                    item_id=f"item_{uuid.uuid4().hex[:8]}",
                    source_site=source_enum,
                    search_keyword="csv_import",
                    original_title=listing.get('title', ''),
                    normalized_title=listing.get('title', ''),
                    price=listing.get('price', 0.0),
                    shipping=listing.get('shipping', 0.0),
                    currency='JPY',
                    total_price=listing.get('price', 0.0) + listing.get('shipping', 0.0),
                    sold_flag=False,
                    active_flag=True,
                    listing_url=listing.get('url'),
                    fetched_at=datetime.now(),
                )
                records.append(record)
            except Exception as e:
                logger.warning(f"Failed to convert listing: {e}")
                continue
        
        return records
