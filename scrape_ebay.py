import os, csv, time
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('EBAY_REST_CLIENT_ID')
CLIENT_SECRET = os.getenv('EBAY_REST_CLIENT_SECRET')

def get_ebay_token():
    """OAuth 2.0 トークン取得"""
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    auth = (CLIENT_ID, CLIENT_SECRET)
    data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
    
    response = requests.post(url, auth=auth, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        print(f"❌ トークン取得失敗: {response.status_code}")
        return None

def search_ebay_pokemon_cards(token, offset=0, limit=200):
    """eBay Browse API でポケモンカード検索"""
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {
        "q": "Pokemon Card",
        "limit": limit,
        "offset": offset
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ API エラー: {response.status_code}")
        return None

def get_item_details(token, item_id):
    """商品詳細情報取得（セラー情報）"""
    url = f"https://api.ebay.com/buy/browse/v1/item/{item_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_ships_from_japan(details):
    """日本からの発送かどうか確認"""
    if not details:
        return False
    
    # セラー情報を確認
    seller = details.get('seller', {})
    
    # seller_location を確認
    seller_location = seller.get('sellerLocation', '')
    
    if seller_location and 'JP' in seller_location or 'Japan' in seller_location:
        return True
    
    return False

def main():
    print("\n" + "="*60)
    print("eBay Browse API - 日本発送セラーのポケモンカード検索")
    print("="*60)
    
    # トークン取得
    print("\n🔐 トークン取得中...")
    token = get_ebay_token()
    if not token:
        print("❌ トークン取得失敗")
        return
    
    print("✓ トークン取得成功\n")
    
    # API検索
    print("🔍 eBay を検索中...")
    data = search_ebay_pokemon_cards(token, offset=0, limit=200)
    
    if not data or 'itemSummaries' not in data:
        print("❌ 検索結果なし")
        return
    
    items = data['itemSummaries']
    print(f"✓ {len(items)} 件の商品を取得\n")
    
    # 各商品の詳細情報を取得してセラー確認
    print("📋 詳細情報取得中（セラー位置確認）...\n")
    
    results = []
    japan_count = 0
    
    for idx, item in enumerate(items, 1):
        try:
            item_id = item.get('itemId', '')
            title = item.get('title', '')
            price = item.get('price', {}).get('value', '')
            
            print(f"[{idx}/{len(items)}] {title[:60]}", end=' → ')
            
            # 詳細情報取得
            details = get_item_details(token, item_id)
            time.sleep(0.5)  # API レート制限対策
            
            # 日本からの発送確認
            ships_from_japan = check_ships_from_japan(details)
            seller_location = details.get('seller', {}).get('sellerLocation', '') if details else 'Unknown'
            
            if ships_from_japan:
                print(f"✓ 日本発送（{seller_location}）")
                japan_count += 1
                
                results.append({
                    'title': title,
                    'price': price,
                    'currency': item.get('price', {}).get('currency', ''),
                    'condition': item.get('condition', ''),
                    'seller_name': item.get('seller', {}).get('username', ''),
                    'seller_location': seller_location,
                    'item_id': item_id,
                    'item_url': item.get('itemWebUrl', ''),
                    'image_url': item.get('image', {}).get('imageUrl', ''),
                    'ships_from_japan': 'Yes',
                    'scraped_at': datetime.now().isoformat()
                })
            else:
                print(f"✗ 日本発送不可（{seller_location}）")
        
        except Exception as e:
            print(f"❌ エラー: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"📊 結果")
    print(f"{'='*60}")
    print(f"全商品: {len(items)} 件")
    print(f"日本発送セラー: {japan_count} 件\n")
    
    # CSV に保存
    if results:
        os.makedirs('data/imports', exist_ok=True)
        filename = 'data/imports/ebay_pokemon_cards_japan.csv'
        
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['title','price','currency','condition','seller_name','seller_location','item_id','item_url','image_url','ships_from_japan','scraped_at'])
            w.writeheader()
            w.writerows(results)
        
        print(f"✅ {len(results)} 件を {filename} に保存\n")
        
        # 統計
        prices = [float(r['price']) for r in results if r['price']]
        if prices:
            print(f"平均価格: ${sum(prices)/len(prices):.2f}")
            print(f"最安値: ${min(prices):.2f}")
            print(f"最高値: ${max(prices):.2f}")
    else:
        print("❌ 日本発送セラーの商品がありません")

if __name__ == '__main__':
    main()
