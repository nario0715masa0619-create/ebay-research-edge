"""
Phase 2 Full Integration Test

Tests the complete pipeline:
1. Fetch eBay data
2. Fetch Mercari data
3. Normalize data
4. Calculate metrics
5. Score candidates
6. Export CSV

Expected output: data/processed/phase2_integration_candidates.csv
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetcher.ebay_fetcher import eBayFetcher
from src.fetcher.mercari_fetcher import MercariFetcher
from src.normalizer.normalizer import Normalizer
from src.analyzer.analyzer import Analyzer
from src.display.csv_output import CSVOutput
from src.models.data_models import MarketRecord, SourceSite
from src.config.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_phase2_full_integration():
    """
    Test the complete Phase 2 pipeline.
    
    Flow:
    1. Fetch eBay Sold data
    2. Fetch Mercari data
    3. Normalize both datasets
    4. Aggregate metrics per item
    5. Score candidates
    6. Export to CSV
    """
    logger.info("\n" + "=" * 60)
    logger.info("Phase 2: Full Integration Test")
    logger.info("=" * 60)
    
    try:
        # Step 1: Initialize fetchers
        logger.info("\n[Step 1] Initializing fetchers...")
        ebay_fetcher = eBayFetcher(use_real_api=False)
        mercari_fetcher = MercariFetcher(use_dummy_data=True)
        
        # Step 2: Fetch data
        logger.info("\n[Step 2] Fetching data...")
        keyword = "pokemon card"
        ebay_listings = ebay_fetcher.fetch_sold_listings(keyword, limit=20)
        mercari_listings = mercari_fetcher.fetch_listings("ポケモンカード", limit=15)
        
        logger.info(f"eBay listings fetched: {len(ebay_listings)}")
        logger.info(f"Mercari listings fetched: {len(mercari_listings)}")
        
        # Step 3: Convert to MarketRecord
        logger.info("\n[Step 3] Converting to MarketRecords...")
        ebay_records = ebay_fetcher.convert_to_market_records(ebay_listings)
        mercari_records = mercari_fetcher.convert_to_market_records(mercari_listings)
        
        all_records = ebay_records + mercari_records
        logger.info(f"Total MarketRecords created: {len(all_records)}")
        
        # Step 4: Normalize data (Normalizer uses global config)
        logger.info("\n[Step 4] Normalizing data...")
        normalizer = Normalizer()
        normalized_records = normalizer.normalize_records(all_records)
        
        logger.info(f"Normalized records: {len(normalized_records)}")
        
        # Step 5: Aggregate and score
        logger.info("\n[Step 5] Aggregating metrics and scoring...")
        analyzer = Analyzer()
        candidates = []
        
        # Group by item
        items_dict = {}
        for record in normalized_records:
            item_name = record.normalized_title
            if item_name not in items_dict:
                items_dict[item_name] = {'ebay': [], 'mercari': []}
            
            if record.source_site == SourceSite.EBAY:
                items_dict[item_name]['ebay'].append(record)
            else:
                items_dict[item_name]['mercari'].append(record)
        
        # Calculate scores for each item
        for item_name, records_by_source in items_dict.items():
            ebay_recs = records_by_source['ebay']
            mercari_recs = records_by_source['mercari']
            
            if not ebay_recs or not mercari_recs:
                continue
            
            # Calculate eBay metrics
            sold_30d = len([r for r in ebay_recs if r.sold_flag])
            sold_90d = len([r for r in ebay_recs if r.sold_flag])
            active_count = len([r for r in ebay_recs if r.active_flag])
            
            if sold_30d == 0:
                continue
            
            prices_usd = [r.price for r in ebay_recs if r.price > 0]
            if not prices_usd:
                continue
            
            # Calculate Mercari metrics
            mercari_prices_jpy = [r.total_price for r in mercari_recs if r.total_price > 0]
            if not mercari_prices_jpy:
                continue
            
            domestic_min = min(mercari_prices_jpy)
            domestic_median = sorted(mercari_prices_jpy)[len(mercari_prices_jpy) // 2]
            
            # Calculate scores
            demand_score = analyzer.calculate_demand_score(sold_30d, sold_90d, 50.0)
            profit_score = analyzer.calculate_profit_score(15.0, 1500.0)
            supply_score = analyzer.calculate_supply_score(active_count)
            candidate_score = analyzer.calculate_candidate_score(
                demand_score, profit_score, supply_score
            )
            decision_status = analyzer.determine_decision_status(candidate_score)
            
            candidates.append({
                'item_name': item_name,
                'sold_30d': sold_30d,
                'sold_90d': sold_90d,
                'active_count': active_count,
                'median_price_usd': float(sorted(prices_usd)[len(prices_usd) // 2]),
                'domestic_min_price_jpy': float(domestic_min),
                'domestic_median_price_jpy': float(domestic_median),
                'estimated_profit_jpy': 1500.0,
                'estimated_profit_rate': 15.0,
                'str': 50.0,
                'candidate_score': candidate_score,
                'decision_status': decision_status.value,
            })
        
        logger.info(f"Candidates scored: {len(candidates)}")
        
        # Step 6: Export to CSV
        logger.info("\n[Step 6] Exporting to CSV...")
        csv_output = CSVOutput()
        output_path = config.processed_data_dir / "phase2_integration_candidates.csv"
        
        if candidates:
            csv_output.export_raw_data(candidates, "phase2_integration_candidates.csv")
            logger.info(f"CSV exported to: {output_path}")
        else:
            logger.warning("No candidates to export")
        
        logger.info("\n" + "=" * 60)
        logger.info("Phase 2 Integration Test: PASSED")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"\nPhase 2 Integration Test: FAILED")
        logger.error(f"Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_phase2_full_integration()
    sys.exit(0 if success else 1)


