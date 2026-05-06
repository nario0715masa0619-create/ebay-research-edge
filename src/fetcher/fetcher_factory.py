from typing import Optional
from src.fetcher.base_fetcher import BaseFetcher
from src.fetcher.ebay_browse_fetcher import EBayBrowseFetcher
from src.fetcher.ebay_insights_fetcher import EBayInsightsFetcher

class FetcherFactory:
    """
    eBay Fetcher のファクトリークラス
    
    設定を変更するだけで、Browse API ↔ Marketplace Insights API を切り替え可能
    """
    
    # 利用可能な Fetcher
    AVAILABLE_FETCHERS = {
        'browse': EBayBrowseFetcher,
        'insights': EBayInsightsFetcher,
    }
    
    # デフォルト（当面は browse を使用）
    DEFAULT_FETCHER = 'browse'
    
    @staticmethod
    def create_fetcher(fetcher_type: Optional[str] = None) -> BaseFetcher:
        """
        Fetcher インスタンスを作成
        
        Args:
            fetcher_type: 'browse' または 'insights'
                         None の場合は DEFAULT_FETCHER を使用
        
        Returns:
            BaseFetcher インスタンス
        
        Example:
            # 当面は Browse API
            fetcher = FetcherFactory.create_fetcher()
            
            # または明示的に指定
            fetcher = FetcherFactory.create_fetcher('browse')
            
            # 将来、Marketplace Insights API が利用可能になったら
            fetcher = FetcherFactory.create_fetcher('insights')
        """
        if fetcher_type is None:
            fetcher_type = FetcherFactory.DEFAULT_FETCHER
        
        if fetcher_type not in FetcherFactory.AVAILABLE_FETCHERS:
            raise ValueError(
                f'Unknown fetcher type: {fetcher_type}. '
                f'Available: {list(FetcherFactory.AVAILABLE_FETCHERS.keys())}'
            )
        
        fetcher_class = FetcherFactory.AVAILABLE_FETCHERS[fetcher_type]
        return fetcher_class()
    
    @staticmethod
    def list_available_fetchers():
        """利用可能な Fetcher のリストを表示"""
        return list(FetcherFactory.AVAILABLE_FETCHERS.keys())
    
    @staticmethod
    def get_current_fetcher() -> str:
        """現在のデフォルト Fetcher を取得"""
        return FetcherFactory.DEFAULT_FETCHER
    
    @staticmethod
    def set_default_fetcher(fetcher_type: str):
        """デフォルト Fetcher を変更"""
        if fetcher_type not in FetcherFactory.AVAILABLE_FETCHERS:
            raise ValueError(f'Unknown fetcher type: {fetcher_type}')
        FetcherFactory.DEFAULT_FETCHER = fetcher_type
        print(f'✓ Default fetcher changed to: {fetcher_type}')
