"""
eBay-Research-Edge - Main Application Entry Point

This is the main script to run the complete research pipeline:
1. Fetch eBay Sold data OR Import CSV data
2. Fetch Mercari data
3. Normalize both datasets
4. Calculate metrics and scores
5. Export results to CSV
6. Launch Streamlit dashboard (Phase 3)

Usage:
    python app.py                                              # Run with default settings (online fetch)
    python app.py --keyword "pokemon card" --limit 50          # Fetch with custom keyword
    python app.py --import-csv amazon.csv --source amazon      # Import Amazon CSV
    python app.py --import-csv yahoo.csv --source yahoo_auction
    python app.py --dashboard                                  # Launch only dashboard (skip fetch/analysis)

Supported CSV Sources:
    - amazon
    - yahoo_auction
    - yahoo_shopping
    - yahoo_fril
    - rakuten

Environment Variables:
    ACTIVE_CATEGORY: Category name (default: pokemon_card)
    DATA_DIR: Data directory (default: ./data)
"""

import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.fetcher.ebay_fetcher import eBayFetcher
from src.fetcher.mercari_fetcher import MercariFetcher
from src.normalizer.normalizer import Normalizer
from src.analyzer.analyzer import Analyzer
from src.display.csv_output import CSVOutput
from src.models.data_models import SourceSite
from src.config.config import config
from src.utils.csv_importer import CSVImporter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_research_pipeline(keyword: str = "pokemon card", limit: int = 50):
    """
    Run the complete research pipeline (online fetch mode).

    Args:
        keyword (str): Search keyword for eBay/Mercari.
        limit (int): Maximum number of listings to fetch per source.

    Returns:
        Path: Path to the generated CSV file.
    """
    logger.info("=" * 60)
    logger.info("eBay-Research-Edge: Starting Research Pipeline (ONLINE FETCH)")
    logger.info(f"Category: {config.category_name} ({config.category_name_ja})")
    logger.info("=" * 60)

    try:
        # Step 1: Initialize fetchers
        logger.info("\n[Step 1] Initializing data fetchers...")
        ebay_fetcher = eBayFetcher(use_real_api=False)
        mercari_fetcher = MercariFetcher(use_dummy_data=True)
        logger.info("✓ Fetchers initialized")

        # Step 2: Fetch data
        logger.info(f"\n[Step 2] Fetching data (keyword: '{keyword}', limit: {limit})...")
        mercari_keyword = config.mercari_keywords[0] if config.mercari_keywords else keyword

        ebay_listings = ebay_fetcher.fetch_sold_listings(keyword, limit=limit)
        mercari_listings = mercari_fetcher.fetch_listings(mercari_keyword, limit=limit)

        logger.info(f"✓ eBay listings fetched: {len(ebay_listings)}")
        logger.info(f"✓ Mercari listings fetched: {len(mercari_listings)}")

        # Step 3: Convert to MarketRecord
        logger.info("\n[Step 3] Converting to MarketRecords...")
        ebay_records = ebay_fetcher.convert_to_market_records(ebay_listings)
        mercari_records = mercari_fetcher.convert_to_market_records(mercari_listings)

        all_records = ebay_records + mercari_records
        logger.info(f"✓ Total records created: {len(all_records)}")

        return _process_and_score_records(all_records)

    except Exception as e:
        logger.error(f"\nPipeline failed: {e}", exc_info=True)
        return None


