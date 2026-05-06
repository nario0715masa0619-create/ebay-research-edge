import os
import logging
from dotenv import load_dotenv

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

app_id = os.getenv('EBAY_APP_ID')
dev_id = os.getenv('EBAY_DEV_ID')
cert_id = os.getenv('EBAY_CERT_ID')
user_token = os.getenv('EBAY_USER_TOKEN')

print('Credentials loaded:')
print(f'App ID: {app_id}')
print(f'Dev ID: {dev_id}')
print(f'Cert ID: {cert_id}')
print(f'User Token: {user_token[:50]}...' if user_token else 'User Token: None')

from src.utils.ebay_api_client import eBayAPIClientXML

print('\nInitializing client...')
client = eBayAPIClientXML(app_id, dev_id, cert_id, user_token)

print('Calling search_sold_items()...')
try:
    items = client.search_sold_items('pokemon card', limit=5)
    print(f'Result: {len(items)} items found')
    if items:
        print(f'First item: {items[0]}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
