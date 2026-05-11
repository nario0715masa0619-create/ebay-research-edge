import os, requests, json
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('EBAY_REST_CLIENT_ID')
CLIENT_SECRET = os.getenv('EBAY_REST_CLIENT_SECRET')

def get_ebay_token():
    url = "https://api.ebay.com/identity/v1/oauth2/token"
    auth = (CLIENT_ID, CLIENT_SECRET)
    data = {"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
    response = requests.post(url, auth=auth, data=data)
    return response.json()['access_token'] if response.status_code == 200 else None

def search_ebay_pokemon_cards(token):
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": "Pokemon Card", "limit": 5}
    response = requests.get(url, headers=headers, params=params)
    return response.json() if response.status_code == 200 else None

def get_item_details(token, item_id):
    url = f"https://api.ebay.com/buy/browse/v1/item/{item_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

# 実行
token = get_ebay_token()
if not token:
    print("❌ トークン取得失敗")
else:
    print("✓ トークン取得成功\n")
    
    data = search_ebay_pokemon_cards(token)
    if data and 'itemSummaries' in data:
        item = data['itemSummaries'][0]
        item_id = item['itemId']
        
        print(f"テスト商品: {item['title'][:60]}\n")
        
        # 詳細情報取得
        details = get_item_details(token, item_id)
        
        if details:
            print("=== itemLocation ===")
            item_location = details.get('itemLocation', {})
            print(json.dumps(item_location, indent=2, ensure_ascii=False))
            
            print("\n=== shippingOptions ===")
            shipping_options = details.get('shippingOptions', [])
            for i, option in enumerate(shipping_options[:3]):
                print(f"\n[{i}]")
                print(json.dumps(option, indent=2, ensure_ascii=False)[:500])
