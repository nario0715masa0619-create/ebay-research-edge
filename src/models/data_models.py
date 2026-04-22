from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SourceSite(str, Enum):
    """データソースの種類"""
    EBAY = "ebay"
    MERCARI = "mercari"
    YAHOO_AUCTION = "yahoo_auction"


class DecisionStatus(str, Enum):
    """候補判定ステータス"""
    LIST_CANDIDATE = "list_candidate"
    HOLD = "hold"
    SKIP = "skip"


@dataclass
class Item:
    """商品マスタ"""
    item_id: str
    normalized_name: str
    franchise: Optional[str] = None
    character: Optional[str] = None
    category: str = "pokemon_card"
    subcategory: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MarketRecord:
    """国内外の取得レコード"""
    record_id: str
    item_id: str
    source_site: SourceSite
    search_keyword: str
    original_title: str
    normalized_title: str
    price: float
    shipping: float
    currency: str
    total_price: float
    sold_flag: bool
    active_flag: bool
    sold_date: Optional[datetime] = None
    listing_url: Optional[str] = None
    fetched_at: datetime = field(default_factory=datetime.now)


@dataclass
class ScoredCandidate:
    """集計結果と判定"""
    candidate_id: str
    item_id: str
    sold_30d: int
    sold_90d: int
    active_count: int
    median_price_usd: float
    avg_price_usd: float
    min_price_usd: float
    max_price_usd: float
    domestic_min_price_jpy: float
    domestic_median_price_jpy: float
    estimated_profit_jpy: float
    estimated_profit_rate: float
    str: float  # Sell Through Rate
    candidate_score: float
    decision_status: DecisionStatus
    calculated_at: datetime = field(default_factory=datetime.now)
