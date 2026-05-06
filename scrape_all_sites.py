"""
Master scraping script to collect data from all 5 sites daily.
Integrates: Mercari, Rakuma, Yahoo Fril, Surugaya, Hard Off
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

from src.scraper.site_scrapers import (
    scrape_mercari,
    scrape_rakuma,
    scrape_yahoo_fril,
    scrape_surugaya_octoparse,
    scrape_hardoff_octoparse
)

def scrape_all_sites(keyword: str = 'ポケモンカード', limit: int = 50):
    """
    全サイトをスクレイピング
    
    Args:
        keyword: 検索キーワード
        limit: 1 サイトあたりの取得件数
    """
    
    logger.info('='*60)
    logger.info('Starting Multi-Site Scraping Pipeline')
    logger.info(f'Keyword: {keyword}, Limit: {limit}')
    logger.info('='*60)
    
    all_items = []
    
    # [Step 1] Mercari（Scrape.do）
    logger.info('[1/5] Scraping Mercari...')
    try:
        mercari_items = scrape_mercari(keyword, limit)
        all_items.extend(mercari_items)
        logger.info(f'✓ Mercari: {len(mercari_items)} items')
    except Exception as e:
        logger.error(f'✗ Mercari failed: {e}')
    
    # [Step 2] Rakuma（Scrape.do）
    logger.info('[2/5] Scraping Rakuma...')
    try:
        rakuma_items = scrape_rakuma(keyword, limit)
        all_items.extend(rakuma_items)
        logger.info(f'✓ Rakuma: {len(rakuma_items)} items')
    except Exception as e:
        logger.error(f'✗ Rakuma failed: {e}')
    
    # [Step 3] Yahoo Fril（Diffbot）
    logger.info('[3/5] Scraping Yahoo Fril...')
    try:
        yahoo_items = scrape_yahoo_fril(keyword, limit)
        all_items.extend(yahoo_items)
        logger.info(f'✓ Yahoo Fril: {len(yahoo_items)} items')
    except Exception as e:
        logger.error(f'✗ Yahoo Fril failed: {e}')
    
    # [Step 4] Surugaya（Octoparse CSV）
    logger.info('[4/5] Importing Surugaya (Octoparse)...')
    surugaya_csv = 'data/imports/surugaya_latest.csv'
    if os.path.exists(surugaya_csv):
        try:
            surugaya_items = scrape_surugaya_octoparse(surugaya_csv)
            all_items.extend(surugaya_items)
            logger.info(f'✓ Surugaya: {len(surugaya_items)} items')
        except Exception as e:
            logger.error(f'✗ Surugaya failed: {e}')
    else:
        logger.warning(f'⚠ Surugaya CSV not found: {surugaya_csv}')
        logger.warning('→ Octoparse で手動実行→CSV エクスポートしてください')
    
    # [Step 5] Hard Off（Octoparse CSV）
    logger.info('[5/5] Importing Hard Off (Octoparse)...')
    hardoff_csv = 'data/imports/hardoff_latest.csv'
    if os.path.exists(hardoff_csv):
        try:
            hardoff_items = scrape_hardoff_octoparse(hardoff_csv)
            all_items.extend(hardoff_items)
            logger.info(f'✓ Hard Off: {len(hardoff_items)} items')
        except Exception as e:
            logger.error(f'✗ Hard Off failed: {e}')
    else:
        logger.warning(f'⚠ Hard Off CSV not found: {hardoff_csv}')
        logger.warning('→ Octoparse で手動実行→CSV エクスポートしてください')
    
    # [Step 6] CSV に統合出力
    logger.info(f'[Summary] Total items collected: {len(all_items)}')
    
    if all_items:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'data/raw_scraping/{keyword}_{timestamp}.csv'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title', 'price', 'seller', 'url', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in all_items:
                writer.writerow(item)
        
        logger.info(f'✓ Exported to: {output_file}')
        
        # [Step 7] app.py の batch-import に渡す
        logger.info('='*60)
        logger.info('Next Step: Run the following command to import into app.py')
        logger.info(f'python app.py --batch-import')
        logger.info('='*60)
        
        return output_file
    else:
        logger.warning('⚠ No items collected.')
        return None

if __name__ == '__main__':
    keyword = sys.argv[1] if len(sys.argv) > 1 else 'ポケモンカード'
    scrape_all_sites(keyword)
