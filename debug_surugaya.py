import re, csv, os, requests
from datetime import datetime

API_KEY = 'd23a98b7bf3661b85c8903ffa400721d'

# 最初のページのHTMLを取得して構造を確認
url = "https://www.suruga-ya.jp/search?category=5&search_word=ポケモンカード&searchbox=1"

print("HTMLを取得中...")
response = requests.get(
    'http://api.scraperapi.com',
    params={'api_key': API_KEY, 'url': url},
    timeout=30
)

html = response.text

# HTMLをファイルに保存
with open('surugaya_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ surugaya_debug.html に保存しました")
print(f"HTMLサイズ: {len(html)} 文字")

# 商品リンクのパターンを探す
patterns = [
    (r'<a[^>]*href="(/product/[^"]+)"[^>]*>([^<]+)</a>', 'Pattern 1: /product/ リンク'),
    (r'class="[^"]*item[^"]*"[^>]*>([^<]*)<a[^>]*href="([^"]+)"', 'Pattern 2: item クラス'),
    (r'<div[^>]*class="[^"]*card[^"]*"', 'Pattern 3: card クラス'),
    (r'<h2[^>]*>([^<]+)</h2>[^<]*<[^>]*>[\d,¥]+', 'Pattern 4: h2 タグ'),
]

print("\n🔍 各パターンのマッチ数:")
for pattern, desc in patterns:
    matches = len(re.findall(pattern, html))
    print(f"  {desc}: {matches} 件")

# 最初の500行を表示
print("\n📄 HTML の先頭部分:")
lines = html.split('\n')
for i, line in enumerate(lines[:100]):
    if any(keyword in line.lower() for keyword in ['product', 'item', 'card', 'price', '¥']):
        print(f"Line {i}: {line[:120]}")
