import os
from dotenv import load_dotenv
import requests
import xml.etree.ElementTree as ET

load_dotenv()

app_id = os.getenv('EBAY_APP_ID')
dev_id = os.getenv('EBAY_DEV_ID')
cert_id = os.getenv('EBAY_CERT_ID')
user_token = os.getenv('EBAY_USER_TOKEN')

print("Sending raw request to eBay API...")

request_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<GetSearchResultsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{user_token}</eBayAuthToken>
    </RequesterCredentials>
    <Query>pokemon card</Query>
    <FindCompletedItems>true</FindCompletedItems>
    <SortOrder>EndTimeNewest</SortOrder>
    <Pagination>
        <EntriesPerPage>10</EntriesPerPage>
        <PageNumber>1</PageNumber>
    </Pagination>
    <ItemFilter>
        <Name>SoldItemsOnly</Name>
        <Value>true</Value>
    </ItemFilter>
    <ItemFilter>
        <Name>ShipsFrom</Name>
        <Value>JP</Value>
    </ItemFilter>
</GetSearchResultsRequest>'''

headers = {
    "X-EBAY-API-CALL-NAME": "GetSearchResults",
    "X-EBAY-API-APP-ID": app_id,
    "X-EBAY-API-DEV-ID": dev_id,
    "X-EBAY-API-CERT-ID": cert_id,
    "X-EBAY-API-SITEID": "0",
    "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
    "Content-Type": "text/xml; charset=utf-8",
}

response = requests.post("https://api.ebay.com/ws/api.dll", headers=headers, data=request_body)

print(f"Status Code: {response.status_code}")
print(f"Response Length: {len(response.text)} bytes")
print(f"\nResponse (full):")
print(response.text)

# Try to parse and extract error messages
try:
    root = ET.fromstring(response.text)
    
    # Check for errors
    errors = root.findall('.//{urn:ebay:apis:eBLBaseComponents}Error')
    if errors:
        print("\n\nErrors found:")
        for error in errors:
            short_msg = error.findtext('{urn:ebay:apis:eBLBaseComponents}ShortMessage', 'N/A')
            long_msg = error.findtext('{urn:ebay:apis:eBLBaseComponents}LongMessage', 'N/A')
            error_code = error.findtext('{urn:ebay:apis:eBLBaseComponents}ErrorCode', 'N/A')
            print(f"  Code: {error_code}")
            print(f"  Short: {short_msg}")
            print(f"  Long: {long_msg}\n")
    
    # Check SearchResultItemArray
    result_count = root.findtext('.//{urn:ebay:apis:eBLBaseComponents}PaginationResult/{urn:ebay:apis:eBLBaseComponents}TotalNumberOfEntries', 'N/A')
    print(f"Total Results in API: {result_count}")
    
except Exception as e:
    print(f"Parse error: {e}")
