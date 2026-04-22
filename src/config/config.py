"""
Configuration management module for eBay-Research-Edge.

This module provides centralized configuration management with support for
dynamic category switching through YAML configuration files.

Global Variables:
    config (Config): Singleton configuration object accessible throughout the project.
                     Usage: from src.config.config import config

Example:
    >>> from src.config.config import config
    >>> print(config.category_name_ja)  # 'Pokemon Card'
    >>> print(config.ebay_keywords)  # ['pokemon card', 'pokemon tcg', ...]
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    """
    Centralized configuration manager for the eBay-Research-Edge project.
    
    This class loads category-specific settings from YAML files and provides
    properties to access configuration values throughout the application.
    
    Attributes:
        project_root (Path): Root directory of the project.
        active_category (str): Currently active category name (from ACTIVE_CATEGORY env var).
        category_config (Dict[str, Any]): Loaded category configuration from YAML.
    
    Example:
        >>> config = Config()
        >>> config.ebay_fee_rate  # 0.129
        >>> config.shipping_cost_estimate_usd  # 15.0
    """
    
    def __init__(self):
        """
        Initialize the Config object.
        
        Loads the active category from the ACTIVE_CATEGORY environment variable
        (defaults to 'pokemon_card' if not set), then loads the corresponding
        category configuration YAML file.
        
        Raises:
            FileNotFoundError: If the category configuration YAML file does not exist.
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.active_category = os.getenv("ACTIVE_CATEGORY", "pokemon_card")
        self.category_config = self._load_category_config()
    
    def _load_category_config(self) -> Dict[str, Any]:
        """
        Load the category configuration from a YAML file.
        
        The YAML file path is constructed as:
        data/categories/{active_category}.yaml
        
        Returns:
            Dict[str, Any]: Parsed YAML configuration dictionary.
                           Structure includes: category, ebay, mercari, normalization, 
                           pricing, scoring keys.
        
        Raises:
            FileNotFoundError: If data/categories/{active_category}.yaml does not exist.
            yaml.YAMLError: If YAML parsing fails.
        
        Example:
            >>> config._load_category_config()
            {
                'category': {'name': 'Pokemon Card', 'name_ja': 'Pokemon Card', ...},
                'ebay': {'keywords': [...], 'exclude_keywords': [...]},
                ...
            }
        """
        categories_dir = self.project_root / "data" / "categories"
        config_file = categories_dir / f"{self.active_category}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Category config not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @property
    def category_name(self) -> str:
        """
        Get the category name in English.
        
        Returns:
            str: Category name (e.g., 'Pokemon Card').
        """
        return self.category_config['category']['name']
    
    @property
    def category_name_ja(self) -> str:
        """
        Get the category name in Japanese.
        
        Returns:
            str: Japanese category name (e.g., 'Pokemon Card').
        """
        return self.category_config['category']['name_ja']
    
    @property
    def ebay_keywords(self) -> list:
        """
        Get eBay search keywords for the current category.
        
        Returns:
            List[str]: Keywords to include in eBay searches.
                      Example: ['pokemon card', 'pokemon tcg', 'pokémon card']
        """
        return self.category_config['ebay']['keywords']
    
    @property
    def ebay_exclude_keywords(self) -> list:
        """
        Get keywords to exclude from eBay searches.
        
        Returns:
            List[str]: Keywords that should exclude results.
                      Example: ['storage box', 'binder', 'sleeve', 'proxy']
        """
        return self.category_config['ebay']['exclude_keywords']
    
    @property
    def mercari_keywords(self) -> list:
        """
        Get Mercari search keywords for the current category.
        
        Returns:
            List[str]: Keywords to include in Mercari searches.
                      Example: ['pokemon card', 'poke card']
        """
        return self.category_config['mercari']['keywords']
    
    @property
    def ebay_fee_rate(self) -> float:
        """
        Get the eBay seller fee rate.
        
        Returns:
            float: Fee rate as decimal (e.g., 0.129 for 12.9%).
                  Used in profit calculation: cost -= (price * fee_rate)
        """
        return self.category_config['pricing']['ebay_fee_rate']
    
    @property
    def shipping_cost_estimate_usd(self) -> float:
        """
        Get the estimated domestic-to-eBay shipping cost in USD.
        
        Returns:
            float: Estimated shipping cost in USD.
                  Used in profit calculation: cost -= shipping_cost_estimate_usd
        """
        return self.category_config['pricing']['shipping_cost_estimate_usd']
    
    @property
    def mercari_fee_rate(self) -> float:
        """
        Get the Mercari seller fee rate.
        
        Returns:
            float: Fee rate as decimal (e.g., 0.10 for 10%).
                  Used when calculating domestic acquisition cost.
        """
        return self.category_config['pricing']['mercari_fee_rate']
    
    @property
    def scoring_config(self) -> Dict[str, Any]:
        """
        Get the scoring configuration.
        
        Returns:
            Dict[str, Any]: Scoring configuration including weights and thresholds.
                           Keys: 'demand_weight', 'profit_weight', 'supply_weight',
                           'thresholds' (list_candidate, hold, skip)
        """
        return self.category_config['scoring']
    
    @property
    def data_dir(self) -> Path:
        """Get the main data directory path (data/)."""
        return self.project_root / "data"
    
    @property
    def raw_data_dir(self) -> Path:
        """Get the raw data directory path (data/raw/)."""
        return self.project_root / "data" / "raw"
    
    @property
    def processed_data_dir(self) -> Path:
        """Get the processed data directory path (data/processed/)."""
        return self.project_root / "data" / "processed"


# Global singleton configuration instance
# Access throughout the project with: from src.config.config import config
config = Config()
