import os
from dotenv import load_dotenv

load_dotenv()

app_id = os.getenv('EBAY_APP_ID')
dev_id = os.getenv('EBAY_DEV_ID')
cert_id = os.getenv('EBAY_CERT_ID')
user_token = os.getenv('EBAY_USER_TOKEN')

from src.utils.ebay_api_client import eBayAPIClientXML

print('Initializing eBay API client...')
client = eBayAPIClientXML(app_id, dev_id, cert_id, user_token)

print('Searching for sold Pokemon cards on eBay...')
items = client.search_sold_items('pokemon card', limit=5)

if items:
    print(f'Found {len(items)} items!\n')
    for i, item in enumerate(items, 1):
        print(f'Item {i}:')
        print(f'  Title: {item.get("title")}')
        print(f'  Item ID: {item.get("itemId")}')
        print(f'  Category ID: {item.get("category_id")}')
        print(f'  Category Name: {item.get("category_name")}')
        print(f'  Price: USD {item.get("price", {}).get("value", 0)}')
        print()
else:
    print('No items found. Check API credentials or user token.')
