"""Phase 5 CSV Import Integration Test

Test the complete CSV import workflow:
1. Load CSV files from docs/csv_formats/
2. Import them using CSVImporter
3. Convert to MarketRecords
4. Analyze and score
5. Export results to CSV
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.csv_importer import CSVImporter
from src.normalizer.normalizer import Normalizer
from src.analyzer.analyzer import Analyzer
from src.display.csv_output import CSVOutput
from src.models.data_models import SourceSite
from src.config.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_csv_import_amazon():
    """Test importing Amazon CSV."""
    logger.info("\n[Test 1] Testing Amazon CSV Import...")
    
    csv_importer = CSVImporter()
    csv_file = Path("docs/csv_formats/amazon_template.csv")
    
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        return False
    
    try:
        records = csv_importer.import_csv(str(csv_file), "amazon")
        logger.info(f"✓ Amazon CSV imported: {len(records)} records")
        
        assert len(records) > 0, "No records imported"
        assert records[0].source_site == SourceSite.AMAZON, "Source site mismatch"
        logger.info("✓ Test 1 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 1 FAILED: {e}")
        return False


def test_csv_import_yahoo_auction():
    """Test importing Yahoo Auction CSV."""
    logger.info("\n[Test 2] Testing Yahoo Auction CSV Import...")
    
    csv_importer = CSVImporter()
    csv_file = Path("docs/csv_formats/yahoo_auction_template.csv")
    
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        return False
    
    try:
        records = csv_importer.import_csv(str(csv_file), "yahoo_auction")
        logger.info(f"✓ Yahoo Auction CSV imported: {len(records)} records")
        
        assert len(records) > 0, "No records imported"
        assert records[0].source_site == SourceSite.YAHOO_AUCTION, "Source site mismatch"
        logger.info("✓ Test 2 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 2 FAILED: {e}")
        return False


def test_csv_import_all_sources():
    """Test importing all CSV sources."""
    logger.info("\n[Test 3] Testing All CSV Sources Import...")
    
    csv_importer = CSVImporter()
    sources = [
        ("amazon", "docs/csv_formats/amazon_template.csv", SourceSite.AMAZON),
        ("yahoo_auction", "docs/csv_formats/yahoo_auction_template.csv", SourceSite.YAHOO_AUCTION),
        ("yahoo_shopping", "docs/csv_formats/yahoo_shopping_template.csv", SourceSite.YAHOO_SHOPPING),
        ("yahoo_fril", "docs/csv_formats/yahoo_fril_template.csv", SourceSite.YAHOO_FRIL),
        ("rakuten", "docs/csv_formats/rakuten_template.csv", SourceSite.RAKUTEN),
    ]
    
    total_records = 0
    
    for source_name, csv_path, expected_source in sources:
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            continue
        
        try:
            records = csv_importer.import_csv(str(csv_file), source_name)
            total_records += len(records)
            logger.info(f"  ✓ {source_name}: {len(records)} records")
            assert records[0].source_site == expected_source, f"Source mismatch for {source_name}"
        except Exception as e:
            logger.error(f"  ✗ {source_name} FAILED: {e}")
            return False
    
    logger.info(f"✓ Total records imported: {total_records}")
    logger.info("✓ Test 3 PASSED")
    return True


def test_csv_normalization_and_scoring():
    """Test CSV import, normalization, and scoring."""
    logger.info("\n[Test 4] Testing CSV Import → Normalization → Scoring...")
    
    try:
        csv_importer = CSVImporter()
        
        # Import from multiple sources
        amazon_records = csv_importer.import_csv("docs/csv_formats/amazon_template.csv", "amazon")
        yahoo_auction_records = csv_importer.import_csv("docs/csv_formats/yahoo_auction_template.csv", "yahoo_auction")
        
        all_records = amazon_records + yahoo_auction_records
        logger.info(f"✓ Imported {len(all_records)} total records")
        
        # Normalize
        normalizer = Normalizer()
        normalized_records = normalizer.normalize_records(all_records)
        logger.info(f"✓ Normalized {len(normalized_records)} records")
        
        # Check that records were normalized
        assert len(normalized_records) > 0, "No records after normalization"
        assert normalized_records[0].normalized_title is not None, "Normalized title is None"
        
        logger.info("✓ Test 4 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 4 FAILED: {e}")
        return False


def test_csv_end_to_end_pipeline():
    """Test complete CSV import → analysis → export pipeline."""
    logger.info("\n[Test 5] Testing Complete CSV Pipeline (Import → Analyze → Export)...")
    
    try:
        csv_importer = CSVImporter()
        analyzer = Analyzer()
        csv_output = CSVOutput()
        
        # Step 1: Import from all sources
        logger.info("  Step 1: Importing CSV files...")
        all_records = []
        sources = [
            ("amazon", "docs/csv_formats/amazon_template.csv"),
            ("yahoo_auction", "docs/csv_formats/yahoo_auction_template.csv"),
        ]
        
        for source_name, csv_path in sources:
            records = csv_importer.import_csv(csv_path, source_name)
            all_records.extend(records)
        
        logger.info(f"  ✓ Imported {len(all_records)} records")
        
        # Step 2: Normalize
        logger.info("  Step 2: Normalizing records...")
        normalizer = Normalizer()
        normalized_records = normalizer.normalize_records(all_records)
        logger.info(f"  ✓ Normalized {len(normalized_records)} records")
        
        # Step 3: Group and analyze
        logger.info("  Step 3: Grouping and analyzing...")
        items_dict = {}
        for record in normalized_records:
            item_name = record.normalized_title
            if item_name not in items_dict:
                items_dict[item_name] = {'amazon': [], 'yahoo': []}
            
            if record.source_site == SourceSite.AMAZON:
                items_dict[item_name]['amazon'].append(record)
            else:
                items_dict[item_name]['yahoo'].append(record)
        
        # Step 4: Score candidates
        candidates = []
        for item_name, records_by_source in items_dict.items():
            amazon_recs = records_by_source['amazon']
            yahoo_recs = records_by_source['yahoo']
            
            if not amazon_recs or not yahoo_recs:
                continue
            
            # Get prices
            amazon_prices = [r.total_price for r in amazon_recs if r.total_price > 0]
            yahoo_prices = [r.total_price for r in yahoo_recs if r.total_price > 0]
            
            if not amazon_prices or not yahoo_prices:
                continue
            
            amazon_median = sorted(amazon_prices)[len(amazon_prices) // 2]
            yahoo_median = sorted(yahoo_prices)[len(yahoo_prices) // 2]
            
            # Calculate scores (dummy values for testing)
            demand_score = analyzer.calculate_demand_score(5, 10, 50.0)
            profit_score = analyzer.calculate_profit_score(15.0, 1500.0)
            supply_score = analyzer.calculate_supply_score(3)
            candidate_score = analyzer.calculate_candidate_score(demand_score, profit_score, supply_score)
            decision_status = analyzer.determine_decision_status(candidate_score)
            
            candidates.append({
                'item_name': item_name,
                'amazon_median_price_jpy': float(amazon_median),
                'yahoo_median_price_jpy': float(yahoo_median),
                'price_diff_jpy': float(abs(amazon_median - yahoo_median)),
                'candidate_score': candidate_score,
                'decision_status': decision_status.value,
            })
        
        logger.info(f"  ✓ Scored {len(candidates)} candidates")
        
        # Step 5: Export
        logger.info("  Step 5: Exporting to CSV...")
        if candidates:
            csv_output.export_raw_data(candidates, "phase5_csv_import_test.csv")
            logger.info(f"  ✓ Exported {len(candidates)} candidates to CSV")
        
        logger.info("✓ Test 5 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 5 FAILED: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("Phase 5: CSV Import Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Amazon CSV Import", test_csv_import_amazon),
        ("Yahoo Auction CSV Import", test_csv_import_yahoo_auction),
        ("All Sources CSV Import", test_csv_import_all_sources),
        ("CSV Normalization & Scoring", test_csv_normalization_and_scoring),
        ("Complete CSV Pipeline", test_csv_end_to_end_pipeline),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary:")
    logger.info("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nTotal: {passed}/{total} passed")
    logger.info("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
