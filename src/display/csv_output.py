"""
CSV output module for data export.

This module provides the CSVOutput class for exporting analysis results
and raw data to CSV files.

Classes:
    CSVOutput: Exports ScoredCandidate and raw data to CSV format.

Global Variables:
    logger: Logging object for this module.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from src.models.data_models import ScoredCandidate
from src.config.config import config

logger = logging.getLogger(__name__)


class CSVOutput:
    """
    Exports analysis results and raw data to CSV files.
    
    This class provides methods to export:
    - Scored candidates (final analysis results)
    - Raw market data (for audit and further analysis)
    
    Files are saved to the processed data directory with timestamps.
    
    Attributes:
        config (Config): Configuration object.
        output_dir (Path): Target directory for CSV exports (data/processed/).
    
    Example:
        >>> csv_output = CSVOutput()
        >>> path = csv_output.export_candidates(candidates)
        >>> print(f"Exported to: {path}")
    """
    
    def __init__(self):
        """
        Initialize the CSV output handler.
        
        Sets up output directory (data/processed/) and creates it if needed.
        """
        self.config = config
        self.output_dir = config.processed_data_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_candidates(self, candidates: List[ScoredCandidate], filename: str = None) -> Path:
        """
        Export scored candidates to CSV file.
        
        Writes ScoredCandidate objects to a CSV file with columns for all metrics
        and decision status. File is created in data/processed/ directory.
        
        Args:
            candidates (List[ScoredCandidate]): List of scored candidates to export.
            filename (str, optional): Custom filename. If None, auto-generates
                                     filename with format:
                                     candidates_{category}_{timestamp}.csv
                                     Example: candidates_pokemon_card_20240422_153000.csv
        
        Returns:
            Path: Full path to the created CSV file.
        
        CSV Columns (in order):
            candidate_id, item_id, sold_30d, sold_90d, active_count,
            median_price_usd, avg_price_usd, min_price_usd, max_price_usd,
            domestic_min_price_jpy, domestic_median_price_jpy,
            estimated_profit_jpy, estimated_profit_rate, str, candidate_score,
            decision_status, calculated_at
        
        Algorithm:
            1. If filename is None:
               - Generate timestamp (YYYYMMDD_HHMMSS)
               - Create filename: candidates_{active_category}_{timestamp}.csv
            2. Construct output path in output_dir
            3. Open CSV file for writing (UTF-8 encoding)
            4. Write header row with fieldnames
            5. For each candidate:
               - Convert DecisionStatus enum to string (.value)
               - Convert datetime to ISO format string
               - Write row to CSV
            6. Close file and log success
            7. Return output path
        
        Raises:
            IOError: If file cannot be created or written.
            csv.Error: If CSV writing fails.
        
        Example:
            >>> csv_output = CSVOutput()
            >>> candidates = [...]  # List of ScoredCandidate
            >>> output_path = csv_output.export_candidates(candidates)
            >>> print(f"Exported {len(candidates)} candidates to {output_path}")
            Exported 42 candidates to data/processed/candidates_pokemon_card_20240422_153000.csv
        
        Notes:
            - Files are always UTF-8 encoded for international character support
            - Timestamps in auto-generated names use local time (not UTC)
            - existing files with same name are overwritten
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"candidates_{self.config.active_category}_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # Define CSV columns
        fieldnames = [
            'candidate_id',
            'item_id',
            'sold_30d',
            'sold_90d',
            'active_count',
            'median_price_usd',
            'avg_price_usd',
            'min_price_usd',
            'max_price_usd',
            'domestic_min_price_jpy',
            'domestic_median_price_jpy',
            'estimated_profit_jpy',
            'estimated_profit_rate',
            'str',
            'candidate_score',
            'decision_status',
            'calculated_at'
        ]
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for candidate in candidates:
                    writer.writerow({
                        'candidate_id': candidate.candidate_id,
                        'item_id': candidate.item_id,
                        'sold_30d': candidate.sold_30d,
                        'sold_90d': candidate.sold_90d,
                        'active_count': candidate.active_count,
                        'median_price_usd': candidate.median_price_usd,
                        'avg_price_usd': candidate.avg_price_usd,
                        'min_price_usd': candidate.min_price_usd,
                        'max_price_usd': candidate.max_price_usd,
                        'domestic_min_price_jpy': candidate.domestic_min_price_jpy,
                        'domestic_median_price_jpy': candidate.domestic_median_price_jpy,
                        'estimated_profit_jpy': candidate.estimated_profit_jpy,
                        'estimated_profit_rate': candidate.estimated_profit_rate,
                        'str': candidate.str,
                        'candidate_score': candidate.candidate_score,
                        'decision_status': candidate.decision_status.value,
                        'calculated_at': candidate.calculated_at.isoformat()
                    })
            
            logger.info(f"Exported {len(candidates)} candidates to {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            raise
    
    def export_raw_data(self, data: List[Dict], filename: str) -> Path:
        """
        Export raw market data to CSV file.
        
        Writes raw dictionary data (from fetch operations) to CSV format.
        Useful for auditing, debugging, and further manual analysis.
        
        Args:
            data (List[Dict]): List of dictionaries containing raw data.
                              All dicts should have the same keys.
            filename (str): Output filename (required, no auto-generation).
        
        Returns:
            Path: Full path to the created CSV file.
        
        Algorithm:
            1. Check if data list is empty:
               - If empty, log warning and return path (no file created)
            2. Extract fieldnames from data[0].keys()
            3. Construct output path in output_dir
            4. Open CSV file for writing (UTF-8 encoding)
            5. Write header row with fieldnames
            6. Write all data rows
            7. Close file and log success
            8. Return output path
        
        Raises:
            IOError: If file cannot be created or written.
            csv.Error: If CSV writing fails.
            IndexError: If data list is empty (caught and logged).
        
        Example:
            >>> csv_output = CSVOutput()
            >>> raw_listings = [
            ...     {
            ...         'itemId': '123456',
            ...         'title': 'Pokemon Card',
            ...         'price': 49.99,
            ...         'fetchedAt': '2024-04-22T10:30:00'
            ...     },
            ...     ...
            ... ]
            >>> path = csv_output.export_raw_data(raw_listings, "ebay_raw_pokemon.csv")
            >>> print(f"Exported to: {path}")
            Exported to: data/processed/ebay_raw_pokemon.csv
        
        Notes:
            - Fieldnames are determined from the first row's keys
            - All rows must have consistent keys
            - Files are UTF-8 encoded
            - Existing files with same name are overwritten
        """
        output_path = self.output_dir / filename
        
        if not data:
            logger.warning("No data to export")
            return output_path
        
        try:
            fieldnames = list(data[0].keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Exported {len(data)} records to {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error exporting raw data: {e}")
            raise
