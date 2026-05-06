"""
Simplified scraping: Octoparse CSV only
All 5 sites use Octoparse GUI tasks
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def import_octoparse_csv(csv_file: str, source_name: str) -> list:
    '''Octoparse CSV をインポート'''
    items = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append({
                    'title': row.get('商品名', row.get('title', '')),
                    'price': float(row.get('価格', row.get('price', '0')).replace('¥', '').replace(',', '')),
                    'url': row.get('URL', row.get('url', '')),
                    'seller': source_name,
                    'source': 'Octoparse'
                })
        logger.info(f'✓ {source_name}: {len(items)} items imported from {csv_file}')
    except FileNotFoundError:
        logger.warning(f'⚠ {csv_file} not found. Please run Octoparse task and export CSV.')
    except Exception as e:
        logger.error(f'✗ Error importing {csv_file}: {e}')
    
    return items

def main():
    logger.info('='*60)
    logger.info('Octoparse CSV Aggregation Pipeline')
    logger.info('='*60)
    
    all_items = []
    
    # 5 つの CSV を読み込み
    csv_files = {
        'Mercari': 'data/imports/mercari_latest.csv',
        'Rakuma': 'data/imports/rakuma_latest.csv',
        'Surugaya': 'data/imports/surugaya_latest.csv',
        'Hard Off': 'data/imports/hardoff_latest.csv',
        'Yahoo Fril': 'data/imports/fril_latest.csv',
    }
    
    for source, csv_file in csv_files.items():
        items = import_octoparse_csv(csv_file, source)
        all_items.extend(items)
    
    logger.info(f'[Summary] Total items: {len(all_items)}')
    
    if all_items:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'data/raw_scraping/all_sites_{timestamp}.csv'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'price', 'seller', 'url', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_items)
        
        logger.info(f'✓ Exported to: {output_file}')
        logger.info('='*60)
        logger.info('Next: python app.py --batch-import')
        logger.info('='*60)
    else:
        logger.warning('⚠ No items collected.')

if __name__ == '__main__':
    main()
