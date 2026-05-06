import os, requests, json
from dotenv import load_dotenv

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

def get_item_details(token, item_id):
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://api.ebay.com/buy/browse/v1/item/{item_id}'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def search_ebay(token, keyword='Pokemon Card', limit=3):
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
    params = {'q': keyword, 'limit': limit, 'filter': 'deliveryCountry:JP'}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    return resp.json() if resp.status_code == 200 else None

token = get_ebay_token()
if token:
    data = search_ebay(token, limit=3)
    if data and 'itemSummaries' in data:
        for item in data['itemSummaries'][:1]:  # 最初の1件のみ詳細取得
            item_id = item['itemId']
            print(f"\n📦 {item.get('title', 'N/A')[:60]}")
            print(f"Seller: {item.get('seller', {}).get('username')}")
            
            details = get_item_details(token, item_id)
            if details and 'shippingOptions' in details:
                print(f"\n🚚 配送オプション:")
                for opt in details['shippingOptions'][:5]:
                    country = opt.get('shippingCostType', 'N/A')
                    cost = opt.get('shippingCost', {}).get('value', 'N/A')
                    carrier = opt.get('shippingCarrierCode', 'N/A')
                    print(f"  - {carrier}: {cost} (type: {country})")
            else:
                print("配送情報が取得できません")
