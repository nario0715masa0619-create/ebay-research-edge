"""
Data models module for eBay-Research-Edge.

This module defines the core data structures (dataclasses and enums) used
throughout the application for representing items, market records, and scored candidates.

Classes:
    SourceSite (Enum): Enumeration of data sources (eBay, Mercari, Yahoo Auction).
    DecisionStatus (Enum): Enumeration of candidate decision statuses.
    Item (Dataclass): Product master information.
    MarketRecord (Dataclass): Individual market listing record.
    ScoredCandidate (Dataclass): Aggregated results and decision status for a product.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class SourceSite(str, Enum):
    """
    Enumeration of data sources.
    
    Values:
        EBAY: eBay marketplace
        MERCARI: Mercari marketplace
        YAHOO_AUCTION: Yahoo Auction Japan
    
    Usage:
        >>> record.source_site == SourceSite.EBAY
        >>> record.source_site.value  # 'ebay'
    """
    EBAY = "ebay"
    MERCARI = "mercari"
    YAHOO_AUCTION = "yahoo_auction"


class DecisionStatus(str, Enum):
    """
    Enumeration of candidate decision statuses.
    
    Values:
        LIST_CANDIDATE: Recommended for listing (score >= 80)
        HOLD: Keep for future consideration (60 <= score < 80)
        SKIP: Not recommended (score < 60)
    
    Usage:
        >>> if candidate.decision_status == DecisionStatus.LIST_CANDIDATE:
        ...     print("Ready to list")
    """
    LIST_CANDIDATE = "list_candidate"
    HOLD = "hold"
    SKIP = "skip"


@dataclass
class Item:
    """
    Product master record.
    
    Represents a unique product across all sources. Used as a reference
    for multiple MarketRecords from different sources/dates.
    
    Attributes:
        item_id (str): Unique identifier for the product.
                      Generated during normalization process.
        normalized_name (str): Standardized product name after normalization.
        franchise (Optional[str]): Franchise/series name (e.g., 'Pokemon').
        character (Optional[str]): Character name if applicable.
        category (str): Category name (default: 'pokemon_card').
        subcategory (Optional[str]): Sub-category classification.
        created_at (datetime): Record creation timestamp.
        updated_at (datetime): Record last update timestamp.
    
    Example:
        >>> item = Item(
        ...     item_id="pkmn_001",
        ...     normalized_name="Pokemon Card Charizard EX Holo",
        ...     franchise="Pokemon",
        ...     character="Charizard",
        ...     category="pokemon_card"
        ... )
    """
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
    """
    Individual market listing record.
    
    Represents a single listing/sale from a specific source (eBay, Mercari, etc).
    Contains raw and normalized information about the listing.
    
    Attributes:
        record_id (str): Unique identifier for this record.
        item_id (str): Foreign key to Item. Links to product master.
        source_site (SourceSite): Source of this record (ebay/mercari/yahoo_auction).
        search_keyword (str): Keyword used when searching/scraping this record.
        original_title (str): Title as retrieved from the source (unmodified).
        normalized_title (str): Title after normalization processing.
        price (float): Item price in source currency.
        shipping (float): Shipping cost in source currency.
        currency (str): Currency code (USD/JPY).
        total_price (float): price + shipping (calculated field).
        sold_flag (bool): Whether the item has been sold/is completed.
        active_flag (bool): Whether the item is currently listed/active.
        sold_date (Optional[datetime]): Date when item was sold (if sold_flag=True).
        listing_url (Optional[str]): URL to the listing on source site.
        fetched_at (datetime): Timestamp when this record was retrieved.
    
    Example:
        >>> record = MarketRecord(
        ...     record_id="ebay_123456",
        ...     item_id="pkmn_001",
        ...     source_site=SourceSite.EBAY,
        ...     search_keyword="pokemon card charizard",
        ...     original_title="Pokemon Card - Charizard EX Holo [Japanese]",
        ...     normalized_title="Pokemon Card Charizard EX Holo",
        ...     price=49.99,
        ...     shipping=5.00,
        ...     currency="USD",
        ...     total_price=54.99,
        ...     sold_flag=True,
        ...     active_flag=False,
        ...     sold_date=datetime(2024, 4, 20)
        ... )
    """
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
    """
    Aggregated results and decision status for a product.
    
    This record represents the final analysis result for a single item,
    containing all calculated metrics and the final decision status.
    
    Attributes:
        candidate_id (str): Unique identifier for this candidate record.
        item_id (str): Foreign key to Item.
        sold_30d (int): Number of sold listings in the last 30 days.
        sold_90d (int): Number of sold listings in the last 90 days.
        active_count (int): Current number of active listings.
        median_price_usd (float): Median price from eBay sales (USD).
        avg_price_usd (float): Average price from eBay sales (USD).
        min_price_usd (float): Minimum price from eBay sales (USD).
        max_price_usd (float): Maximum price from eBay sales (USD).
        domestic_min_price_jpy (float): Lowest domestic price (JPY).
        domestic_median_price_jpy (float): Median domestic price (JPY).
        estimated_profit_jpy (float): Estimated profit amount (JPY).
                                     Calculation: ebay_price - fees - shipping - domestic_cost
        estimated_profit_rate (float): Estimated profit rate (%).
                                      Calculation: (profit / ebay_price) * 100
        str (float): Sell Through Rate (%).
                    Formula: (sold / (sold + active)) * 100
        candidate_score (float): Overall composite score (0-100).
                               Formula: 0.4*demand + 0.4*profit + 0.2*supply
        decision_status (DecisionStatus): Final decision (list_candidate/hold/skip).
                                         Based on candidate_score thresholds.
        calculated_at (datetime): Timestamp when metrics were calculated.
    
    Example:
        >>> candidate = ScoredCandidate(
        ...     candidate_id="cand_001",
        ...     item_id="pkmn_001",
        ...     sold_30d=5,
        ...     sold_90d=12,
        ...     active_count=3,
        ...     median_price_usd=48.50,
        ...     avg_price_usd=47.20,
        ...     min_price_usd=39.99,
        ...     max_price_usd=59.99,
        ...     domestic_min_price_jpy=1800,
        ...     domestic_median_price_jpy=2200,
        ...     estimated_profit_jpy=2500,
        ...     estimated_profit_rate=22.5,
        ...     str=62.5,
        ...     candidate_score=81.2,
        ...     decision_status=DecisionStatus.LIST_CANDIDATE
        ... )
    """
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
    str: float
    candidate_score: float
    decision_status: DecisionStatus
    calculated_at: datetime = field(default_factory=datetime.now)
