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
    resp = requests.get(url, headers=headers, timeout=10)
    return resp.json() if resp.status_code == 200 else None

def search_ebay(token, keyword='Pokemon Card', limit=1):
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
    params = {'q': keyword, 'limit': limit, 'filter': 'deliveryCountry:JP'}
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    return resp.json() if resp.status_code == 200 else None

token = get_ebay_token()
if token:
    data = search_ebay(token, limit=1)
    if data and 'itemSummaries' in data:
        item_id = data['itemSummaries'][0]['itemId']
        details = get_item_details(token, item_id)
        if details:
            print("=== shippingOptions の全情報 ===\n")
            if 'shippingOptions' in details:
                print(json.dumps(details['shippingOptions'], indent=2, ensure_ascii=False))
            else:
                print("shippingOptions が見つかりません")
            
            print("\n=== 他の配送関連フィールド ===")
            for key in ['estimatedDeliveries', 'shipToLocations', 'seller']:
                if key in details:
                    print(f"\n{key}:")
                    print(json.dumps(details[key], indent=2, ensure_ascii=False)[:500])
