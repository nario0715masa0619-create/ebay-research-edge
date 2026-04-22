"""
Phase 1 integration tests for the complete pipeline.

This module tests the entire pipeline:
1. Generate sample data (Items + MarketRecords)
2. Normalize titles
3. Calculate metrics and scores
4. Export to CSV

Tests the full flow from raw data to final candidate output.
"""

import sys
import logging
from pathlib import Path
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.sample_data_generator import SampleDataGenerator
from src.normalizer.normalizer import Normalizer
from src.analyzer.analyzer import Analyzer
from src.display.csv_output import CSVOutput
from src.models.data_models import ScoredCandidate, DecisionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pipeline_normalization():
    """
    Test Phase 1: Data normalization.
    
    Verifies that raw market records can be normalized properly.
    """
    logger.info("\n=== Test 1: Normalization ===\n")
    
    # Generate sample data
    generator = SampleDataGenerator()
    dataset = generator.generate_complete_dataset(3, 10, 8)
    
    # Normalize records
    normalizer = Normalizer()
    normalized_records = normalizer.normalize_records(dataset['all_records'])
    
    # Verify normalization
    assert len(normalized_records) == 18, f"Expected 18 records, got {len(normalized_records)}"
    assert all(rec.normalized_title for rec in normalized_records), "Some records have empty normalized_title"
    assert all('[eBay]' not in rec.normalized_title and '[Mercari]' not in rec.normalized_title 
               for rec in normalized_records), "Bracket markers not removed"
    
    logger.info(f"✓ Successfully normalized {len(normalized_records)} records")
    return dataset, normalized_records


def test_pipeline_metrics_calculation(dataset, normalized_records):
    """
    Test Phase 1: Metrics calculation.
    
    Verifies that various metrics can be calculated from records.
    """
    logger.info("\n=== Test 2: Metrics Calculation ===\n")
    
    analyzer = Analyzer()
    
    # Group records by item_id
    items_dict = {item.item_id: item for item in dataset['items']}
    records_by_item = {}
    
    for record in normalized_records:
        if record.item_id not in records_by_item:
            records_by_item[record.item_id] = []
        records_by_item[record.item_id].append(record)
    
    logger.info(f"Processing {len(records_by_item)} unique items...")
    
    # Calculate metrics for each item
    metrics_list = []
    for item_id, records in records_by_item.items():
        # Separate eBay and Mercari records
        ebay_records = [r for r in records if r.source_site.value == 'ebay']
        mercari_records = [r for r in records if r.source_site.value == 'mercari']
        
        # Calculate sold counts
        sold_counts = analyzer.calculate_sold_counts(ebay_records)
        
        # Calculate price stats
        ebay_stats = analyzer.calculate_price_stats(ebay_records)
        mercari_stats = analyzer.calculate_price_stats(mercari_records)
        
        # Calculate STR
        active_count = sum(1 for r in ebay_records if r.active_flag)
        str_value = analyzer.calculate_str(sold_counts[30], active_count)
        
        # Calculate profit (using median eBay price and min domestic price)
        if ebay_stats['median'] > 0 and mercari_stats['min'] > 0:
            profit = analyzer.calculate_estimated_profit(
                ebay_stats['median'],
                mercari_stats['min']
            )
        else:
            profit = {'profit_jpy': 0.0, 'profit_rate': 0.0}
        
        metrics = {
            'item_id': item_id,
            'sold_30d': sold_counts[30],
            'sold_90d': sold_counts[90],
            'active_count': active_count,
            'median_price_usd': ebay_stats['median'],
            'avg_price_usd': ebay_stats['avg'],
            'min_price_usd': ebay_stats['min'],
            'max_price_usd': ebay_stats['max'],
            'domestic_min_price_jpy': mercari_stats['min'],
            'domestic_median_price_jpy': mercari_stats['median'],
            'estimated_profit_jpy': profit['profit_jpy'],
            'estimated_profit_rate': profit['profit_rate'],
            'str': str_value
        }
        metrics_list.append(metrics)
        
        logger.info(f"✓ Item {item_id}: sold_30d={metrics['sold_30d']}, STR={metrics['str']}, profit_rate={metrics['estimated_profit_rate']}%")
    
    assert len(metrics_list) > 0, "No metrics calculated"
    logger.info(f"\n✓ Successfully calculated metrics for {len(metrics_list)} items\n")
    return metrics_list


