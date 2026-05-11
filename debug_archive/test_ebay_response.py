import os
from dotenv import load_dotenv
from src.utils.ebay_api_client import eBayAPIClientXML
import requests

load_dotenv()

app_id = os.getenv('EBAY_APP_ID')
dev_id = os.getenv('EBAY_DEV_ID')
cert_id = os.getenv('EBAY_CERT_ID')
user_token = os.getenv('EBAY_USER_TOKEN')

client = eBayAPIClientXML(app_id, dev_id, cert_id, user_token)

# Build raw XML request
xml_request = f'''<?xml version="1.0" encoding="utf-8"?>
<GetSearchResultsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{user_token}</eBayAuthToken>
    </RequesterCredentials>
    <Query>pokemon card</Query>
    <SearchLocation>AllItemsCompleted</SearchLocation>
    <Pagination>
        <EntriesPerPage>10</EntriesPerPage>
        <PageNumber>1</PageNumber>
    </Pagination>
    <SortOrder>EndTimeNewest</SortOrder>
</GetSearchResultsRequest>'''

# Send request
headers = {
    "X-EBAY-API-APP-ID": app_id,
    "X-EBAY-API-DEV-ID": dev_id,
    "X-EBAY-API-CERT-ID": cert_id,
    "X-EBAY-API-CALL-NAME": "GetSearchResults",
    "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
    "Content-Type": "text/xml",
}

print('Sending request to eBay API...')
response = requests.post('https://api.ebay.com/ws/api.dll', data=xml_request, headers=headers)

print(f'Status Code: {response.status_code}')
print(f'Response Length: {len(response.text)} bytes')
print(f'Response (first 2000 chars):\\n{response.text[:2000]}')
