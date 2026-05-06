import re, csv, os, requests
from datetime import datetime

def scrape_surugaya_api(keyword='ポケモンカード', max_pages=None):
    """ScraperAPI を使用して駿河屋をスクレイピング"""
    API_KEY = 'd23a98b7bf3661b85c8903ffa400721d'
    results = []
    
    # 最初のページでページ数を判定
    url = f"https://www.suruga-ya.jp/search?category=5&search_word={keyword}&searchbox=1"
    
    print(f"\nURL: {url}")
    print("ページ読み込み中...")
    
    try:
        response = requests.get(
            'http://api.scraperapi.com',
            params={'api_key': API_KEY, 'url': url},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ APIエラー: {response.status_code}")
            print(f"レスポンス: {response.text[:200]}")
            return results
        
        # ページネーション検出
        max_page = 1
        if 'page=' in response.text:
            matches = re.findall(r'page=(\d+)', response.text)
            if matches:
                max_page = max(int(m) for m in matches)
        
        print(f"✓ 総ページ数: {max_page} ページ\n")
        
        if max_pages:
            max_page = min(max_page, max_pages)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return results
    
    # 各ページをスクレイピング
    for page_num in range(1, max_page + 1):
        url = f"https://www.suruga-ya.jp/search?category=5&search_word={keyword}&page={page_num}&searchbox=1"
        print(f"ページ {page_num}/{max_page}: ", end='', flush=True)
        
        try:
            response = requests.get(
                'http://api.scraperapi.com',
                params={'api_key': API_KEY, 'url': url},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ エラー（{response.status_code}）")
                continue
            
            html = response.text
            
            # 商品情報を正規表現で抽出
            product_pattern = r'<a\s+href="(/product/[^"]+)">([^<]+)</a>'
            price_pattern = r'￥([\d,]+)'
            
            matches = re.finditer(product_pattern, html)
            page_count = 0
            seen_titles = set()
            
            for match in matches:
                try:
                    link = match.group(1)
                    title = match.group(2).strip()
                    
                    # 重複チェック
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    # 価格を同じセクションから抽出
                    section_start = max(0, match.start() - 200)
                    section_end = min(len(html), match.end() + 500)
                    section = html[section_start:section_end]
                    
                    price_match = re.search(price_pattern, section)
                    if price_match:
                        price = price_match.group(1).replace(',', '')
                    else:
                        continue
                    
                    if not link.startswith('http'):
                        link = 'https://www.suruga-ya.jp' + link
                    
                    results.append({
                        'title': title,
                        'price': price,
                        'url': link,
                        'scraped_at': datetime.now().isoformat()
                    })
                    page_count += 1
                except:
                    continue
            
            print(f"✓ {page_count} 件取得（累計 {len(results)} 件）")
            
        except Exception as e:
            print(f"❌ エラー: {str(e)[:30]}")
            continue
    
    return results

def save_csv(items):
    os.makedirs('data/imports', exist_ok=True)
    filename = 'data/imports/surugaya_scrape.csv'
    if not items:
        print("\n❌ データなし")
        return
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['title','price','url','scraped_at'])
        w.writeheader()
        w.writerows(items)
    print(f"✅ {len(items)} 件を {filename} に保存")

def main():
    print("\n" + "="*60)
    print("駿河屋 スクレイピング開始（ScraperAPI）")
    print("="*60)
    
    items = scrape_surugaya_api(keyword='ポケモンカード', max_pages=100)
    
    print(f"\n{'='*60}")
    print(f"📊 完了")
    print(f"{'='*60}")
    print(f"合計: {len(items)} 件")
    
    if items:
        prices = [int(i['price']) for i in items if i['price'].isdigit()]
        if prices:
            print(f"平均: ¥{sum(prices)//len(prices):,}")
            print(f"最安: ¥{min(prices):,}")
            print(f"最高: ¥{max(prices):,}")
        save_csv(items)
        print("\n✨ 成功！")

if __name__ == '__main__':
    main()
