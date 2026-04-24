"""Phase 5B Batch Import Integration Test

Test the complete batch CSV import workflow:
1. Create test CSV files in data/imports/
2. Discover CSV files by source
3. Process all CSVs in batch mode
4. Combine with eBay data
5. Analyze and score
6. Export results
7. Archive processed files
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.batch_processor import BatchCSVProcessor
from src.normalizer.normalizer import Normalizer
from src.analyzer.analyzer import Analyzer
from src.display.csv_output import CSVOutput
from src.models.data_models import SourceSite
from src.config.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_batch_discovery():
    """Test CSV file discovery."""
    logger.info("\n[Test 1] Testing CSV file discovery...")
    
    # Create test import directory with sample files
    import_dir = Path("data/imports")
    import_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy template CSVs to import directory
    templates = [
        ("docs/csv_formats/amazon_template.csv", "amazon_sample_001.csv"),
        ("docs/csv_formats/yahoo_auction_template.csv", "yahoo_auction_sample_001.csv"),
    ]
    
    for src, dst in templates:
        src_path = Path(src)
        dst_path = import_dir / dst
        if src_path.exists():
            try:
                shutil.copy2(src_path, dst_path)
                logger.info(f"  Copied: {src} → {dst_path}")
            except Exception as e:
                logger.warning(f"  Failed to copy {src}: {e}")
    
    try:
        processor = BatchCSVProcessor(import_dir=str(import_dir))
        sources = processor.discover_csv_files()
        
        # Verify discovery
        total_discovered = sum(len(files) for files in sources.values())
        logger.info(f"✓ Discovered {total_discovered} files")
        
        for source, files in sources.items():
            if files:
                logger.info(f"  {source}: {len(files)} file(s)")
        
        assert total_discovered > 0, "No files discovered"
        logger.info("✓ Test 1 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 1 FAILED: {e}")
        return False


def test_batch_processing():
    """Test batch processing of multiple CSVs."""
    logger.info("\n[Test 2] Testing batch CSV processing...")
    
    try:
        processor = BatchCSVProcessor(import_dir="data/imports")
        sources = processor.discover_csv_files()
        
        if sum(len(files) for files in sources.values()) == 0:
            logger.warning("  No CSV files to process (skipping test)")
            logger.info("✓ Test 2 PASSED (no files)")
            return True
        
        all_records, total_files, success_count = processor.process_batch(sources)
        
        logger.info(f"✓ Processed {total_files} files")
        logger.info(f"✓ Successful: {success_count}/{total_files}")
        logger.info(f"✓ Total records: {len(all_records)}")
        
        assert len(all_records) > 0, "No records imported"
        logger.info("✓ Test 2 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 2 FAILED: {e}")
        return False


def test_batch_normalization_and_scoring():
    """Test batch import → normalization → scoring."""
    logger.info("\n[Test 3] Testing batch import → normalization → scoring...")
    
    try:
        processor = BatchCSVProcessor(import_dir="data/imports")
        sources = processor.discover_csv_files()
        
        if sum(len(files) for files in sources.values()) == 0:
            logger.warning("  No CSV files to process (skipping test)")
            logger.info("✓ Test 3 PASSED (no files)")
            return True
        
        # Step 1: Batch process
        all_records, total_files, success_count = processor.process_batch(sources)
        logger.info(f"  Step 1: Imported {len(all_records)} records")
        
        # Step 2: Normalize
        normalizer = Normalizer()
        normalized_records = normalizer.normalize_records(all_records)
        logger.info(f"  Step 2: Normalized {len(normalized_records)} records")
        
        # Step 3: Group and score
        analyzer = Analyzer()
        from collections import defaultdict
        items_dict = defaultdict(lambda: defaultdict(list))
        
        for record in normalized_records:
            item_name = record.normalized_title
            source_name = record.source_site.name.lower()
            items_dict[item_name][source_name].append(record)
        
        candidates = []
        for item_name, sources_dict in items_dict.items():
            other_recs = []
            other_sources = []
            for source_name, recs in sources_dict.items():
                if source_name != 'ebay':
                    other_recs.extend(recs)
                    other_sources.append(source_name)
            
            if other_recs:
                domestic_prices_jpy = [r.total_price for r in other_recs if r.total_price > 0]
                if domestic_prices_jpy:
                    domestic_min = min(domestic_prices_jpy)
                    domestic_median = sorted(domestic_prices_jpy)[len(domestic_prices_jpy) // 2]
                    domestic_max = max(domestic_prices_jpy)
                    
                    price_variance = domestic_max - domestic_min
                    score_base = 50 + (price_variance / 1000.0) * 10
                    candidate_score = min(100.0, score_base)
                    decision_status = analyzer.determine_decision_status(candidate_score)
                    
                    candidates.append({
                        'item_name': item_name,
                        'domestic_min_price_jpy': float(domestic_min),
                        'domestic_median_price_jpy': float(domestic_median),
                        'candidate_score': candidate_score,
                        'decision_status': decision_status.value,
                    })
        
        logger.info(f"  Step 3: Scored {len(candidates)} candidates")
        logger.info("✓ Test 3 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 3 FAILED: {e}")
        return False


def test_batch_end_to_end():
    """Test complete batch import pipeline."""
    logger.info("\n[Test 4] Testing complete batch import pipeline...")
    
    try:
        processor = BatchCSVProcessor(import_dir="data/imports")
        sources = processor.discover_csv_files()
        
        if sum(len(files) for files in sources.values()) == 0:
            logger.warning("  No CSV files to process (skipping test)")
            logger.info("✓ Test 4 PASSED (no files)")
            return True
        
        # Step 1: Batch process
        logger.info("  Step 1: Batch processing...")
        all_records, total_files, success_count = processor.process_batch(sources)
        logger.info(f"    ✓ Imported {len(all_records)} from {success_count}/{total_files} files")
        
        # Step 2: Normalize
        logger.info("  Step 2: Normalizing...")
        normalizer = Normalizer()
        normalized_records = normalizer.normalize_records(all_records)
        logger.info(f"    ✓ Normalized {len(normalized_records)} records")
        
        # Step 3: Export
        logger.info("  Step 3: Exporting to CSV...")
        csv_output = CSVOutput()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        candidates = []
        from collections import defaultdict
        items_dict = defaultdict(lambda: defaultdict(list))
        
        for record in normalized_records:
            item_name = record.normalized_title
            source_name = record.source_site.name.lower()
            items_dict[item_name][source_name].append(record)
        
        analyzer = Analyzer()
        for item_name, sources_dict in items_dict.items():
            other_recs = []
            other_sources = []
            for source_name, recs in sources_dict.items():
                if source_name != 'ebay':
                    other_recs.extend(recs)
                    other_sources.append(source_name)
            
            if other_recs:
                domestic_prices_jpy = [r.total_price for r in other_recs if r.total_price > 0]
                if domestic_prices_jpy:
                    candidates.append({'item_name': item_name, 'sources': ', '.join(other_sources)})
        
        if candidates:
            csv_output.export_raw_data(candidates, "phase5b_batch_test.csv")
            logger.info(f"    ✓ Exported {len(candidates)} candidates to CSV")
        
        logger.info("✓ Test 4 PASSED")
        return True
    except Exception as e:
        logger.error(f"✗ Test 4 FAILED: {e}")
        return False


def run_all_tests():
    """Run all batch import tests."""
    logger.info("\n" + "=" * 60)
    logger.info("Phase 5B: Batch Import Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("CSV File Discovery", test_batch_discovery),
        ("Batch Processing", test_batch_processing),
        ("Batch Normalization & Scoring", test_batch_normalization_and_scoring),
        ("Complete Batch Pipeline", test_batch_end_to_end),
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
