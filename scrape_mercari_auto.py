import requests
import json
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
from urllib.parse import quote
import os
from dotenv import load_dotenv

# .env ファイルを読み込む
load_dotenv()
SCRAPE_DO_API_KEY = os.getenv('SCRAPEDO_API_KEY')
SCRAPE_DO_URL = "https://api.scrape.do"

def scrape_mercari_with_scrapeapi(keyword="ポケモンカード", pages=1, debug=True):
    """Scrape.do を使用してメルカリをスクレイピング"""
    results = []
    
    if not SCRAPE_DO_API_KEY:
        print("❌ エラー: .env に SCRAPEDO_API_KEY が設定されていません。")
        return results
    
    for page in range(1, pages + 1):
        target_url = f"https://jp.mercari.com/search?keyword={quote(keyword)}&page={page}"
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ページ {page} をスクレイピング中")
        print(f"  URL: {target_url}")
        
        try:
            # Scrape.do API にリクエスト
            api_url = f"{SCRAPE_DO_URL}?url={quote(target_url)}&token={SCRAPE_DO_API_KEY}&render=true"
            print(f"  API リクエスト実行中...")
            
            response = requests.get(
                api_url,
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            print(f"  ステータス: {response.status_code}")
            
            if response.status_code != 200:
                print(f"  ⚠️ エラー: HTTP {response.status_code}")
                continue
            
            # HTML パース
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # デバッグ: HTML を保存
            if debug:
                with open(f'debug_page_{page}.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"  💾 HTML を debug_page_{page}.html に保存しました")
            
            # 複数のセレクタを試す
            print(f"  🔍 セレクタをテスト中...")
            
            # セレクタ 1: li[data-testid="item-cell"]
            cards = soup.find_all('li', {'data-testid': 'item-cell'})
            print(f"    - li[data-testid='item-cell']: {len(cards)} 件")
            
            # セレクタ 2: a[data-testid="product-card-anchor"]
            if len(cards) == 0:
                cards = soup.find_all('a', {'data-testid': 'product-card-anchor'})
                print(f"    - a[data-testid='product-card-anchor']: {len(cards)} 件")
            
            # セレクタ 3: div.merch-item-card (汎用)
            if len(cards) == 0:
                cards = soup.find_all('div', {'class': re.compile(r'merch|item|card', re.I)})
                print(f"    - div[class*='merch|item|card']: {len(cards)} 件")
            
            # セレクタ 4: すべての li
            if len(cards) == 0:
                cards = soup.find_all('li')
                print(f"    - すべての li: {len(cards)} 件")
            
            if len(cards) == 0:
                print(f"  ⚠️ カードが見つかりません")
                print(f"  HTML サイズ: {len(response.text)} bytes")
                print(f"  HTML サンプル:\n{response.text[:500]}")
                continue
            
            print(f"  ✓ {len(cards)} 件の商品カードを検出")
            
            page_results = 0
            for idx, card in enumerate(cards[:5], 1):  # 最初の5件だけテスト
                try:
                    # デバッグ: カード HTML を出力
                    print(f"    [{idx}] HTML: {str(card)[:200]}...")
                    
                    # aria-label から商品名と価格を抽出
                    img_div = card.find('div', {'class': 'meritItemThumbnail'})
                    if not img_div:
                        img_div = card.find('div', {'class': re.compile(r'image|img|thumbnail', re.I)})
                    
                    if not img_div:
                        print(f"    [{idx}] aria-label なし")
                        continue
                    
                    aria_label = img_div.get('aria-label', '')
                    print(f"    [{idx}] aria-label: {aria_label[:100]}")
                    
                    # 正規表現で抽出: "商品名 の画像 価格円"
                    match = re.search(r'(.+?)\s+の画像\s+(\d+(?:,\d+)?)円', aria_label)
                    if not match:
                        print(f"    [{idx}] 正規表現マッチなし")
                        continue
                    
                    title = match.group(1).strip()
                    price_str = match.group(2).replace(',', '')
                    
                    # リンク URL 取得
                    link = card.find('a', {'href': re.compile(r'/item/')})
                    if not link:
                        print(f"    [{idx}] リンクなし")
                        continue
                    
                    item_url = "https://jp.mercari.com" + link.get('href', '')
                    
                    # 結果に追加
                    item_data = {
                        'title': title,
                        'price': int(price_str),
                        'price_display': match.group(2) + '円',
                        'url': item_url,
                        'scraped_at': datetime.now().isoformat()
                    }
                    results.append(item_data)
                    page_results += 1
                    print(f"    ✅ [{idx}] {title} - ¥{match.group(2)}")
                    
                except Exception as e:
                    print(f"    ❌ [{idx}] エラー: {str(e)}")
                    continue
            
            print(f"  ✅ ページ {page} 完了: {page_results} 件取得\n")
            
        except requests.exceptions.RequestException as e:
            print(f"  ❌ リクエストエラー: {str(e)}\n")
            continue
    
    return results

# メイン実行
if __name__ == "__main__":
    print("=" * 60)
    print("メルカリ Scrape.do スクレイピング（デバッグモード）")
    print("=" * 60)
    print()
    
    # スクレイピング実行（デバッグモード）
    items = scrape_mercari_with_scrapeapi(keyword="ポケモンカード", pages=1, debug=True)
    
    print(f"\n📊 結果サマリー")
    print(f"  合計取得件数: {len(items)}")
