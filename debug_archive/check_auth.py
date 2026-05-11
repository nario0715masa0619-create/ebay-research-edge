import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv('EBAY_REST_CLIENT_ID')
client_secret = os.getenv('EBAY_REST_CLIENT_SECRET')

print(f"Client ID length: {len(client_id)}")
print(f"Client ID: {client_id}")
print()
print(f"Client Secret length: {len(client_secret)}")
print(f"Client Secret: {client_secret}")
print()

# Check if contains special characters
if ':' in client_id or ':' in client_secret:
    print("WARNING: Client ID/Secret contains colons")
if ' ' in client_id or ' ' in client_secret:
    print("WARNING: Client ID/Secret contains spaces")

print("\nFor OAuth 2.0, the format should be:")
print("Client ID: Masakazu-MarketAn-PRD-xxxxx")
print("Client Secret: PRD-xxxxx")
