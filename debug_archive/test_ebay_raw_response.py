import os
from dotenv import load_dotenv
from src.utils.ebay_api_client import eBayAPIClientXML
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

app_id = os.getenv('EBAY_APP_ID')
dev_id = os.getenv('EBAY_DEV_ID')
cert_id = os.getenv('EBAY_CERT_ID')
user_token = os.getenv('EBAY_USER_TOKEN')

print("Testing eBay API with site_id='US' and ShipsFrom='JP' filter...")
client = eBayAPIClientXML(app_id, dev_id, cert_id, user_token, site_id='US')

items = client.search_sold_items("pokemon card", limit=10)

print(f"\nResult: Found {len(items)} sold items")
if items:
    print("\nFirst 3 items:")
    for i, item in enumerate(items[:3], 1):
        print(f"\n{i}. {item.get('title')}")
        print(f"   Item ID: {item.get('itemId')}")
        print(f"   Category: {item.get('category_name')} (ID: {item.get('category_id')})")
        print(f"   Price: USD {item.get('price', {}).get('value', 0)}")
        print(f"   Shipping: USD {item.get('shipping_cost', 0)}")
else:
    print("\nNo items found. Possible reasons:")
    print("- Invalid user token")
    print("- No sold items matching criteria (pokemon card + ShipsFrom JP)")
    print("- API error (check logs above)")
