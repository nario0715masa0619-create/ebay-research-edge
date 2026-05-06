import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from src.fetcher.base_fetcher import BaseFetcher

class EBayBrowseFetcher(BaseFetcher):
    """eBay Browse API を使用した実装"""
    
    def __init__(self):
        load_dotenv()
        self.user_token = os.getenv('EBAY_REST_USER_TOKEN')
        if not self.user_token:
            raise ValueError('EBAY_REST_USER_TOKEN not set in .env')
        
        self.base_url = 'https://api.ebay.com/buy/browse/v1'
        self.headers = {
            'Authorization': f'Bearer {self.user_token}',
            'Content-Type': 'application/json'
        }
    
    def search(self, query: str, limit: int = 50, **filters) -> List[Dict]:
        """
        Browse API で検索
        
        Args:
            query: 検索キーワード
            limit: 取得件数（デフォルト50）
            **filters: フィルター（例：itemLocationCountry='JP'）
        
        Returns:
            標準化されたアイテムリスト
        """
        params = {
            'q': query,
            'limit': min(limit, 200),  # Browse API max 200
            'sort': '-price'
        }
        
        # フィルター処理
        if 'itemLocationCountry' in filters:
            params['filter'] = f"itemLocationCountry:{filters['itemLocationCountry']}"
        
        try:
            response = requests.get(
                f'{self.base_url}/item_summary/search',
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get('itemSummaries', [])
            
            # 標準化
            return [self._normalize_item(item) for item in items]
        
        except requests.exceptions.RequestException as e:
            print(f'✗ Browse API Error: {e}')
            return []
    
    def get_item_details(self, item_id: str) -> Dict:
        """アイテム詳細取得"""
        try:
            response = requests.get(
                f'{self.base_url}/item/{item_id}',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            item = response.json()
            return self._normalize_item(item)
        
        except requests.exceptions.RequestException as e:
            print(f'✗ Get Item Details Error: {e}')
            return {}
    
    def _normalize_item(self, item: Dict) -> Dict:
        """Browse API のレスポンスを標準フォーマットに変換"""
        price_obj = item.get('price', {})
        location = item.get('itemLocation', {})
        
        return {
            'item_id': item.get('itemId', ''),
            'title': item.get('title', ''),
            'price': float(price_obj.get('value', 0)),
            'currency': price_obj.get('currency', 'USD'),
            'url': item.get('itemWebUrl', ''),
            'condition': item.get('condition', 'Unknown'),
            'ships_from': location.get('country', 'Unknown'),
            'source': 'eBay Browse API'
        }
