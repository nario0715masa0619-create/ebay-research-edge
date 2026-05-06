"""
eBay Trading API Client - XML API

Handles authentication and API calls to eBay Trading API.
"""

import logging
import os
from typing import Dict, Any, Optional, List
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class eBayAPIClientXML:
    """eBay Trading API client for sold listings and item details."""

    # eBay API endpoints
    TRADING_API_URL = "https://api.ebay.com/ws/api.dll"
    
    # Site ID mappings
    SITE_IDS = {
        'US': 0,
        'UK': 3,
        'CA': 2,
        'JP': 205,
        'DE': 77,
        'FR': 71,
        'AU': 15,
    }

    def __init__(self, app_id: str, dev_id: str, cert_id: str, user_token: Optional[str] = None, site_id: str = 'US'):
        """Initialize eBay Trading API client."""
        self.app_id = app_id
        self.dev_id = dev_id
        self.cert_id = cert_id
        self.user_token = user_token
        self.site_id = site_id
        self.site_id_value = self.SITE_IDS.get(site_id, 0)
        logger.info(f"eBayAPIClientXML initialized (Site: {site_id} = {self.site_id_value})")

    def _build_request_headers(self) -> Dict[str, str]:
        """Build eBay API request headers."""
        return {
            "X-EBAY-API-CALL-NAME": "GetSearchResults",
            "X-EBAY-API-APP-ID": self.app_id,
            "X-EBAY-API-DEV-ID": self.dev_id,
            "X-EBAY-API-CERT-ID": self.cert_id,
            "X-EBAY-API-SITEID": str(self.site_id_value),
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "Content-Type": "text/xml; charset=utf-8",
        }

    def _build_search_request(self, query: str, limit: int = 100, find_completed: bool = True) -> str:
        """Build XML request for GetSearchResults."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<GetSearchResultsRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{self.user_token}</eBayAuthToken>
    </RequesterCredentials>
    <Query>{query}</Query>
    <FindCompletedItems>{str(find_completed).lower()}</FindCompletedItems>
    <SortOrder>EndTimeNewest</SortOrder>
    <Pagination>
        <EntriesPerPage>{min(limit, 100)}</EntriesPerPage>
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

    def search_sold_items(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search for sold items by keyword."""
        logger.info(f"Searching eBay ({self.site_id}) Trading API for: {keyword}")
        
        request_body = self._build_search_request(keyword, limit)
        headers = self._build_request_headers()

        try:
            response = requests.post(self.TRADING_API_URL, headers=headers, data=request_body)
            response.raise_for_status()
            
            items = self._parse_search_response(response.text)
            logger.info(f"Found {len(items)} sold items for keyword: {keyword}")
            return items
        except Exception as e:
            logger.error(f"Error searching eBay API: {e}")
            return []

    def _parse_search_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse XML response from GetSearchResults."""
        items = []
        try:
            root = ET.fromstring(response_text)
            ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
            
            # Extract items from response
            for item_elem in root.findall('.//ebay:SearchResultItem', ns):
                try:
                    item_id = item_elem.findtext('ebay:Item/ebay:ItemID', '', ns)
                    title = item_elem.findtext('ebay:Item/ebay:Title', '', ns)
                    price_text = item_elem.findtext('ebay:Item/ebay:CurrentPrice', '', ns)
                    category_id = item_elem.findtext('ebay:Item/ebay:PrimaryCategory/ebay:CategoryID', '', ns)
                    category_name = item_elem.findtext('ebay:Item/ebay:PrimaryCategory/ebay:CategoryName', '', ns)
                    shipping = item_elem.findtext('ebay:Item/ebay:ShippingInfo/ebay:ShippingServiceCost', '', ns)
                    
                    # Try to get end time (sold date)
                    end_time = item_elem.findtext('ebay:Item/ebay:EndTime', '', ns)
                    
                    items.append({
                        'itemId': item_id,
                        'title': title,
                        'price': {
                            'value': float(price_text) if price_text else 0.0,
                            'currency': 'USD'
                        },
                        'category_id': category_id,
                        'category_name': category_name,
                        'shipping_cost': float(shipping) if shipping else 0.0,
                        'end_time': end_time,
                    })
                except Exception as e:
                    logger.warning(f"Error parsing item: {e}")
                    continue
            
            return items
        except ET.ParseError as e:
            logger.error(f"XML Parse Error: {e}")
            logger.debug(f"Response text (first 1000 chars): {response_text[:1000]}")
            return []

    def get_item_details(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific item."""
        request_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{self.user_token}</eBayAuthToken>
    </RequesterCredentials>
    <ItemID>{item_id}</ItemID>
    <IncludeSelector>Details,Description</IncludeSelector>
</GetItemRequest>'''
        
        headers = {
            "X-EBAY-API-CALL-NAME": "GetItem",
            "X-EBAY-API-APP-ID": self.app_id,
            "X-EBAY-API-DEV-ID": self.dev_id,
            "X-EBAY-API-CERT-ID": self.cert_id,
            "X-EBAY-API-SITEID": str(self.site_id_value),
            "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
            "Content-Type": "text/xml; charset=utf-8",
        }

        try:
            response = requests.post(self.TRADING_API_URL, headers=headers, data=request_body)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            ns = {'ebay': 'urn:ebay:apis:eBLBaseComponents'}
            
            return {
                'itemId': root.findtext('ebay:Item/ebay:ItemID', '', ns),
                'title': root.findtext('ebay:Item/ebay:Title', '', ns),
                'description': root.findtext('ebay:Item/ebay:Description', '', ns),
            }
        except Exception as e:
            logger.error(f"Error getting item details: {e}")
            return None


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    app_id = os.getenv("EBAY_APP_ID")
    dev_id = os.getenv("EBAY_DEV_ID")
    cert_id = os.getenv("EBAY_CERT_ID")
    user_token = os.getenv("EBAY_USER_TOKEN")
    
    if not all([app_id, dev_id, cert_id, user_token]):
        print("ERROR: eBay credentials not configured in .env")
        exit(1)
    
    client = eBayAPIClientXML(app_id, dev_id, cert_id, user_token, site_id='US')
    items = client.search_sold_items("pokemon card", limit=5)
    
    print(f"\nFound {len(items)} items:")
    for item in items[:3]:
        print(f"  - {item.get('title')} (ID: {item.get('itemId')})")
        print(f"    Price: USD {item.get('price', {}).get('value', 0)}")
        print(f"    Category: {item.get('category_name')} (ID: {item.get('category_id')})")
