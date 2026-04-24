"""
Yahoo Fril (フリマ) Japan data fetching module.
"""

import logging
from typing import List, Dict, Any

from src.config.config import config
from src.models.data_models import MarketRecord, SourceSite

logger = logging.getLogger(__name__)


class YahooFrilFetcher:
    """Fetches price data from Yahoo Fril Japan."""
    
    def __init__(self, use_dummy_data: bool = True):
        self.config = config
        self.use_dummy_data = use_dummy_data
        logger.info(f"YahooFrilFetcher initialized (use_dummy_data={use_dummy_data})")
    
    def fetch_listings(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        logger.info(f"Fetching Yahoo Fril listings for: {keyword}")
        logger.warning("Yahoo Fril fetcher: Not yet implemented")
        return []
    
    def convert_to_market_records(self, raw_listings: List[Dict[str, Any]]) -> List[MarketRecord]:
        logger.warning("Yahoo Fril conversion not yet implemented")
        return []
