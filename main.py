import logging
import sys
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """メイン処理"""
    logger.info("eBay-Research-Edge Starting...")
    
    try:
        from src.config.config import config
        from src.fetcher.ebay_fetcher import eBayFetcher
        from src.normalizer.normalizer import Normalizer
        from src.analyzer.analyzer import Analyzer
        from src.display.csv_output import CSVOutput
        
        logger.info(f"Active category: {config.category_name_ja}")
        logger.info(f"eBay keywords: {config.ebay_keywords}")
        
        # TODO: Phase 1 実装
        # 1. eBay Sold データ取得
        # 2. 正規化
        # 3. 指標計算
        # 4. CSV出力
        
        logger.info("MVP Phase 1 - Coming soon...")
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
