import os, requests, json, csv
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
CLIENT_ID = os.getenv('EBAY_REST_CLIENT_ID')
CLIENT_SECRET = os.getenv('EBAY_REST_CLIENT_SECRET')

def get_ebay_token():
    auth = (CLIENT_ID, CLIENT_SECRET)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'}
    resp = requests.post('https://api.ebay.com/identity/v1/oauth2/token', auth=auth, headers=headers, data=data, timeout=10)
    if resp.status_code == 200:
        return resp.json()['access_token']
    return None

def search_ebay(token, keyword='Pokemon Card', limit=200):
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
    params = {'q': keyword, 'limit': limit}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    return resp.json() if resp.status_code == 200 else None

def get_item_details(token, item_id):
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://api.ebay.com/buy/browse/v1/item/{item_id}'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None

def ships_to_japan(details):
    """shipToLocations に JP が含まれているか確認"""
    if 'shipToLocations' not in details:
        return False
    
    regions = details['shipToLocations'].get('regionIncluded', [])
    for region in regions:
        region_id = region.get('regionId', '').upper()
        region_name = region.get('regionName', '').upper()
        if region_id == 'JP' or 'JAPAN' in region_name:
            return True
    return False

# メイン処理
token = get_ebay_token()
if not token:
    print("❌ トークン取得失敗")
    exit()

print("🔍 eBay から Pokemon Card を検索中...\n")
data = search_ebay(token, limit=200)

if not data or 'itemSummaries' not in data:
    print("❌ 検索結果なし")
    exit()

results = []
checked = 0
ships_to_japan_count = 0

for item in data['itemSummaries']:
    item_id = item['itemId']
    title = item.get('title', 'N/A')
    price = item.get('price', {}).get('value', 'N/A')
    seller = item.get('seller', {}).get('username', 'N/A')
    
    # 詳細情報取得
    details = get_item_details(token, item_id)
    checked += 1
    
    if details and ships_to_japan(details):
        ships_to_japan_count += 1
        results.append({
            'title': title,
            'price': price,
            'seller': seller,
            'item_id': item_id,
            'ships_to_japan': 'Yes',
            'scraped_at': datetime.now().isoformat()
        })
        print(f"✓ [{ships_to_japan_count}] {title[:60]} - ${price} - {seller}")
    else:
        print(f"✗ {title[:60]} - {seller} (日本発送なし)")
    
    if checked >= 50:  # 最初の50件まで確認
        break

print(f"\n{'='*60}")
print(f"📊 結果: {ships_to_japan_count}/{checked} 件が日本発送可能")
print(f"{'='*60}\n")

if results:
    os.makedirs('data/imports', exist_ok=True)
    filename = 'data/imports/ebay_pokemon_cards_japan_ships.csv'
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['title', 'price', 'seller', 'item_id', 'ships_to_japan', 'scraped_at'])
        w.writeheader()
        w.writerows(results)
    print(f"✅ {len(results)} 件を {filename} に保存しました")
else:
    print("❌ 日本発送可能な商品が見つかりません")