def test_pipeline_scoring(metrics_list):
    """
    Test Phase 1: Scoring and decision.
    
    Verifies that scores can be calculated and decisions made.
    """
    logger.info("\n=== Test 3: Scoring and Decision ===\n")
    
    analyzer = Analyzer()
    candidates = []
    
    for i, metrics in enumerate(metrics_list):
        # Calculate sub-scores
        demand_score = analyzer.calculate_demand_score(
            metrics['sold_30d'],
            metrics['sold_90d'],
            metrics['str']
        )
        
        profit_score = analyzer.calculate_profit_score(
            metrics['estimated_profit_rate'],
            metrics['estimated_profit_jpy']
        )
        
        supply_score = analyzer.calculate_supply_score(
            metrics['active_count']
        )
        
        # Calculate composite score
        candidate_score = analyzer.calculate_candidate_score(
            demand_score,
            profit_score,
            supply_score
        )
        
        # Determine decision status
        decision_status = analyzer.determine_decision_status(candidate_score)
        
        # Create ScoredCandidate
        candidate = ScoredCandidate(
            candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
            item_id=metrics['item_id'],
            sold_30d=metrics['sold_30d'],
            sold_90d=metrics['sold_90d'],
            active_count=metrics['active_count'],
            median_price_usd=metrics['median_price_usd'],
            avg_price_usd=metrics['avg_price_usd'],
            min_price_usd=metrics['min_price_usd'],
            max_price_usd=metrics['max_price_usd'],
            domestic_min_price_jpy=metrics['domestic_min_price_jpy'],
            domestic_median_price_jpy=metrics['domestic_median_price_jpy'],
            estimated_profit_jpy=metrics['estimated_profit_jpy'],
            estimated_profit_rate=metrics['estimated_profit_rate'],
            str=metrics['str'],
            candidate_score=candidate_score,
            decision_status=decision_status
        )
        candidates.append(candidate)
        
        logger.info(f"✓ {candidate.candidate_id}: score={candidate_score}, status={decision_status.value}")
    
    # Verify results
    assert len(candidates) > 0, "No candidates generated"
    assert all(hasattr(c, 'candidate_score') for c in candidates), "Some candidates missing score"
    assert all(hasattr(c, 'decision_status') for c in candidates), "Some candidates missing decision status"
    
    # Count decision statuses
    list_candidates = sum(1 for c in candidates if c.decision_status == DecisionStatus.LIST_CANDIDATE)
    hold_count = sum(1 for c in candidates if c.decision_status == DecisionStatus.HOLD)
    skip_count = sum(1 for c in candidates if c.decision_status == DecisionStatus.SKIP)
    
    logger.info(f"\nDecision Summary:")
    logger.info(f"  LIST_CANDIDATE: {list_candidates}")
    logger.info(f"  HOLD: {hold_count}")
    logger.info(f"  SKIP: {skip_count}")
    logger.info(f"\n✓ Successfully scored {len(candidates)} candidates\n")
    
    return candidates


def test_pipeline_csv_export(candidates):
    """
    Test Phase 1: CSV export.
    
    Verifies that scored candidates can be exported to CSV.
    """
    logger.info("\n=== Test 4: CSV Export ===\n")
    
    csv_output = CSVOutput()
    
    # Export candidates
    output_path = csv_output.export_candidates(
        candidates,
        filename="test_phase1_candidates.csv"
    )
    
    # Verify file exists
    assert output_path.exists(), f"CSV file not created: {output_path}"
    
    # Verify file has content
    file_size = output_path.stat().st_size
    assert file_size > 0, "CSV file is empty"
    
    # Read and verify CSV structure
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) > 1, "CSV file has no data rows"
        
        # Check header
        header = lines[0].strip().split(',')
        expected_columns = [
            'candidate_id', 'item_id', 'sold_30d', 'sold_90d', 'active_count',
            'median_price_usd', 'avg_price_usd', 'min_price_usd', 'max_price_usd',
            'domestic_min_price_jpy', 'domestic_median_price_jpy',
            'estimated_profit_jpy', 'estimated_profit_rate', 'str', 'candidate_score',
            'decision_status', 'calculated_at'
        ]
        assert len(header) == len(expected_columns), f"CSV header mismatch: {header}"
        
        logger.info(f"✓ CSV file created: {output_path}")
        logger.info(f"✓ File size: {file_size} bytes")
        logger.info(f"✓ Records: {len(lines) - 1}")
        logger.info(f"✓ Columns: {len(header)}\n")
    
    return output_path


def run_integration_test():
    """
    Run the complete Phase 1 integration test.
    """
    logger.info("\n" + "="*60)
    logger.info("=== Phase 1 Integration Test Started ===")
    logger.info("="*60 + "\n")
    
    try:
        # Step 1: Normalization
        dataset, normalized_records = test_pipeline_normalization()
        
        # Step 2: Metrics calculation
        metrics_list = test_pipeline_metrics_calculation(dataset, normalized_records)
        
        # Step 3: Scoring
        candidates = test_pipeline_scoring(metrics_list)
        
        # Step 4: CSV export
        output_path = test_pipeline_csv_export(candidates)
        
        logger.info("="*60)
        logger.info("=== Phase 1 Integration Test PASSED ===")
        logger.info("="*60)
        logger.info(f"\nFinal output: {output_path}\n")
        
        return True
    
    except AssertionError as e:
        logger.error(f"\n✗ Integration Test Failed: {e}\n")
        return False
    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}\n", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_integration_test()
    exit(0 if success else 1)
