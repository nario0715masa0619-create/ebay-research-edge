from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseFetcher(ABC):
    """eBay データ取得の抽象インターフェース"""
    
    @abstractmethod
    def search(self, query: str, limit: int = 50, **filters) -> List[Dict]:
        """
        キーワード検索
        
        Returns:
            [
                {
                    'item_id': str,
                    'title': str,
                    'price': float,
                    'currency': str,
                    'url': str,
                    'condition': str,
                    'ships_from': str,
                    'source': str (API名)
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def get_item_details(self, item_id: str) -> Dict:
        """アイテム詳細取得"""
        pass
