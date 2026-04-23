"""
Phase 2 tests for eBay Fetcher implementation.

Tests the eBayFetcher's ability to:
1. Fetch sample data (development mode)
2. Convert to MarketRecord format
3. Filter by keyword
4. Apply exclude keywords
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetcher.ebay_fetcher import eBayFetcher
from src.models.data_models import SourceSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ebay_fetcher_initialization():
    """
    Test eBayFetcher initialization in development mode.
    """
    logger.info("\n=== Test 1: Initialization ===\n")
    
    # Development mode
    fetcher_dev = eBayFetcher(use_real_api=False)
    assert fetcher_dev.use_real_api == False, "Should be in development mode"
    
    # Production mode (not yet available)
    fetcher_prod = eBayFetcher(use_real_api=True)
    assert fetcher_prod.use_real_api == True, "Should be in production mode"
    
    logger.info("✓ eBayFetcher initialized correctly\n")


def test_fetch_from_sample_data():
    """
    Test fetching sample data with keyword filtering.
    """
    logger.info("\n=== Test 2: Fetch from Sample Data ===\n")
    
    fetcher = eBayFetcher(use_real_api=False)
    
    # Fetch with keyword
    listings = fetcher.fetch_sold_listings("pokemon card", limit=10)
    
    assert len(listings) > 0, "Should return sample listings"
    assert len(listings) <= 10, "Should respect limit parameter"
    
    # Verify structure
    for listing in listings:
        assert 'itemId' in listing, "Missing itemId"
        assert 'title' in listing, "Missing title"
        assert 'price' in listing, "Missing price"
        assert 'shipping' in listing, "Missing shipping"
        assert 'soldDate' in listing, "Missing soldDate"
        assert 'itemWebUrl' in listing, "Missing itemWebUrl"
    
    logger.info(f"✓ Fetched {len(listings)} sample listings")
    logger.info(f"✓ All listings have required fields\n")


def test_keyword_filtering():
    """
    Test that keyword filtering works correctly.
    """
    logger.info("\n=== Test 3: Keyword Filtering ===\n")
    
    fetcher = eBayFetcher(use_real_api=False)
    
    # Fetch with specific keyword
    listings_specific = fetcher.fetch_sold_listings("Charizard", limit=100)
    
    # Verify all results contain the keyword (case-insensitive)
    for listing in listings_specific:
        title_lower = listing['title'].lower()
        assert "charizard" in title_lower, f"Keyword not in title: {listing['title']}"
    
    logger.info(f"✓ Keyword filtering works correctly")
    logger.info(f"✓ Fetched {len(listings_specific)} listings matching 'Charizard'\n")


def test_convert_to_market_records():
    """
    Test conversion from raw API format to MarketRecord.
    """
    logger.info("\n=== Test 4: Conversion to MarketRecord ===\n")
    
    fetcher = eBayFetcher(use_real_api=False)
    
    # Fetch raw listings
    raw_listings = fetcher.fetch_sold_listings("pokemon card", limit=5)
    
    # Convert to MarketRecords
    records = fetcher.convert_to_market_records(raw_listings)
    
    assert len(records) == len(raw_listings), "Should convert all listings"
    
    # Verify record structure
    for record in records:
        assert record.record_id, "Missing record_id"
        assert record.original_title, "Missing original_title"
        assert record.price > 0, "Price should be positive"
        assert record.total_price >= record.price, "Total price should include shipping"
        assert record.source_site == SourceSite.EBAY, "Should be eBay source"
        assert record.sold_flag == True, "Should be marked as sold"
        assert record.currency == "USD", "Currency should be USD"
    
    logger.info(f"✓ Converted {len(records)} to MarketRecords")
    logger.info(f"✓ All records have correct structure\n")


def test_price_handling():
    """
    Test that price and shipping are handled correctly.
    """
    logger.info("\n=== Test 5: Price Handling ===\n")
    
    fetcher = eBayFetcher(use_real_api=False)
    
    raw_listings = fetcher.fetch_sold_listings("pokemon card", limit=5)
    records = fetcher.convert_to_market_records(raw_listings)
    
    for record in records:
        # Verify price calculation
        expected_total = record.price + record.shipping
        assert record.total_price == expected_total, \
            f"Total price mismatch: {record.total_price} != {expected_total}"
        
        # Verify reasonable price ranges
        assert 0 < record.price < 200, "Price outside expected range"
        assert 0 <= record.shipping < 30, "Shipping outside expected range"
    
    logger.info(f"✓ Price calculations correct")
    logger.info(f"✓ Price ranges are realistic\n")


def test_exclude_keywords():
    """
    Test that exclude keywords are applied.
    """
    logger.info("\n=== Test 6: Exclude Keywords ===\n")
    
    fetcher = eBayFetcher(use_real_api=False)
    
    # Fetch listings (which should exclude certain items)
    listings = fetcher.fetch_sold_listings("pokemon card", limit=100)
    
    # Check that excluded keywords are not present
    exclude_keywords = ["storage box", "binder", "sleeve"]
    for listing in listings:
        title_lower = listing['title'].lower()
        for exclude in exclude_keywords:
            assert exclude not in title_lower, \
                f"Excluded keyword '{exclude}' found in: {listing['title']}"
    
    logger.info(f"✓ Exclude keywords applied correctly")
    logger.info(f"✓ Retrieved {len(listings)} listings without excluded items\n")


def run_all_tests():
    """
    Run all eBay Fetcher tests.
    """
    logger.info("\n" + "="*60)
    logger.info("=== Phase 2: eBay Fetcher Tests ===")
    logger.info("="*60 + "\n")
    
    try:
        test_ebay_fetcher_initialization()
        test_fetch_from_sample_data()
        test_keyword_filtering()
        test_convert_to_market_records()
        test_price_handling()
        test_exclude_keywords()
        
        logger.info("="*60)
        logger.info("=== All eBay Fetcher Tests PASSED ===")
        logger.info("="*60 + "\n")
        
        return True
    
    except AssertionError as e:
        logger.error(f"\n✗ Test Failed: {e}\n")
        return False
    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}\n", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
