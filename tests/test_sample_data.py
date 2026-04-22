"""
Tests for sample data generator.

This module tests the SampleDataGenerator to ensure it produces
realistic and consistent sample data.
"""

import logging
from tests.sample_data_generator import SampleDataGenerator
from src.models.data_models import SourceSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_generate_items():
    """
    Test that sample items are generated correctly.
    
    Verifies:
    - Correct number of items generated
    - All items have unique item_ids
    - All items have normalized names
    - Franchise is 'Pokemon'
    """
    generator = SampleDataGenerator()
    items = generator.generate_items(count=5)
    
    assert len(items) == 5, f"Expected 5 items, got {len(items)}"
    
    item_ids = [item.item_id for item in items]
    assert len(set(item_ids)) == len(item_ids), "Item IDs are not unique"
    
    assert all(item.franchise == "Pokemon" for item in items), "Not all items have franchise='Pokemon'"
    assert all(item.category == "pokemon_card" for item in items), "Not all items have category='pokemon_card'"
    
    logger.info("✓ test_generate_items passed")


def test_generate_ebay_records():
    """
    Test that eBay records are generated correctly.
    
    Verifies:
    - Correct number of records
    - All records have source_site=EBAY
    - sold_flag=True and active_flag=False
    - Currency is USD
    - Prices are in expected range
    """
    generator = SampleDataGenerator()
    items = generator.generate_items(count=3)
    records = generator.generate_ebay_records(items, count=10)
    
    assert len(records) == 10, f"Expected 10 records, got {len(records)}"
    assert all(r.source_site == SourceSite.EBAY for r in records), "Not all records are from eBay"
    assert all(r.sold_flag for r in records), "Not all records marked as sold"
    assert all(not r.active_flag for r in records), "Some records marked as active"
    assert all(r.currency == "USD" for r in records), "Not all records in USD"
    
    # Check price range
    prices = [r.price for r in records]
    assert all(29.99 <= p <= 99.99 for p in prices), "Some prices outside expected range"
    
    logger.info("✓ test_generate_ebay_records passed")


def test_generate_mercari_records():
    """
    Test that Mercari records are generated correctly.
    
    Verifies:
    - Correct number of records
    - All records have source_site=MERCARI
    - sold_flag=True and active_flag=False
    - Currency is JPY
    - Prices are in expected range
    """
    generator = SampleDataGenerator()
    items = generator.generate_items(count=3)
    records = generator.generate_mercari_records(items, count=10)
    
    assert len(records) == 10, f"Expected 10 records, got {len(records)}"
    assert all(r.source_site == SourceSite.MERCARI for r in records), "Not all records are from Mercari"
    assert all(r.sold_flag for r in records), "Not all records marked as sold"
    assert all(not r.active_flag for r in records), "Some records marked as active"
    assert all(r.currency == "JPY" for r in records), "Not all records in JPY"
    
    # Check price range
    prices = [r.price for r in records]
    assert all(1500 <= p <= 8000 for p in prices), "Some prices outside expected range"
    
    logger.info("✓ test_generate_mercari_records passed")


def test_generate_complete_dataset():
    """
    Test that a complete dataset is generated correctly.
    
    Verifies:
    - All components are generated
    - Correct counts of each component
    - Records are properly associated with items
    """
    generator = SampleDataGenerator()
    dataset = generator.generate_complete_dataset(
        item_count=3,
        ebay_records=10,
        mercari_records=8
    )
    
    assert 'items' in dataset, "Missing 'items' in dataset"
    assert 'ebay_records' in dataset, "Missing 'ebay_records' in dataset"
    assert 'mercari_records' in dataset, "Missing 'mercari_records' in dataset"
    assert 'all_records' in dataset, "Missing 'all_records' in dataset"
    
    assert len(dataset['items']) == 3, f"Expected 3 items, got {len(dataset['items'])}"
    assert len(dataset['ebay_records']) == 10, f"Expected 10 eBay records, got {len(dataset['ebay_records'])}"
    assert len(dataset['mercari_records']) == 8, f"Expected 8 Mercari records, got {len(dataset['mercari_records'])}"
    assert len(dataset['all_records']) == 18, f"Expected 18 total records, got {len(dataset['all_records'])}"
    
    # Verify all records reference valid items
    item_ids = {item.item_id for item in dataset['items']}
    record_item_ids = {record.item_id for record in dataset['all_records']}
    assert record_item_ids.issubset(item_ids), "Some records reference non-existent items"
    
    logger.info("✓ test_generate_complete_dataset passed")


def run_all_tests():
    """
    Run all sample data tests.
    """
    logger.info("\n=== Running Sample Data Generator Tests ===\n")
    
    try:
        test_generate_items()
        test_generate_ebay_records()
        test_generate_mercari_records()
        test_generate_complete_dataset()
        
        logger.info("\n=== All Tests Passed! ===\n")
        return True
    except AssertionError as e:
        logger.error(f"\n✗ Test Failed: {e}\n")
        return False
    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
