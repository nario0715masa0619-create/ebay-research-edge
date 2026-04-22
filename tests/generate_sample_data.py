"""
Script to generate and save sample data to CSV files.

This script generates realistic sample data and exports it to CSV format
for use in testing and development without relying on actual API calls.

Usage:
    python tests/generate_sample_data.py
"""

import sys
import logging
import csv
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.sample_data_generator import SampleDataGenerator
from src.config.config import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def save_items_to_csv(items, filename: str = "sample_items.csv"):
    """
    Save Item data to CSV file.
    
    Args:
        items: List of Item objects.
        filename: Output filename.
    
    Returns:
        Path to created CSV file.
    """
    output_dir = config.raw_data_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    fieldnames = [
        'item_id', 'normalized_name', 'franchise', 'character',
        'category', 'subcategory', 'created_at'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items:
            writer.writerow({
                'item_id': item.item_id,
                'normalized_name': item.normalized_name,
                'franchise': item.franchise or '',
                'character': item.character or '',
                'category': item.category,
                'subcategory': item.subcategory or '',
                'created_at': item.created_at.isoformat()
            })
    
    logger.info(f"Saved {len(items)} items to {output_path}")
    return output_path


def save_records_to_csv(records, filename: str):
    """
    Save MarketRecord data to CSV file.
    
    Args:
        records: List of MarketRecord objects.
        filename: Output filename.
    
    Returns:
        Path to created CSV file.
    """
    output_dir = config.raw_data_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    
    fieldnames = [
        'record_id', 'item_id', 'source_site', 'search_keyword',
        'original_title', 'normalized_title', 'price', 'shipping',
        'currency', 'total_price', 'sold_flag', 'active_flag',
        'sold_date', 'listing_url', 'fetched_at'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow({
                'record_id': record.record_id,
                'item_id': record.item_id,
                'source_site': record.source_site.value,
                'search_keyword': record.search_keyword,
                'original_title': record.original_title,
                'normalized_title': record.normalized_title,
                'price': record.price,
                'shipping': record.shipping,
                'currency': record.currency,
                'total_price': record.total_price,
                'sold_flag': record.sold_flag,
                'active_flag': record.active_flag,
                'sold_date': record.sold_date.isoformat() if record.sold_date else '',
                'listing_url': record.listing_url or '',
                'fetched_at': record.fetched_at.isoformat()
            })
    
    logger.info(f"Saved {len(records)} records to {output_path}")
    return output_path


def main():
    """
    Main function: generate and save sample data.
    """
    logger.info("\n=== Sample Data Generation Started ===\n")
    
    try:
        # Initialize generator
        generator = SampleDataGenerator()
        
        # Generate complete dataset
        logger.info("Generating complete dataset...")
        dataset = generator.generate_complete_dataset(
            item_count=5,      # 5 unique Pokemon cards
            ebay_records=30,   # 30 eBay sold listings
            mercari_records=25 # 25 Mercari sold listings
        )
        
        # Save items
        logger.info("\nSaving items...")
        items_path = save_items_to_csv(dataset['items'], "sample_items.csv")
        
        # Save eBay records
        logger.info("Saving eBay records...")
        ebay_path = save_records_to_csv(
            dataset['ebay_records'],
            "sample_ebay_sold.csv"
        )
        
        # Save Mercari records
        logger.info("Saving Mercari records...")
        mercari_path = save_records_to_csv(
            dataset['mercari_records'],
            "sample_mercari_sold.csv"
        )
        
        # Summary
        logger.info("\n=== Sample Data Generation Completed ===\n")
        logger.info(f"Items saved: {items_path}")
        logger.info(f"eBay records saved: {ebay_path}")
        logger.info(f"Mercari records saved: {mercari_path}")
        logger.info(f"\nTotal records: {len(dataset['all_records'])}")
        logger.info(f"  - eBay: {len(dataset['ebay_records'])}")
        logger.info(f"  - Mercari: {len(dataset['mercari_records'])}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during sample data generation: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
