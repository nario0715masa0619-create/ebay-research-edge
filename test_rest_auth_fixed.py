import os
from dotenv import load_dotenv
import requests

load_dotenv()

user_token = os.getenv('EBAY_REST_USER_TOKEN')

if not user_token:
    print("ERROR: EBAY_REST_USER_TOKEN not set in .env")
    exit(1)

print("Testing eBay REST API (OAuth 2.0) with User Token...")
print(f"User Token: {user_token[:50]}...")

# Use the User Token directly (no client_credentials)
headers = {
    "Authorization": f"Bearer {user_token}",
    "Content-Type": "application/json"
}

print("\nTesting Browse API search...")
response = requests.get(
    "https://api.ebay.com/buy/browse/v1/item_summary/search",
    headers=headers,
    params={
        "q": "pokemon card",
        "filter": "itemLocationCountry:JP",
        "sort": "-soldDate",
        "limit": 10
    }
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    items = data.get('itemSummaries', [])
    print(f"\n✓ Success! Found {len(items)} items")
    if items:
        print(f"\nFirst item:")
        item = items[0]
        print(f"  Title: {item.get('title')}")
        print(f"  Item ID: {item.get('itemId')}")
        print(f"  Price: {item.get('price', {}).get('value')} {item.get('price', {}).get('currency')}")
else:
    print(f"\n✗ Error: {response.status_code}")
    print(f"Response: {response.text[:500]}")
