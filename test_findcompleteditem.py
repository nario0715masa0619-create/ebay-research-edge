import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET

load_dotenv()

app_id = os.getenv('EBAY_APP_ID')
dev_id = os.getenv('EBAY_DEV_ID')
cert_id = os.getenv('EBAY_CERT_ID')
user_token = os.getenv('EBAY_USER_TOKEN')

print("Testing FindCompletedItems operation...")

# Use FindCompletedItems instead
request_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<FindCompletedItemsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{user_token}</eBayAuthToken>
    </RequesterCredentials>
    <Query>pokemon card</Query>
    <SortOrder>EndTimeNewest</SortOrder>
    <Pagination>
        <EntriesPerPage>10</EntriesPerPage>
        <PageNumber>1</PageNumber>
    </Pagination>
</FindCompletedItemsRequest>'''

headers = {
    "X-EBAY-API-CALL-NAME": "FindCompletedItems",
    "X-EBAY-API-APP-ID": app_id,
    "X-EBAY-API-DEV-ID": dev_id,
    "X-EBAY-API-CERT-ID": cert_id,
    "X-EBAY-API-SITEID": "0",
    "X-EBAY-API-COMPATIBILITY-LEVEL": "1231",
    "Content-Type": "text/xml; charset=utf-8",
}

print(f"Headers: {headers['X-EBAY-API-CALL-NAME']}")
response = requests.post("https://api.ebay.com/ws/api.dll", headers=headers, data=request_body)

print(f"Status Code: {response.status_code}")
print(f"Response (first 1500 chars):")
print(response.text[:1500])

# Parse response
try:
    root = ET.fromstring(response.text)
    
    # Check for errors
    errors = root.findall('.//{urn:ebay:apis:eBLBaseComponents}Error')
    if errors:
        print("\n\nErrors found:")
        for error in errors:
            short_msg = error.findtext('{urn:ebay:apis:eBLBaseComponents}ShortMessage', 'N/A')
            error_code = error.findtext('{urn:ebay:apis:eBLBaseComponents}ErrorCode', 'N/A')
            print(f"  Code: {error_code} - {short_msg}")
    else:
        print("\n\nNo errors! Parsing items...")
        items = root.findall('.//{urn:ebay:apis:eBLBaseComponents}SearchResultItem')
        print(f"Found {len(items)} items")
        if items:
            for i, item in enumerate(items[:2], 1):
                title = item.findtext('{urn:ebay:apis:eBLBaseComponents}Item/{urn:ebay:apis:eBLBaseComponents}Title', 'N/A')
                print(f"  {i}. {title}")
    
except Exception as e:
    print(f"Parse error: {e}")
