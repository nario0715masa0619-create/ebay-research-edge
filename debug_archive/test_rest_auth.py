import os
from dotenv import load_dotenv
import requests
import base64

load_dotenv()

client_id = os.getenv('EBAY_REST_CLIENT_ID')
client_secret = os.getenv('EBAY_REST_CLIENT_SECRET')

if not client_id or not client_secret:
    print("ERROR: EBAY_REST_CLIENT_ID or EBAY_REST_CLIENT_SECRET not set in .env")
    exit(1)

print("Testing eBay REST API (OAuth 2.0)...")
print(f"Client ID: {client_id[:20]}...")

# Get OAuth token
credentials = f"{client_id}:{client_secret}"
encoded = base64.b64encode(credentials.encode()).decode()

response = requests.post(
    "https://api.ebay.com/identity/v1/oauth2/token",
    headers={
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded"
    },
    data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"}
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get('access_token')
    print(f"✓ Access Token obtained: {access_token[:50]}...")
    print(f"Expires in: {token_data.get('expires_in')} seconds")
    
    # Now test Browse API search
    print("\nTesting Browse API search...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    search_response = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers=headers,
        params={
            "q": "pokemon card",
            "filter": "itemLocationCountry:JP",
            "sort": "-soldDate",
            "limit": 10
        }
    )
    
    print(f"Search Status: {search_response.status_code}")
    print(f"Search Response (first 500 chars):")
    print(search_response.text[:500])
    
else:
    print(f"✗ Error: {response.status_code}")
    print(f"Response: {response.text}")
