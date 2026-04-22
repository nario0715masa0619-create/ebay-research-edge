import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics
from src.models.data_models import MarketRecord, ScoredCandidate, DecisionStatus, SourceSite
from src.config.config import config

logger = logging.getLogger(__name__)


class Analyzer:
    """データを分析し、指標を計算するクラス"""
    
    def __init__(self):
        self.config = config
        self.scoring_config = config.scoring_config
    
    def calculate_sold_counts(self, records: List[MarketRecord], days_list: List[int] = [30, 90]) -> Dict[int, int]:
        """
        指定された日数内の Sold 件数を計算
        
        Args:
            records: MarketRecord のリスト
            days_list: 計算対象の日数リスト（例: [30, 90]）
        
        Returns:
            {日数: Sold件数} の辞書
        """
        result = {}
        now = datetime.now()
        
        for days in days_list:
            threshold = now - timedelta(days=days)
            sold_count = sum(1 for r in records 
                           if r.sold_flag and r.sold_date and r.sold_date >= threshold)
            result[days] = sold_count
            logger.debug(f"Sold count for {days}d: {sold_count}")
        
        return result
    
    def calculate_price_stats(self, records: List[MarketRecord]) -> Dict[str, float]:
        """
        価格の統計値を計算（中央値、平均値、最小値、最大値）
        
        Args:
            records: MarketRecord のリスト
        
        Returns:
            統計値の辞書
        """
        prices = [r.total_price for r in records if r.total_price > 0]
        
        if not prices:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "median": 0.0
            }
        
        return {
            "min": min(prices),
            "max": max(prices),
            "avg": statistics.mean(prices),
            "median": statistics.median(prices)
        }
    
    def calculate_str(self, sold_count: int, active_count: int) -> float:
        """
        Sell Through Rate を計算
        STR = sold / (sold + active) * 100
        
        Args:
            sold_count: Sold 件数
            active_count: 現在の出品数
        
        Returns:
            STR (%)
        """
        if sold_count + active_count == 0:
            return 0.0
        
        str_value = (sold_count / (sold_count + active_count)) * 100
        return round(str_value, 2)
    
    def calculate_estimated_profit(self, ebay_price_usd: float, domestic_cost_jpy: float, 
                                   exchange_rate: float = 150.0) -> Dict[str, float]:
        """
        概算利益を計算
        
        Args:
            ebay_price_usd: eBay売却価格（ドル）
            domestic_cost_jpy: 国内仕入れ価格（円）
            exchange_rate: 為替レート（円/ドル）
        
        Returns:
            {profit_jpy, profit_rate} の辞書
        """
        ebay_price_jpy = ebay_price_usd * exchange_rate
        ebay_fee = ebay_price_jpy * self.config.ebay_fee_rate
        shipping_cost_jpy = self.config.shipping_cost_estimate_usd * exchange_rate
        
        estimated_profit_jpy = ebay_price_jpy - ebay_fee - shipping_cost_jpy - domestic_cost_jpy
        
        if ebay_price_jpy == 0:
            profit_rate = 0.0
        else:
            profit_rate = (estimated_profit_jpy / ebay_price_jpy) * 100
        
        return {
            "profit_jpy": round(estimated_profit_jpy, 0),
            "profit_rate": round(profit_rate, 2)
        }
    
    def calculate_demand_score(self, sold_30d: int, sold_90d: int, str_value: float) -> float:
        """
        需要スコアを計算
        
        Args:
            sold_30d: 30日 Sold 件数
            sold_90d: 90日 Sold 件数
            str_value: Sell Through Rate
        
        Returns:
            需要スコア（0-100）
        """
        # TODO: 実装
        # 30日 Sold 件数、90日 Sold 件数、STR を組み合わせて加点
        score = 0.0
        return score
    
    def calculate_profit_score(self, profit_rate: float, profit_jpy: float) -> float:
        """
        利益スコアを計算
        
        Args:
            profit_rate: 粗利率（%）
            profit_jpy: 概算利益（円）
        
        Returns:
            利益スコア（0-100）
        """
        # TODO: 実装
        # 粗利率と利益額を組み合わせて加点
        score = 0.0
        return score
    
    def calculate_supply_score(self, active_count: int) -> float:
        """
        供給スコアを計算（active_count が少ないほど加点）
        
        Args:
            active_count: 現在の出品数
        
        Returns:
            供給スコア（0-100）
        """
        # TODO: 実装
        # active_count が少ないほど加点
        score = 0.0
        return score
    
    def calculate_candidate_score(self, demand_score: float, profit_score: float, supply_score: float) -> float:
        """
        総合スコアを計算
        candidate_score = 0.4 * demand_score + 0.4 * profit_score + 0.2 * supply_score
        
        Args:
            demand_score: 需要スコア
            profit_score: 利益スコア
            supply_score: 供給スコア
        
        Returns:
            総合スコア（0-100）
        """
        weights = self.scoring_config['weights']
        total_score = (weights['demand'] * demand_score + 
                      weights['profit'] * profit_score + 
                      weights['supply'] * supply_score)
        
        return round(total_score, 2)
    
    def determine_decision_status(self, score: float) -> DecisionStatus:
        """
        総合スコアから判定ステータスを決定
        
        Args:
            score: 総合スコア
        
        Returns:
            DecisionStatus
        """
        thresholds = self.scoring_config['thresholds']
        
        if score >= thresholds['list_candidate']:
            return DecisionStatus.LIST_CANDIDATE
        elif score >= thresholds['hold']:
            return DecisionStatus.HOLD
        else:
            return DecisionStatus.SKIP
