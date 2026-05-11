import os
from dotenv import load_dotenv

load_dotenv()

app_id = os.getenv('EBAY_APP_ID')
dev_id = os.getenv('EBAY_DEV_ID')
cert_id = os.getenv('EBAY_CERT_ID')
user_token = os.getenv('EBAY_USER_TOKEN')

if not all([app_id, dev_id, cert_id]):
    print('ERROR: eBay credentials not configured in .env')
    exit(1)

print('Testing eBay API connection...')
print(f'App ID: {app_id[:10]}...')
print(f'Dev ID: {dev_id[:10]}...')
print(f'Cert ID: {cert_id[:10]}...')

if user_token:
    print(f'User Token: configured')
else:
    print('User Token: NOT configured (optional)')

from src.utils.ebay_api_client import eBayAPIClientXML

client = eBayAPIClientXML(app_id, dev_id, cert_id, user_token)
print('Client created successfully!')
print('Ready to search for items...')