def run_pipeline_from_csv(csv_file: str, source_site: str):
    """
    Run the complete research pipeline (CSV import mode).

    Args:
        csv_file (str): Path to CSV file to import.
        source_site (str): Source site name (amazon, yahoo_auction, etc.).

    Returns:
        Path: Path to the generated CSV file.
    """
    logger.info("=" * 60)
    logger.info("eBay-Research-Edge: Starting Research Pipeline (CSV IMPORT)")
    logger.info(f"Category: {config.category_name} ({config.category_name_ja})")
    logger.info(f"CSV File: {csv_file}")
    logger.info(f"Source: {source_site}")
    logger.info("=" * 60)

    try:
        # Step 1: Initialize CSV importer
        logger.info("\n[Step 1] Initializing CSV importer...")
        csv_importer = CSVImporter()
        logger.info("✓ CSV importer initialized")

        # Step 2: Import CSV data
        logger.info(f"\n[Step 2] Importing CSV from: {csv_file}")
        csv_records = csv_importer.import_csv(csv_file, source_site)
        logger.info(f"✓ Records imported from CSV: {len(csv_records)}")

        # Step 3: Optionally fetch eBay data for comparison
        logger.info("\n[Step 3] Fetching eBay data for price comparison (optional)...")
        ebay_fetcher = eBayFetcher(use_real_api=False)
        mercari_keyword = config.mercari_keywords[0] if config.mercari_keywords else "pokemon card"
        ebay_listings = ebay_fetcher.fetch_sold_listings("pokemon card", limit=50)
        ebay_records = ebay_fetcher.convert_to_market_records(ebay_listings)
        logger.info(f"✓ eBay listings fetched: {len(ebay_records)}")

        # Step 4: Combine records
        logger.info("\n[Step 4] Combining CSV records with eBay data...")
        all_records = csv_records + ebay_records
        logger.info(f"✓ Total records: {len(all_records)}")

        return _process_and_score_records(all_records)

    except Exception as e:
        logger.error(f"\nCSV Import Pipeline failed: {e}", exc_info=True)
        return None


