"""
[ARCHIVED] eBay-Research-Edge - Old Pipeline Entry Point
This file is part of the old modular system (Phase 1-5) and is no longer used.
The current official entry point is generate_research_report.py.
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
from src.fetcher.fetcher_factory import FetcherFactory
from src.normalizer.normalizer import Normalizer
from src.analyzer.analyzer import Analyzer
from src.display.csv_output import CSVOutput
from src.models.data_models import SourceSite, MarketRecord
from src.config.config import config
from src.utils.csv_importer import CSVImporter
from src.utils.batch_processor import BatchCSVProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _convert_api_items_to_records(items):
    """
    Convert API items to MarketRecord objects.
    
    Args:
        items: List of normalized items from Fetcher API
    
    Returns:
        List of MarketRecord objects
    """
    records = []
    for i, item in enumerate(items):
        record = MarketRecord(
            record_id=f"ebay_api_{i}_{item.get('item_id', '')}",
            item_id=item.get('item_id', ''),
            source_site=SourceSite.EBAY,
            search_keyword='pokemon card',
            original_title=item.get('title', ''),
            normalized_title=item.get('title', ''),
            price=item.get('price', 0),
            shipping=0,
            currency=item.get('currency', 'USD'),
            total_price=item.get('price', 0),
            sold_flag=False,
            active_flag=True,
            sold_date=None,
            listing_url=item.get('url', ''),
        )
        records.append(record)
    
    return records


def run_pipeline_from_ebay_api(keyword: str = "pokemon card", limit: int = 50, fetcher_type: str = 'browse'):
    """Run the research pipeline fetching from eBay Browse/Insights API."""
    logger.info("=" * 60)
    logger.info("eBay-Research-Edge: Starting Research Pipeline (eBay API FETCH)")
    logger.info(f"Category: {config.category_name} ({config.category_name_ja})")
    logger.info(f"Fetcher: {fetcher_type}")
    logger.info("=" * 60)

    try:
        logger.info(f"\n[Step 1] Initializing eBay {fetcher_type} API fetcher...")
        try:
            api_fetcher = FetcherFactory.create_fetcher(fetcher_type)
            logger.info(f"✓ eBay {fetcher_type} API fetcher initialized")
        except ValueError as e:
            logger.error(f"✗ Failed to create fetcher: {e}")
            return None

        logger.info(f"\n[Step 2] Fetching data from eBay API (keyword: '{keyword}', limit: {limit})...")
        ebay_items = api_fetcher.search(
            query=keyword,
            limit=limit,
            itemLocationCountry='JP'
        )

        if not ebay_items:
            logger.warning(f"⚠️  No items found from eBay {fetcher_type} API")
            return None

        logger.info(f"✓ eBay items fetched: {len(ebay_items)}")

        logger.info("\n[Step 3] Converting eBay API items to MarketRecords...")
        ebay_records = _convert_api_items_to_records(ebay_items)
        logger.info(f"✓ Total records created: {len(ebay_records)}")

        return _process_and_score_records(ebay_records)

    except Exception as e:
        logger.error(f"\neBay API Pipeline failed: {e}", exc_info=True)
        return None


def run_research_pipeline(keyword: str = "pokemon card", limit: int = 50):
    """Run the complete research pipeline (online fetch mode)."""
    logger.info("=" * 60)
    logger.info("eBay-Research-Edge: Starting Research Pipeline (ONLINE FETCH)")
    logger.info(f"Category: {config.category_name} ({config.category_name_ja})")
    logger.info("=" * 60)

    try:
        logger.info("\n[Step 1] Initializing data fetchers...")
        ebay_fetcher = eBayFetcher(use_real_api=False)
        mercari_fetcher = MercariFetcher(use_dummy_data=True)
        logger.info("✓ Fetchers initialized")

        logger.info(f"\n[Step 2] Fetching data (keyword: '{keyword}', limit: {limit})...")
        mercari_keyword = config.mercari_keywords[0] if config.mercari_keywords else keyword

        ebay_listings = ebay_fetcher.fetch_sold_listings(keyword, limit=limit)
        mercari_listings = mercari_fetcher.fetch_listings(mercari_keyword, limit=limit)

        logger.info(f"✓ eBay listings fetched: {len(ebay_listings)}")
        logger.info(f"✓ Mercari listings fetched: {len(mercari_listings)}")

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
    """Run the complete research pipeline (single CSV import mode)."""
    logger.info("=" * 60)
    logger.info("eBay-Research-Edge: Starting Research Pipeline (CSV IMPORT - SINGLE FILE)")
    logger.info(f"Category: {config.category_name} ({config.category_name_ja})")
    logger.info(f"CSV File: {csv_file}")
    logger.info(f"Source: {source_site}")
    logger.info("=" * 60)

    try:
        logger.info("\n[Step 1] Initializing CSV importer...")
        csv_importer = CSVImporter()
        logger.info("✓ CSV importer initialized")

        logger.info(f"\n[Step 2] Importing CSV from: {csv_file}")
        csv_records = csv_importer.import_csv(csv_file, source_site)
        logger.info(f"✓ Records imported from CSV: {len(csv_records)}")

        logger.info("\n[Step 3] Fetching eBay data for comparison...")
        ebay_fetcher = eBayFetcher(use_real_api=False)
        ebay_listings = ebay_fetcher.fetch_sold_listings("pokemon card", limit=50)
        ebay_records = ebay_fetcher.convert_to_market_records(ebay_listings)
        logger.info(f"✓ eBay listings fetched: {len(ebay_records)}")

        logger.info("\n[Step 4] Combining CSV records with eBay data...")
        all_records = csv_records + ebay_records
        logger.info(f"✓ Total records: {len(all_records)}")

        return _process_and_score_records(all_records)

    except Exception as e:
        logger.error(f"\nCSV Import Pipeline failed: {e}", exc_info=True)
        return None


def run_pipeline_from_batch(import_dir: str = "data/imports", archive: bool = False):
    """Run the complete research pipeline (batch CSV import mode)."""
    logger.info("=" * 60)
    logger.info("eBay-Research-Edge: Starting Research Pipeline (BATCH CSV IMPORT)")
    logger.info(f"Category: {config.category_name} ({config.category_name_ja})")
    logger.info(f"Import Directory: {import_dir}")
    logger.info("=" * 60)

    try:
        logger.info("\n[Step 1] Initializing batch processor...")
        batch_processor = BatchCSVProcessor(import_dir=import_dir)
        logger.info("✓ Batch processor initialized")

        logger.info(f"\n[Step 2] Discovering CSV files in: {import_dir}")
        sources = batch_processor.discover_csv_files()
        csv_records, total_files, success_count = batch_processor.process_batch(sources)
        logger.info(f"✓ Processed {success_count}/{total_files} files, imported {len(csv_records)} records")

        logger.info("\n[Step 3] Fetching eBay data for comparison...")
        ebay_fetcher = eBayFetcher(use_real_api=False)
        ebay_listings = ebay_fetcher.fetch_sold_listings("pokemon card", limit=50)
        ebay_records = ebay_fetcher.convert_to_market_records(ebay_listings)
        logger.info(f"✓ eBay listings fetched: {len(ebay_records)}")

        logger.info("\n[Step 4] Combining CSV records with eBay data...")
        all_records = csv_records + ebay_records
        logger.info(f"✓ Total records: {len(all_records)}")

        output_path = _process_and_score_records(all_records)

        if archive and success_count > 0:
            logger.info(f"\n[Step 7] Archiving processed files...")
            batch_processor.archive_processed_files(sources)

        return output_path

    except Exception as e:
        logger.error(f"\nBatch CSV Import Pipeline failed: {e}", exc_info=True)
        return None


def _process_and_score_records(all_records):
    """Common scoring and analysis logic used by all pipeline modes."""
    try:
        logger.info("\n[Step 4] Normalizing data...")
        normalizer = Normalizer()
        normalized_records = normalizer.normalize_records(all_records)
        logger.info(f"✓ Records normalized: {len(normalized_records)}")

        logger.info("\n[Step 5] Aggregating metrics and scoring candidates...")
        analyzer = Analyzer()
        candidates = []

        items_dict = defaultdict(lambda: defaultdict(list))
        for record in normalized_records:
            item_name = record.normalized_title
            source_name = record.source_site.name.lower()
            items_dict[item_name][source_name].append(record)

        for item_name, sources_dict in items_dict.items():
            ebay_recs = sources_dict.get('ebay', [])
            other_recs = []
            other_sources = []

            for source_name, recs in sources_dict.items():
                if source_name != 'ebay':
                    other_recs.extend(recs)
                    other_sources.append(source_name)

            # Strategy 1: Multi-source matching (eBay sold + domestic)
            if ebay_recs and other_recs:
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
                candidate_score = analyzer.calculate_candidate_score(demand_score, profit_score, supply_score)
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

            # Strategy 2: eBay active-only (from Browse API)
            elif ebay_recs and not other_recs:
                active_count = len([r for r in ebay_recs if r.active_flag])
                if active_count == 0:
                    continue

                prices_usd = [r.price for r in ebay_recs if r.price > 0]
                if not prices_usd:
                    continue

                median_price = sorted(prices_usd)[len(prices_usd) // 2]
                
                # For active listings, estimate demand based on price variance
                price_variance = max(prices_usd) - min(prices_usd)
                estimated_demand = 50 + (price_variance / median_price * 100 if median_price > 0 else 0) * 0.3
                estimated_demand = min(100, estimated_demand)
                
                candidate_score = estimated_demand
                decision_status = analyzer.determine_decision_status(candidate_score)

                candidates.append({
                    'item_name': item_name,
                    'sold_30d': 0,
                    'sold_90d': 0,
                    'active_count': active_count,
                    'median_price_usd': float(median_price),
                    'domestic_min_price_jpy': 0.0,
                    'domestic_median_price_jpy': 0.0,
                    'estimated_profit_jpy': 0.0,
                    'estimated_profit_rate': 0.0,
                    'str': 0.0,
                    'candidate_score': candidate_score,
                    'decision_status': decision_status.value,
                    'data_source': 'ebay-active-only (browse-api)',
                })

            # Strategy 3: Domestic-only
            elif other_recs and not ebay_recs:
                domestic_prices_jpy = [r.total_price for r in other_recs if r.total_price > 0]
                if not domestic_prices_jpy:
                    continue

                domestic_min = min(domestic_prices_jpy)
                domestic_median = sorted(domestic_prices_jpy)[len(domestic_prices_jpy) // 2]
                domestic_max = max(domestic_prices_jpy)

                price_variance = domestic_max - domestic_min
                score_base = 50 + (price_variance / 1000.0) * 10
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
  python app.py --fetch-ebay pokemon card --limit 50
  python app.py --import-csv amazon.csv --source amazon
  python app.py --batch-import
        """
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--batch-import', action='store_true', help='Batch import all CSVs')
    mode_group.add_argument('--import-csv', help='Import single CSV file')
    mode_group.add_argument('--fetch-ebay', metavar='KEYWORD', help='Fetch from eBay API')
    mode_group.add_argument('--keyword', default='pokemon card', help='Search keyword')

    parser.add_argument('--source', choices=['amazon', 'yahoo_auction', 'yahoo_shopping', 'yahoo_fril', 'rakuten'], help='CSV source')
    parser.add_argument('--limit', type=int, default=50, help='Max listings per source')
    parser.add_argument('--fetcher', choices=['browse', 'insights'], default='browse', help='eBay API fetcher type')
    parser.add_argument('--archive', action='store_true', help='Archive processed files')
    parser.add_argument('--dashboard', action='store_true', help='Launch dashboard only')

    args = parser.parse_args()

    if not args.dashboard:
        if args.batch_import:
            output_path = run_pipeline_from_batch(import_dir="data/imports", archive=args.archive)
        elif args.import_csv:
            if not args.source:
                logger.error("ERROR: --source is required with --import-csv")
                sys.exit(1)
            output_path = run_pipeline_from_csv(csv_file=args.import_csv, source_site=args.source)
        elif args.fetch_ebay:
            output_path = run_pipeline_from_ebay_api(keyword=args.fetch_ebay, limit=args.limit, fetcher_type=args.fetcher)
        else:
            output_path = run_research_pipeline(keyword=args.keyword, limit=args.limit)

        if output_path is None:
            sys.exit(1)

    logger.info("\nResults available in: data/processed/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

