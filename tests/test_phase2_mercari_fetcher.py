"""
Phase 2 Mercari Fetcher Tests

Tests for the MercariFetcher class including:
- Initialization
- Sample data fetching
- Keyword filtering
- Exclusion keyword handling
- MarketRecord conversion
- Price calculations
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetcher.mercari_fetcher import MercariFetcher
from src.models.data_models import MarketRecord, SourceSite, DecisionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_mercari_initialization():
    """Test MercariFetcher initialization."""
    logger.info("\n=== Test: Mercari Initialization ===")
    
    try:
        fetcher = MercariFetcher(use_dummy_data=True)
        assert fetcher is not None
        logger.info("✓ MercariFetcher initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Initialization failed: {e}")
        return False


def test_mercari_fetch_listings():
    """Test fetching listings from Mercari."""
    logger.info("\n=== Test: Mercari Fetch Listings ===")
    
    try:
        fetcher = MercariFetcher(use_dummy_data=True)
        listings = fetcher.fetch_listings("ポケモンカード", limit=10)
        
        assert isinstance(listings, list), "Results should be a list"
        assert len(listings) > 0, "Should return at least one listing"
        assert all(isinstance(item, dict) for item in listings), "All items should be dicts"
        
        # Check required fields
        required_fields = ['item_id', 'title', 'price', 'seller_name', 'sold_date']
        for item in listings:
            for field in required_fields:
                assert field in item, f"Missing field: {field}"
        
        logger.info(f"✓ Mercari fetch returned {len(listings)} listings")
        return True
    except Exception as e:
        logger.error(f"✗ Mercari fetch test failed: {e}")
        return False


def test_mercari_keyword_filtering():
    """Test keyword filtering for Mercari listings."""
    logger.info("\n=== Test: Mercari Keyword Filtering ===")
    
    try:
        fetcher = MercariFetcher(use_dummy_data=True)
        
        # Fetch with keyword
        listings_pokemon = fetcher.fetch_listings("ポケモンカード", limit=50)
        listings_charizard = fetcher.fetch_listings("リザードン", limit=50)
        
        assert len(listings_pokemon) > 0, "Should find Pokemon card listings"
        assert len(listings_charizard) > 0, "Should find Charizard listings"
        
        logger.info(f"✓ Keyword filter: ポケモンカード={len(listings_pokemon)}, リザードン={len(listings_charizard)}")
        return True
    except Exception as e:
        logger.error(f"✗ Keyword filtering test failed: {e}")
        return False


def test_mercari_exclude_keywords():
    """Test exclusion keyword handling."""
    logger.info("\n=== Test: Mercari Exclude Keywords ===")
    
    try:
        fetcher = MercariFetcher(use_dummy_data=True)
        listings = fetcher.fetch_listings("ポケモンカード", limit=50)
        
        # Check that exclude keywords are not present
        exclude_keywords = ["スリーブ", "ボックス", "ファイル"]
        for listing in listings:
            title = listing['title'].lower()
            for exclude in exclude_keywords:
                assert exclude.lower() not in title, f"Title contains excluded keyword: {exclude}"
        
        logger.info(f"✓ Exclude keywords verified ({len(listings)} listings checked)")
        return True
    except Exception as e:
        logger.error(f"✗ Exclude keywords test failed: {e}")
        return False


def test_mercari_conversion_to_records():
    """Test conversion to MarketRecord format."""
    logger.info("\n=== Test: Mercari Conversion to MarketRecord ===")
    
    try:
        fetcher = MercariFetcher(use_dummy_data=True)
        raw_listings = fetcher.fetch_listings("ポケモンカード", limit=5)
        records = fetcher.convert_to_market_records(raw_listings)
        
        assert isinstance(records, list), "Should return a list"
        assert len(records) == len(raw_listings), "All listings should be converted"
        assert all(isinstance(r, MarketRecord) for r in records), "All should be MarketRecord objects"
        
        # Check fields
        for record in records:
            assert record.source_site == SourceSite.MERCARI, "Source should be MERCARI"
            assert record.currency == "JPY", "Currency should be JPY"
            assert record.total_price > 0, "Price should be positive"
            assert record.active_flag == True, "Mercari items are active"
        
        logger.info(f"✓ Converted {len(records)} listings to MarketRecord")
        return True
    except Exception as e:
        logger.error(f"✗ Conversion test failed: {e}")
        return False


def test_mercari_price_handling():
    """Test price calculation and range."""
    logger.info("\n=== Test: Mercari Price Handling ===")
    
    try:
        fetcher = MercariFetcher(use_dummy_data=True)
        raw_listings = fetcher.fetch_listings("ポケモンカード", limit=20)
        records = fetcher.convert_to_market_records(raw_listings)
        
        prices = [r.total_price for r in records]
        
        assert min(prices) > 0, "All prices should be positive"
        assert max(prices) < 100000, "Prices should be realistic (< 100,000 JPY)"
        
        avg_price = sum(prices) / len(prices)
        logger.info(f"✓ Price range: {min(prices):.0f} - {max(prices):.0f} JPY (avg: {avg_price:.0f} JPY)")
        return True
    except Exception as e:
        logger.error(f"✗ Price handling test failed: {e}")
        return False


def run_all_tests():
    """Run all Mercari Fetcher tests."""
    logger.info("=" * 60)
    logger.info("eBay-Research-Edge Phase 2: Mercari Fetcher Tests")
    logger.info("=" * 60)
    
    tests = [
        test_mercari_initialization,
        test_mercari_fetch_listings,
        test_mercari_keyword_filtering,
        test_mercari_exclude_keywords,
        test_mercari_conversion_to_records,
        test_mercari_price_handling,
    ]
    
    results = [test() for test in tests]
    
    logger.info("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    logger.info(f"Test Results: {passed}/{total} passed")
    logger.info("=" * 60)
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
