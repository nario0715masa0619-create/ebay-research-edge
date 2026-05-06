"""
Site-specific scrapers for Mercari, Rakuma, Yahoo! Fril
Fixed HTML parsing with correct selectors
"""

from src.scraper.scraping_clients import ScrapingFactory
import json
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
import re

logger = logging.getLogger(__name__)

def scrape_mercari(keyword: str, limit: int = 50) -> List[Dict]:
    '''Mercari をスクレイピング（Scrape.do 使用）'''
    client = ScrapingFactory.get_client('scrapedo')
    
    search_url = f'https://jp.mercari.com/search?keyword={keyword}'
    result = client.scrape(search_url, render_js=True)
    
    if result['status'] != 200:
        logger.error(f'Mercari scraping failed: {result.get("error")}')
        return []
    
    soup = BeautifulSoup(result['content'], 'html.parser')
    items = []
    
    try:
        # Mercari の商品セル（React コンポーネント）
        product_cells = soup.find_all('a', {'data-testid': 'product-card-anchor'})
        
        for cell in product_cells[:limit]:
            try:
                # 商品 URL
                url = cell.get('href', '')
                if not url.startswith('http'):
                    url = f'https://jp.mercari.com{url}'
                
                # 商品情報は data 属性またはテキストから抽出
                title_elem = cell.find('h2') or cell.find('div', class_='merch-title')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                price_elem = cell.find('span', {'data-testid': 'price'}) or cell.find('span', class_='price')
                price_text = price_elem.get_text(strip=True) if price_elem else '0'
                
                # 価格をクリーン（¥1,234 → 1234）
                price = float(re.sub(r'[¥,]', '', price_text)) if price_text else 0
                
                if title and price > 0:
                    items.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'seller': 'Mercari User',
                        'source': 'Scrape.do'
                    })
            except Exception as e:
                logger.debug(f'Error parsing Mercari item: {e}')
                continue
        
        logger.info(f'✓ Mercari: {len(items)} items scraped')
    except Exception as e:
        logger.error(f'Mercari parsing error: {e}')
    
    return items

def scrape_rakuma(keyword: str, limit: int = 50) -> List[Dict]:
    '''Rakuma をスクレイピング（Scrape.do 使用）'''
    client = ScrapingFactory.get_client('scrapedo')
    
    search_url = f'https://fril.jp/search?query={keyword}'
    result = client.scrape(search_url, render_js=True)
    
    if result['status'] != 200:
        logger.error(f'Rakuma scraping failed: {result.get("error")}')
        return []
    
    soup = BeautifulSoup(result['content'], 'html.parser')
    items = []
    
    try:
        # Rakuma の商品セル
        product_cells = soup.find_all('a', class_='item-card')
        
        for cell in product_cells[:limit]:
            try:
                url = cell.get('href', '')
                if not url.startswith('http'):
                    url = f'https://fril.jp{url}'
                
                title_elem = cell.find('h3') or cell.find('div', class_='title')
                title = title_elem.get_text(strip=True) if title_elem else ''
                
                price_elem = cell.find('span', class_='price') or cell.find('div', class_='price')
                price_text = price_elem.get_text(strip=True) if price_elem else '0'
                price = float(re.sub(r'[¥,]', '', price_text)) if price_text else 0
                
                if title and price > 0:
                    items.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'seller': 'Rakuma User',
                        'source': 'Scrape.do'
                    })
            except Exception as e:
                logger.debug(f'Error parsing Rakuma item: {e}')
                continue
        
        logger.info(f'✓ Rakuma: {len(items)} items scraped')
    except Exception as e:
        logger.error(f'Rakuma parsing error: {e}')
    
    return items

def scrape_yahoo_fril(keyword: str, limit: int = 50) -> List[Dict]:
    '''Yahoo! Fril をスクレイピング（Diffbot 使用、構造化データ）'''
    client = ScrapingFactory.get_client('diffbot')
    
    search_url = f'https://fril.jp/search?query={keyword}'
    result = client.extract(search_url)
    
    if 'error' in result:
        logger.error(f'Yahoo Fril scraping failed: {result.get("error")}')
        # Fallback: Rakuma スクレイピングを使用
        return scrape_rakuma(keyword, limit)
    
    items = []
    
    try:
        # Diffbot は構造化データを JSON で返す
        objects = result.get('objects', [])
        
        for obj in objects[:limit]:
            try:
                title = obj.get('title', '')
                price_str = obj.get('offerPrice', '0')
                price = float(re.sub(r'[¥,]', '', str(price_str))) if price_str else 0
                url = obj.get('pageUrl', '')
                
                if title and price > 0:
                    items.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'seller': 'Fril User',
                        'source': 'Diffbot'
                    })
            except Exception as e:
                logger.debug(f'Error parsing Diffbot item: {e}')
                continue
        
        logger.info(f'✓ Yahoo Fril (Diffbot): {len(items)} items scraped')
    except Exception as e:
        logger.error(f'Yahoo Fril parsing error: {e}')
    
    return items

def scrape_surugaya_octoparse(csv_file: str) -> List[Dict]:
    '''Octoparse からエクスポートされた Surugaya CSV をインポート'''
    import csv
    
    items = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    price = float(re.sub(r'[¥,]', '', row.get('価格', '0')))
                    items.append({
                        'title': row.get('商品名', ''),
                        'price': price,
                        'url': row.get('URL', ''),
                        'seller': row.get('販売会社', 'Surugaya'),
                        'source': 'Octoparse'
                    })
                except Exception as e:
                    logger.debug(f'Error parsing Surugaya row: {e}')
                    continue
        
        logger.info(f'✓ Surugaya (Octoparse): {len(items)} items imported')
    except Exception as e:
        logger.error(f'Error importing Surugaya CSV: {e}')
    
    return items

def scrape_hardoff_octoparse(csv_file: str) -> List[Dict]:
    '''Octoparse からエクスポートされた Hard Off CSV をインポート'''
    import csv
    
    items = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    price = float(re.sub(r'[¥,]', '', row.get('価格', '0')))
                    items.append({
                        'title': row.get('商品名', ''),
                        'price': price,
                        'url': row.get('URL', ''),
                        'seller': row.get('販売会社', 'Hard Off'),
                        'source': 'Octoparse'
                    })
                except Exception as e:
                    logger.debug(f'Error parsing Hard Off row: {e}')
                    continue
        
        logger.info(f'✓ Hard Off (Octoparse): {len(items)} items imported')
    except Exception as e:
        logger.error(f'Error importing Hard Off CSV: {e}')
    
    return items
