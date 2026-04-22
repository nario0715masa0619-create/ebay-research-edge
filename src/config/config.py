import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """プロジェクト全体の設定を管理するクラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.active_category = os.getenv("ACTIVE_CATEGORY", "pokemon_card")
        self.category_config = self._load_category_config()
    
    def _load_category_config(self) -> Dict[str, Any]:
        """カテゴリ設定YAMLを読み込む"""
        categories_dir = self.project_root / "data" / "categories"
        config_file = categories_dir / f"{self.active_category}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Category config not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @property
    def category_name(self) -> str:
        """カテゴリ名を取得"""
        return self.category_config['category']['name']
    
    @property
    def category_name_ja(self) -> str:
        """カテゴリ日本語名を取得"""
        return self.category_config['category']['name_ja']
    
    @property
    def ebay_keywords(self) -> list:
        """eBay検索キーワードを取得"""
        return self.category_config['ebay']['keywords']
    
    @property
    def ebay_exclude_keywords(self) -> list:
        """eBay除外キーワードを取得"""
        return self.category_config['ebay']['exclude_keywords']
    
    @property
    def mercari_keywords(self) -> list:
        """メルカリ検索キーワードを取得"""
        return self.category_config['mercari']['keywords']
    
    @property
    def ebay_fee_rate(self) -> float:
        """eBay手数料率を取得"""
        return self.category_config['pricing']['ebay_fee_rate']
    
    @property
    def shipping_cost_estimate_usd(self) -> float:
        """推定送料（ドル）を取得"""
        return self.category_config['pricing']['shipping_cost_estimate_usd']
    
    @property
    def mercari_fee_rate(self) -> float:
        """メルカリ手数料率を取得"""
        return self.category_config['pricing']['mercari_fee_rate']
    
    @property
    def scoring_config(self) -> Dict[str, Any]:
        """スコアリング設定を取得"""
        return self.category_config['scoring']
    
    @property
    def data_dir(self) -> Path:
        """データディレクトリを取得"""
        return self.project_root / "data"
    
    @property
    def raw_data_dir(self) -> Path:
        """生データディレクトリを取得"""
        return self.project_root / "data" / "raw"
    
    @property
    def processed_data_dir(self) -> Path:
        """処理済みデータディレクトリを取得"""
        return self.project_root / "data" / "processed"


# グローバル設定インスタンス
config = Config()
