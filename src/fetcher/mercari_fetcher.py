"""
Mercari data fetching module.
"""

import logging
from typing import List, Dict, Any

from src.config.config import config
from src.models.data_models import MarketRecord

logger = logging.getLogger(__name__)


class MercariF​etcher:
    """Fetches domestic price data from Mercari Japan."""
    
    def __init__(self):
        self.config = config
        logger.info("MercariF​etcher initialized")
    
    def fetch_listings(self, keyword: str, limit: int = 100) -> List[Dict]:
        logger.info(f"Fetching Mercari listings for: {keyword}")
        return []
    
    def convert_to_market_records(self, raw_listings: List[Dict]) -> List[MarketRecord]:
        logger.info("Converting Mercari listings to MarketRecords")
        return []