def _process_and_score_records(all_records):
    """
    Common scoring and analysis logic used by both pipeline modes.
    Handles both multi-source matching and single-source ranking.

    Args:
        all_records: List of MarketRecord objects.

    Returns:
        Path: Path to the generated CSV file.
    """
    try:
        # Step 4 (or Step 5 depending on pipeline mode): Normalize data
        logger.info("\n[Step 4] Normalizing data...")
        normalizer = Normalizer()
        normalized_records = normalizer.normalize_records(all_records)
        logger.info(f"✓ Records normalized: {len(normalized_records)}")

        # Step 5 (or Step 6): Aggregate and score
        logger.info("\n[Step 5] Aggregating metrics and scoring candidates...")
        analyzer = Analyzer()
        candidates = []

        # Group by normalized title and source
        items_dict = defaultdict(lambda: defaultdict(list))
        for record in normalized_records:
            item_name = record.normalized_title
            source_name = record.source_site.name.lower()
            items_dict[item_name][source_name].append(record)

        # Calculate scores
        for item_name, sources_dict in items_dict.items():
            ebay_recs = sources_dict.get('ebay', [])
            other_recs = []
            other_sources = []
            
            # Collect all non-eBay records
            for source_name, recs in sources_dict.items():
                if source_name != 'ebay':
                    other_recs.extend(recs)
                    other_sources.append(source_name)

            # Strategy: Score if we have eBay + at least one other source
            # OR score single-source (domestic) items
            if ebay_recs and other_recs:
                # Multi-source matching
                sold_30d = len([r for r in ebay_recs if r.sold_flag])
                sold_90d = len([r for r in ebay_recs if r.sold_flag])
                active_count = len([r for r in ebay_recs if r.active_flag])

                if sold_30d == 0:
                    continue

                prices_usd = [r.price for r in ebay_recs if r.price > 0]
                if not prices_usd:
                    continue

                domestic_prices_jpy = [r.total_price for r in other_recs if r.total_price > 0]
                if not domestic_prices_jpy:
                    continue

                domestic_min = min(domestic_prices_jpy)
                domestic_median = sorted(domestic_prices_jpy)[len(domestic_prices_jpy) // 2]

                str_value = (sold_30d / (sold_30d + active_count) * 100) if (sold_30d + active_count) > 0 else 0
                demand_score = analyzer.calculate_demand_score(sold_30d, sold_90d, str_value)
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
                    'str': str_value,
                    'candidate_score': candidate_score,
                    'decision_status': decision_status.value,
                    'data_source': 'multi-source (ebay + ' + ', '.join(other_sources) + ')',
                })

            elif other_recs and not ebay_recs:
                # Single-source (domestic) ranking without eBay data
                domestic_prices_jpy = [r.total_price for r in other_recs if r.total_price > 0]
                if not domestic_prices_jpy:
                    continue

                domestic_min = min(domestic_prices_jpy)
                domestic_median = sorted(domestic_prices_jpy)[len(domestic_prices_jpy) // 2]
                domestic_max = max(domestic_prices_jpy)

                # Domestic-only scoring: use price variance and count as proxies
                price_variance = domestic_max - domestic_min
                score_base = 50 + (price_variance / 1000.0) * 10  # Higher variance = higher score (more opportunity)
                candidate_score = min(100.0, score_base)
                decision_status = analyzer.determine_decision_status(candidate_score)

                candidates.append({
                    'item_name': item_name,
                    'sold_30d': len(other_recs),
                    'sold_90d': len(other_recs),
                    'active_count': 0,
                    'median_price_usd': 0.0,
                    'domestic_min_price_jpy': float(domestic_min),
                    'domestic_median_price_jpy': float(domestic_median),
                    'estimated_profit_jpy': 0.0,
                    'estimated_profit_rate': 0.0,
                    'str': 0.0,
                    'candidate_score': candidate_score,
                    'decision_status': decision_status.value,
                    'data_source': 'domestic-only (' + ', '.join(other_sources) + ')',
                })

        logger.info(f"✓ Candidates scored: {len(candidates)}")

        # Step 6 (or Step 7): Export to CSV
        logger.info("\n[Step 6] Exporting results to CSV...")
        csv_output = CSVOutput()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"candidates_{config.active_category}_{timestamp}.csv"
        output_path = csv_output.export_raw_data(candidates, output_filename)

        logger.info(f"✓ Results exported to: {output_path}")

        logger.info("\n" + "=" * 60)
        logger.info("Research Pipeline Completed Successfully!")
        logger.info("=" * 60)

        return output_path

    except Exception as e:
        logger.error(f"\nScoring/Export failed: {e}", exc_info=True)
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='eBay-Research-Edge: Research support tool for Japanese sellers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                                         # Run with defaults (online fetch)
  python app.py --keyword "pokemon card" --limit 50     # Fetch with custom keyword
  python app.py --import-csv amazon.csv --source amazon # Import Amazon CSV
  python app.py --dashboard                             # Launch dashboard only
        """
    )

    # Create mutually exclusive group: online fetch vs CSV import
    mode_group = parser.add_mutually_exclusive_group()

    mode_group.add_argument(
        '--import-csv',
        help='Import data from CSV file (requires --source)'
    )

    mode_group.add_argument(
        '--keyword',
        default='pokemon card',
        help='Search keyword for online fetch (default: pokemon card)'
    )

    parser.add_argument(
        '--source',
        choices=['amazon', 'yahoo_auction', 'yahoo_shopping', 'yahoo_fril', 'rakuten'],
        help='CSV source site (required with --import-csv)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Max listings per source for online fetch (default: 50)'
    )

    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Launch Streamlit dashboard only (skip pipeline)'
    )

    parser.add_argument(
        '--category',
        help='Category name (overrides ACTIVE_CATEGORY env var)'
    )

    args = parser.parse_args()

    # Run pipeline (choose mode)
    if not args.dashboard:
        if args.import_csv:
            # CSV import mode
            if not args.source:
                logger.error("ERROR: --source is required when using --import-csv")
                parser.print_help()
                sys.exit(1)

            output_path = run_pipeline_from_csv(
                csv_file=args.import_csv,
                source_site=args.source
            )
        else:
            # Online fetch mode (default)
            output_path = run_research_pipeline(
                keyword=args.keyword,
                limit=args.limit
            )

        if output_path is None:
            sys.exit(1)

    # Launch dashboard (Phase 3)
    logger.info("\n[Step 7] Launching Streamlit dashboard...")
    logger.info("Note: Streamlit dashboard implementation pending (Phase 3)")
    logger.info("For now, results are available in: data/processed/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
