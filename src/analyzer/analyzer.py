"""
Analysis module for metric calculation and scoring.

This module provides the Analyzer class which calculates various metrics
from market records and determines candidate scores and decision statuses.

Classes:
    Analyzer: Performs analysis and scoring of market data.

Global Variables:
    logger: Logging object for this module.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics
from src.models.data_models import MarketRecord, ScoredCandidate, DecisionStatus, SourceSite
from src.config.config import config

logger = logging.getLogger(__name__)


class Analyzer:
    """
    Analyzes market records and calculates metrics for candidate scoring.
    
    This class provides methods to:
    - Calculate sold counts for specified date ranges
    - Compute price statistics (median, average, min, max)
    - Calculate Sell Through Rate (STR)
    - Estimate profit and profit rate
    - Generate composite candidate scores
    - Determine decision status
    
    Attributes:
        config (Config): Configuration object for pricing and scoring.
        scoring_config (Dict): Scoring configuration from config.
    
    Example:
        >>> analyzer = Analyzer()
        >>> sold_counts = analyzer.calculate_sold_counts(records)
        >>> price_stats = analyzer.calculate_price_stats(records)
    """
    
    def __init__(self):
        """
        Initialize the Analyzer.
        
        Loads configuration objects needed for analysis.
        """
        self.config = config
        self.scoring_config = config.scoring_config
    
    def calculate_sold_counts(self, records: List[MarketRecord], days_list: List[int] = [30, 90]) -> Dict[int, int]:
        """
        Calculate the number of sold listings within specified date ranges.
        
        Args:
            records (List[MarketRecord]): List of market records to analyze.
            days_list (List[int]): List of day ranges to calculate (default: [30, 90]).
        
        Returns:
            Dict[int, int]: Dictionary mapping days to sold count.
                           Example: {30: 5, 90: 12}
        
        Algorithm:
            1. Get current datetime
            2. For each days value in days_list:
               - Calculate threshold date: now - timedelta(days)
               - Count records where sold_flag=True and sold_date >= threshold
            3. Return results as dictionary
        
        Example:
            >>> records = [...]  # List of MarketRecord
            >>> counts = analyzer.calculate_sold_counts(records, [30, 90])
            >>> print(counts[30])  # 5 items sold in last 30 days
            >>> print(counts[90])  # 12 items sold in last 90 days
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
        Calculate price statistics from records.
        
        Computes minimum, maximum, average, and median prices from a list of records.
        
        Args:
            records (List[MarketRecord]): List of market records with price data.
        
        Returns:
            Dict[str, float]: Dictionary with keys 'min', 'max', 'avg', 'median'.
                             Example: {min: 29.99, max: 59.99, avg: 45.2, median: 48.5}
        
        Notes:
            - Only records with total_price > 0 are included
            - If no valid records, returns all 0.0
            - Uses statistics.mean() and statistics.median()
        
        Example:
            >>> records = [...]  # List of MarketRecord
            >>> stats = analyzer.calculate_price_stats(records)
            >>> print(stats['median'])  # 48.5
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
        Calculate Sell Through Rate (STR).
        
        STR indicates how quickly items are being sold compared to active listings.
        Higher STR means stronger demand.
        
        Args:
            sold_count (int): Number of sold items (usually sold_30d or sold_90d).
            active_count (int): Current number of active listings.
        
        Returns:
            float: STR as percentage (0-100). Rounded to 2 decimal places.
        
        Formula:
            STR = (sold_count / (sold_count + active_count)) * 100
        
        Edge Cases:
            - If (sold_count + active_count) == 0, returns 0.0
        
        Example:
            >>> analyzer.calculate_str(5, 3)
            62.5
            >>> analyzer.calculate_str(0, 10)
            0.0
        """
        if sold_count + active_count == 0:
            return 0.0
        
        str_value = (sold_count / (sold_count + active_count)) * 100
        return round(str_value, 2)
    
    def calculate_estimated_profit(self, ebay_price_usd: float, domestic_cost_jpy: float, 
                                   exchange_rate: float = 150.0) -> Dict[str, float]:
        """
        Calculate estimated profit and profit rate.
        
        Estimates profit by converting eBay USD price to JPY, subtracting fees and costs.
        
        Args:
            ebay_price_usd (float): Sale price on eBay in USD.
            domestic_cost_jpy (float): Cost to acquire item domestically in JPY.
            exchange_rate (float): USD to JPY conversion rate (default: 150.0).
        
        Returns:
            Dict[str, float]: Dictionary with keys:
                            - 'profit_jpy': Estimated profit in JPY (rounded to nearest integer)
                            - 'profit_rate': Profit rate as percentage (2 decimal places)
        
        Calculation Steps:
            1. Convert eBay price to JPY: ebay_price_jpy = ebay_price_usd * exchange_rate
            2. Calculate eBay fees: ebay_fee = ebay_price_jpy * config.ebay_fee_rate
            3. Convert shipping estimate to JPY: shipping_jpy = config.shipping_cost_estimate_usd * exchange_rate
            4. Calculate profit: estimated_profit_jpy = ebay_price_jpy - ebay_fee - shipping_jpy - domestic_cost_jpy
            5. Calculate rate: profit_rate = (estimated_profit_jpy / ebay_price_jpy) * 100
        
        Example:
            >>> profit = analyzer.calculate_estimated_profit(50.0, 3000.0)
            >>> print(profit['profit_jpy'])  # 2350
            >>> print(profit['profit_rate'])  # 31.33
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
        Calculate demand score (0-100).
        
        Evaluates the strength of demand based on sales history and sell-through rate.
        
        Args:
            sold_30d (int): Number of items sold in last 30 days.
            sold_90d (int): Number of items sold in last 90 days.
            str_value (float): Sell Through Rate percentage.
        
        Returns:
            float: Demand score (0-100).
        
        Scoring Logic:
        1. Base score from sold_30d:
           - 0-1: 0 points
           - 2-3: 20 points
           - 4-5: 40 points
           - 6-7: 60 points
           - 8+: 100 points
        
        2. STR bonus:
           - < 20%: 0 bonus
           - 20-40%: +10 points
           - 40-60%: +20 points
           - > 60%: +30 points
        
        3. Consistency bonus (90-day check):
           - If sold_90d > sold_30d * 2.5: +10 points
           - (indicates sustained strong demand)
        
        4. Final: min(100, base + str_bonus + consistency_bonus)
        
        Example:
            >>> score = analyzer.calculate_demand_score(5, 15, 45.0)
            >>> print(score)  # ~70 (40 base + 20 STR + 10 consistency)
        """
        # Base score from sold_30d
        if sold_30d >= 8:
            base_score = 100.0
        elif sold_30d >= 6:
            base_score = 60.0
        elif sold_30d >= 4:
            base_score = 40.0
        elif sold_30d >= 2:
            base_score = 20.0
        else:
            base_score = 0.0
        
        # STR bonus
        if str_value > 60:
            str_bonus = 30.0
        elif str_value > 40:
            str_bonus = 20.0
        elif str_value > 20:
            str_bonus = 10.0
        else:
            str_bonus = 0.0
        
        # Consistency bonus: check if 90-day sales are sustained
        consistency_bonus = 0.0
        if sold_30d > 0 and sold_90d > sold_30d * 2.5:
            consistency_bonus = 10.0
        
        # Cap at 100
        demand_score = min(100.0, base_score + str_bonus + consistency_bonus)
        return round(demand_score, 2)
    
    def calculate_profit_score(self, profit_rate: float, profit_jpy: float) -> float:
        """
        Calculate profit score (0-100).
        
        Evaluates profitability based on profit rate and absolute profit amount.
        
        Args:
            profit_rate (float): Profit rate as percentage (e.g., 22.5).
            profit_jpy (float): Absolute profit amount in JPY.
        
        Returns:
            float: Profit score (0-100).
        
        Scoring Logic:
        1. Base score from profit_rate:
           - < 5%: 0 points
           - 5-10%: 30 points
           - 10-15%: 50 points
           - 15-20%: 70 points
           - 20%+: 100 points
        
        2. Amount bonus:
           - < 500 JPY: 0 bonus
           - 500-1000 JPY: +10 points
           - 1000-2000 JPY: +20 points
           - 2000+ JPY: +30 points
        
        3. Final: min(100, base + amount_bonus)
        
        Example:
            >>> score = analyzer.calculate_profit_score(18.0, 1500.0)
            >>> print(score)  # ~90 (70 base + 20 amount bonus)
        """
        # Base score from profit_rate
        if profit_rate >= 20:
            rate_score = 100.0
        elif profit_rate >= 15:
            rate_score = 70.0
        elif profit_rate >= 10:
            rate_score = 50.0
        elif profit_rate >= 5:
            rate_score = 30.0
        else:
            rate_score = 0.0
        
        # Amount bonus
        if profit_jpy >= 2000:
            amount_bonus = 30.0
        elif profit_jpy >= 1000:
            amount_bonus = 20.0
        elif profit_jpy >= 500:
            amount_bonus = 10.0
        else:
            amount_bonus = 0.0
        
        # Cap at 100
        profit_score = min(100.0, rate_score + amount_bonus)
        return round(profit_score, 2)
    
    def calculate_supply_score(self, active_count: int) -> float:
        """
        Calculate supply/competition score (0-100).
        
        Evaluates competitiveness based on number of active listings.
        Fewer active listings = less competition = higher score.
        
        Args:
            active_count (int): Number of currently active listings.
        
        Returns:
            float: Supply score (0-100).
        
        Scoring Logic:
        Active count tiers:
        - > 50: 0 points (highly competitive)
        - 30-50: 20 points
        - 15-30: 40 points
        - 5-15: 60 points
        - < 5: 100 points (low competition)
        
        Example:
            >>> score = analyzer.calculate_supply_score(8)
            >>> print(score)  # 60 (5-15 range)
        """
        if active_count < 5:
            supply_score = 100.0
        elif active_count < 15:
            supply_score = 60.0
        elif active_count < 30:
            supply_score = 40.0
        elif active_count < 50:
            supply_score = 20.0
        else:
            supply_score = 0.0
        
        return supply_score
    
    def calculate_candidate_score(self, demand_score: float, profit_score: float, supply_score: float) -> float:
        """
        Calculate composite candidate score (0-100).
        
        Combines demand, profit, and supply scores using configured weights.
        
        Args:
            demand_score (float): Demand score (0-100).
            profit_score (float): Profit score (0-100).
            supply_score (float): Supply score (0-100).
        
        Returns:
            float: Composite candidate score (0-100), rounded to 2 decimal places.
        
        Formula:
            candidate_score = (demand_weight * demand_score) +
                            (profit_weight * profit_score) +
                            (supply_weight * supply_score)
            
            Default weights from config.scoring_config:
            - demand_weight: 0.4
            - profit_weight: 0.4
            - supply_weight: 0.2
        
        Example:
            >>> score = analyzer.calculate_candidate_score(85.0, 75.0, 80.0)
            >>> print(score)  # 80.0
        """
        weights = self.scoring_config.get('weights', {
            'demand': 0.4,
            'profit': 0.4,
            'supply': 0.2
        })
        
        total_score = (weights['demand'] * demand_score + 
                      weights['profit'] * profit_score + 
                      weights['supply'] * supply_score)
        
        return round(total_score, 2)
    
    def determine_decision_status(self, score: float) -> DecisionStatus:
        """
        Determine decision status based on candidate score.
        
        Maps composite score to one of three decision categories.
        
        Args:
            score (float): Composite candidate score (0-100).
        
        Returns:
            DecisionStatus: One of LIST_CANDIDATE, HOLD, or SKIP.
        
        Decision Logic:
            - score >= list_candidate_threshold (default 80) → LIST_CANDIDATE
            - hold_threshold <= score < list_candidate_threshold (default 60-79) → HOLD
            - score < hold_threshold (default < 60) → SKIP
        
        Thresholds come from config.scoring_config['thresholds'].
        
        Example:
            >>> analyzer.determine_decision_status(85.0)
            <DecisionStatus.LIST_CANDIDATE: 'list_candidate'>
            >>> analyzer.determine_decision_status(70.0)
            <DecisionStatus.HOLD: 'hold'>
            >>> analyzer.determine_decision_status(45.0)
            <DecisionStatus.SKIP: 'skip'>
        """
        thresholds = self.scoring_config.get('thresholds', {
            'list_candidate': 80.0,
            'hold': 60.0,
            'skip': 0.0
        })
        
        if score >= thresholds['list_candidate']:
            return DecisionStatus.LIST_CANDIDATE
        elif score >= thresholds['hold']:
            return DecisionStatus.HOLD
        else:
            return DecisionStatus.SKIP
