import re
import logging
from typing import List
from src.models.data_models import MarketRecord
from src.config.config import config

logger = logging.getLogger(__name__)


class Normalizer:
    """商品情報を正規化するクラス"""
    
    def __init__(self):
        self.config = config
        self.normalization_rules = config.category_config['normalization']['title_patterns']
    
    def normalize_title(self, title: str) -> str:
        """
        商品タイトルを正規化
        
        Args:
            title: 元のタイトル
        
        Returns:
            正規化されたタイトル
        """
        normalized = title
        
        # 正規化ルールを適用
        for rule in self.normalization_rules:
            pattern = rule['pattern']
            replacement = rule['replacement']
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # 複数スペースを単一スペースに
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        logger.debug(f"Normalized title: {title} -> {normalized}")
        return normalized
    
    def normalize_records(self, records: List[MarketRecord]) -> List[MarketRecord]:
        """
        MarketRecord のリストを正規化
        
        Args:
            records: 正規化前の MarketRecord リスト
        
        Returns:
            正規化済みの MarketRecord リスト
        """
        normalized_records = []
        
        for record in records:
            record.normalized_title = self.normalize_title(record.original_title)
            normalized_records.append(record)
        
        logger.info(f"Normalized {len(normalized_records)} records")
        return normalized_records
    
    def extract_keywords(self, title: str) -> dict:
        """
        タイトルから重要な情報を抽出
        
        Args:
            title: 商品タイトル
        
        Returns:
            抽出された情報（例：シリーズ、レアリティなど）
        """
        # TODO: 実装
        # カテゴリごとの抽出ロジック
        return {}
