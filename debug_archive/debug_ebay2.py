import os, requests, json
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('EBAY_REST_CLIENT_ID')
CLIENT_SECRET = os.getenv('EBAY_REST_CLIENT_SECRET')

print(f"CLIENT_ID exists: {bool(CLIENT_ID)}")
print(f"CLIENT_SECRET exists: {bool(CLIENT_SECRET)}")

def get_ebay_token():
    auth = (CLIENT_ID, CLIENT_SECRET)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'}
    try:
        print("\n🔐 トークン取得中...")
        resp = requests.post('https://api.ebay.com/identity/v1/oauth2/token', auth=auth, headers=headers, data=data, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            token = resp.json()['access_token']
            print(f"✓ トークン取得成功: {token[:50]}...")
            return token
        else:
            print(f"❌ エラー: {resp.status_code}")
            print(f"レスポンス: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ 例外: {e}")
        return None

def search_ebay(token, keyword='Pokemon Card', limit=5):
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
    params = {
        'q': keyword,
        'limit': limit,
        'filter': 'deliveryCountry:JP'
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"\n検索Status: {resp.status_code}")
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"エラー: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"例外: {e}")
        return None

token = get_ebay_token()
if token:
    print('\n✓ トークン取得成功\n')
    data = search_ebay(token, limit=5)
    if data and 'itemSummaries' in data:
        print(f"取得件数: {len(data['itemSummaries'])}\n")
        for idx, item in enumerate(data['itemSummaries'][:3], 1):
            print(f"{idx}. {item.get('title', 'N/A')}")
            print(f"   ID: {item.get('itemId')}")
            print(f"   Seller: {item.get('seller', {}).get('username', 'N/A')}")
            print(f"   Price: {item.get('price', {}).get('value')} {item.get('price', {}).get('currency')}")
            print()
    else:
        print("❌ 検索結果がありません")
else:
    print('❌ トークン取得失敗')
