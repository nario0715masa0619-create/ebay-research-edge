"""
Tests for scoring logic implementation.

This module tests the Analyzer's scoring functions to ensure they produce
correct scores according to the defined tiers and bonuses.
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.analyzer import Analyzer
from src.models.data_models import DecisionStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_demand_score():
    """
    Test demand_score calculation with various inputs.
    """
    analyzer = Analyzer()
    
    test_cases = [
        # (sold_30d, sold_90d, str_value, expected_min, expected_max)
        (0, 0, 0.0, 0.0, 0.0),           # No sales
        (1, 3, 10.0, 10.0, 10.0),        # Very low sales, no bonuses
        (2, 6, 25.0, 40.0, 40.0),        # Low sales + STR bonus + consistency bonus
        (5, 15, 50.0, 70.0, 70.0),       # Good sales + STR bonus + consistency bonus
        (8, 25, 70.0, 100.0, 100.0),     # Strong sales + high STR (capped)
    ]
    
    for sold_30d, sold_90d, str_val, expected_min, expected_max in test_cases:
        score = analyzer.calculate_demand_score(sold_30d, sold_90d, str_val)
        assert expected_min <= score <= expected_max, \
            f"Demand score {score} not in range [{expected_min}, {expected_max}] for inputs ({sold_30d}, {sold_90d}, {str_val})"
        logger.info(f"✓ demand_score({sold_30d}, {sold_90d}, {str_val}) = {score}")
    
    logger.info("✓ test_demand_score passed\n")


def test_profit_score():
    """
    Test profit_score calculation with various inputs.
    """
    analyzer = Analyzer()
    
    test_cases = [
        # (profit_rate, profit_jpy, expected_min, expected_max)
        (0.0, 0.0, 0.0, 0.0),           # No profit
        (3.0, 200.0, 0.0, 5.0),         # Low rate, low amount
        (8.0, 800.0, 40.0, 45.0),       # Medium rate (5-10) + amount bonus (10)
        (18.0, 1500.0, 90.0, 95.0),     # Good rate (15-20) + good amount bonus (20)
        (25.0, 2500.0, 100.0, 100.0),   # Excellent (capped)
    ]
    
    for profit_rate, profit_jpy, expected_min, expected_max in test_cases:
        score = analyzer.calculate_profit_score(profit_rate, profit_jpy)
        assert expected_min <= score <= expected_max, \
            f"Profit score {score} not in range [{expected_min}, {expected_max}] for inputs ({profit_rate}, {profit_jpy})"
        logger.info(f"✓ profit_score({profit_rate}, {profit_jpy}) = {score}")
    
    logger.info("✓ test_profit_score passed\n")


def test_supply_score():
    """
    Test supply_score calculation with various inputs.
    """
    analyzer = Analyzer()
    
    test_cases = [
        # (active_count, expected_score)
        (2, 100.0),    # Very low competition
        (10, 60.0),    # Low competition
        (20, 40.0),    # Medium competition
        (40, 20.0),    # High competition
        (100, 0.0),    # Very high competition
    ]
    
    for active_count, expected_score in test_cases:
        score = analyzer.calculate_supply_score(active_count)
        assert score == expected_score, \
            f"Supply score {score} != {expected_score} for active_count={active_count}"
        logger.info(f"✓ supply_score({active_count}) = {score}")
    
    logger.info("✓ test_supply_score passed\n")


def test_candidate_score():
    """
    Test candidate_score (composite) calculation.
    """
    analyzer = Analyzer()
    
    # Test case: 0.4 * 80 + 0.4 * 75 + 0.2 * 80 = 32 + 30 + 16 = 78
    demand = 80.0
    profit = 75.0
    supply = 80.0
    
    score = analyzer.calculate_candidate_score(demand, profit, supply)
    expected = 78.0
    
    assert score == expected, f"Candidate score {score} != {expected}"
    logger.info(f"✓ candidate_score({demand}, {profit}, {supply}) = {score}")
    
    logger.info("✓ test_candidate_score passed\n")


def test_decision_status():
    """
    Test decision_status determination.
    """
    analyzer = Analyzer()
    
    test_cases = [
        (85.0, DecisionStatus.LIST_CANDIDATE),
        (80.0, DecisionStatus.LIST_CANDIDATE),
        (79.9, DecisionStatus.HOLD),
        (70.0, DecisionStatus.HOLD),
        (60.0, DecisionStatus.HOLD),
        (59.9, DecisionStatus.SKIP),
        (30.0, DecisionStatus.SKIP),
    ]
    
    for score, expected_status in test_cases:
        status = analyzer.determine_decision_status(score)
        assert status == expected_status, \
            f"Status {status} != {expected_status} for score={score}"
        logger.info(f"✓ decision_status({score}) = {status.value}")
    
    logger.info("✓ test_decision_status passed\n")


def test_str_calculation():
    """
    Test STR (Sell Through Rate) calculation.
    """
    analyzer = Analyzer()
    
    test_cases = [
        # (sold, active, expected)
        (5, 3, 62.5),
        (0, 10, 0.0),
        (10, 10, 50.0),
        (0, 0, 0.0),
    ]
    
    for sold, active, expected in test_cases:
        str_val = analyzer.calculate_str(sold, active)
        assert str_val == expected, f"STR {str_val} != {expected}"
        logger.info(f"✓ calculate_str({sold}, {active}) = {str_val}")
    
    logger.info("✓ test_str_calculation passed\n")


def test_profit_calculation():
    """
    Test profit and profit_rate calculation.
    """
    analyzer = Analyzer()
    
    # Test with eBay price 50 USD, domestic cost 3000 JPY
    # 50 USD * 150 = 7500 JPY
    # Fee: 7500 * 0.129 = 967.5 JPY
    # Shipping: 15 USD * 150 = 2250 JPY
    # Profit: 7500 - 967.5 - 2250 - 3000 = 1282.5 JPY
    # Rate: 1282.5 / 7500 * 100 = 17.1%
    
    result = analyzer.calculate_estimated_profit(50.0, 3000.0)
    
    assert 'profit_jpy' in result
    assert 'profit_rate' in result
    assert result['profit_jpy'] == 1282.0, f"Profit {result['profit_jpy']} != 1282"
    assert 17.0 <= result['profit_rate'] <= 18.0, f"Rate {result['profit_rate']} not in range"
    
    logger.info(f"✓ calculate_profit(50.0 USD, 3000 JPY) = {result}")
    logger.info("✓ test_profit_calculation passed\n")


def run_all_tests():
    """
    Run all scoring logic tests.
    """
    logger.info("\n=== Running Scoring Logic Tests ===\n")
    
    try:
        test_demand_score()
        test_profit_score()
        test_supply_score()
        test_candidate_score()
        test_decision_status()
        test_str_calculation()
        test_profit_calculation()
        
        logger.info("=== All Scoring Tests Passed! ===\n")
        return True
    except AssertionError as e:
        logger.error(f"\n✗ Test Failed: {e}\n")
        return False
    except Exception as e:
        logger.error(f"\n✗ Unexpected Error: {e}\n", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
