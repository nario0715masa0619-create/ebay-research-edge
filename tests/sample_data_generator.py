"""
Sample data generator for testing eBay-Research-Edge.

This module generates realistic sample data for eBay and Mercari listings
to test the entire pipeline without relying on actual API calls.

Classes:
    SampleDataGenerator: Generates sample MarketRecord and Item data.

Global Variables:
    logger: Logging object for this module.
"""

import logging
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any
from src.models.data_models import Item, MarketRecord, SourceSite, ScoredCandidate, DecisionStatus

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """
    Generates realistic sample data for testing and development.
    
    Creates sample MarketRecords simulating eBay and Mercari listings
    for Pokemon cards, with realistic price ranges and sold dates.
    
    Attributes:
        pokemon_card_names (List[str]): Sample Pokemon card product names.
        ebay_price_range (tuple): Min and max prices for eBay listings (USD).
        mercari_price_range (tuple): Min and max prices for Mercari listings (JPY).
    
    Example:
        >>> generator = SampleDataGenerator()
        >>> items = generator.generate_items(count=5)
        >>> records = generator.generate_ebay_records(items, count=20)
    """
    
    # Sample Pokemon card names for variety
    POKEMON_CARDS = [
        "Pokemon Card Charizard EX Holo",
        "Pokemon Card Blastoise VMAX Secret",
        "Pokemon Card Venusaur VSTar",
        "Pokemon Card Pikachu Promo",
        "Pokemon Card Dragonite EX",
        "Pokemon Card Alakazam GX",
        "Pokemon Card Mewtwo V",
        "Pokemon Card Rayquaza VMAX",
        "Pokemon Card Lugia EX",
        "Pokemon Card Ho-Oh GX",
    ]
    
    def __init__(self):
        """
        Initialize the SampleDataGenerator.
        """
        self.pokemon_card_names = self.POKEMON_CARDS
        self.ebay_price_range = (29.99, 99.99)
        self.mercari_price_range = (1500, 8000)
    
    def generate_items(self, count: int = 5) -> List[Item]:
        """
        Generate sample Item (product master) records.
        
        Args:
            count (int): Number of items to generate (default: 5).
        
        Returns:
            List[Item]: List of Item records with unique IDs and normalized names.
        
        Algorithm:
            1. For count iterations:
               - Select a Pokemon card name from POKEMON_CARDS
               - Generate unique item_id (pkmn_{uuid})
               - Extract franchise='Pokemon' and character name from title
               - Create Item instance
            2. Return item list
        
        Example:
            >>> generator = SampleDataGenerator()
            >>> items = generator.generate_items(5)
            >>> print(items[0].normalized_name)
            'Pokemon Card Charizard EX Holo'
        """
        items = []
        
        for i in range(count):
            card_name = self.pokemon_card_names[i % len(self.pokemon_card_names)]
            item_id = f"pkmn_{uuid.uuid4().hex[:8]}"
            
            # Simple character extraction from card name
            character = card_name.split()[2] if len(card_name.split()) > 2 else "Unknown"
            
            item = Item(
                item_id=item_id,
                normalized_name=card_name,
                franchise="Pokemon",
                character=character,
                category="pokemon_card",
                subcategory="Trading Card"
            )
            items.append(item)
        
        logger.info(f"Generated {count} sample items")
        return items
    
    def generate_ebay_records(self, items: List[Item], count: int = 20, 
                             days_back: int = 90) -> List[MarketRecord]:
        """
        Generate sample eBay MarketRecords (sold listings).
        
        Args:
            items (List[Item]): List of Item records to associate with.
            count (int): Total number of records to generate (default: 20).
            days_back (int): How many days in the past to generate sold_dates (default: 90).
        
        Returns:
            List[MarketRecord]: List of eBay MarketRecords.
        
        Algorithm:
            1. Calculate dates: from (today - days_back) to today
            2. For count iterations:
               - Select random item
               - Generate record_id (ebay_{uuid})
               - Create random sold_date within range
               - Generate price in ebay_price_range
               - Generate shipping cost (5-15 USD)
               - Create MarketRecord with:
                 * source_site=SourceSite.EBAY
                 * sold_flag=True
                 * active_flag=False
                 * currency='USD'
            3. Return record list
        
        Example:
            >>> items = generator.generate_items(3)
            >>> records = generator.generate_ebay_records(items, count=15)
            >>> print(records[0].source_site)
            <SourceSite.EBAY: 'ebay'>
        """
        records = []
        now = datetime.now()
        start_date = now - timedelta(days=days_back)
        
        for i in range(count):
            item = items[i % len(items)]
            record_id = f"ebay_{uuid.uuid4().hex[:8]}"
            
            # Random sold date within range
            days_offset = (now - start_date).days
            sold_date = start_date + timedelta(days=int((i / count) * days_offset))
            
            # Random price
            price = round(self.ebay_price_range[0] + 
                         (i % 10) * (self.ebay_price_range[1] - self.ebay_price_range[0]) / 10, 2)
            shipping = round(5.0 + (i % 5) * 2.0, 2)
            total_price = price + shipping
            
            record = MarketRecord(
                record_id=record_id,
                item_id=item.item_id,
                source_site=SourceSite.EBAY,
                search_keyword="pokemon card",
                original_title=f"{item.normalized_name} [eBay]",
                normalized_title=item.normalized_name,
                price=price,
                shipping=shipping,
                currency="USD",
                total_price=total_price,
                sold_flag=True,
                active_flag=False,
                sold_date=sold_date,
                listing_url=f"https://ebay.com/itm/{record_id}",
                fetched_at=now
            )
            records.append(record)
        
        logger.info(f"Generated {count} sample eBay records")
        return records
    
    def generate_mercari_records(self, items: List[Item], count: int = 15,
                                days_back: int = 90) -> List[MarketRecord]:
        """
        Generate sample Mercari MarketRecords (sold listings).
        
        Args:
            items (List[Item]): List of Item records to associate with.
            count (int): Total number of records to generate (default: 15).
            days_back (int): How many days in the past to generate sold_dates (default: 90).
        
        Returns:
            List[MarketRecord]: List of Mercari MarketRecords.
        
        Algorithm:
            Similar to generate_ebay_records but:
            - Price range in JPY (mercari_price_range)
            - Shipping is 0 (Mercari calculates separately)
            - source_site=SourceSite.MERCARI
            - currency='JPY'
        
        Example:
            >>> items = generator.generate_items(3)
            >>> records = generator.generate_mercari_records(items, count=12)
            >>> print(records[0].currency)
            'JPY'
        """
        records = []
        now = datetime.now()
        start_date = now - timedelta(days=days_back)
        
        for i in range(count):
            item = items[i % len(items)]
            record_id = f"mercari_{uuid.uuid4().hex[:8]}"
            
            # Random sold date
            days_offset = (now - start_date).days
            sold_date = start_date + timedelta(days=int((i / count) * days_offset))
            
            # Random price in JPY
            price = round(self.mercari_price_range[0] + 
                         (i % 8) * (self.mercari_price_range[1] - self.mercari_price_range[0]) / 8, 0)
            shipping = 0.0  # Mercari shipping handled separately
            total_price = price + shipping
            
            record = MarketRecord(
                record_id=record_id,
                item_id=item.item_id,
                source_site=SourceSite.MERCARI,
                search_keyword="pokemon card",
                original_title=f"{item.normalized_name} [Mercari]",
                normalized_title=item.normalized_name,
                price=price,
                shipping=shipping,
                currency="JPY",
                total_price=total_price,
                sold_flag=True,
                active_flag=False,
                sold_date=sold_date,
                listing_url=f"https://mercari.com/item/{record_id}",
                fetched_at=now
            )
            records.append(record)
        
        logger.info(f"Generated {count} sample Mercari records")
        return records
    
    def generate_complete_dataset(self, item_count: int = 3, 
                                 ebay_records: int = 20,
                                 mercari_records: int = 15) -> Dict[str, List]:
        """
        Generate a complete sample dataset for testing the full pipeline.
        
        Args:
            item_count (int): Number of unique items (default: 3).
            ebay_records (int): Number of eBay records to generate (default: 20).
            mercari_records (int): Number of Mercari records to generate (default: 15).
        
        Returns:
            Dict[str, List]: Dictionary with keys:
                           - 'items': List of Item
                           - 'ebay_records': List of MarketRecord (eBay)
                           - 'mercari_records': List of MarketRecord (Mercari)
                           - 'all_records': Combined list of all records
        
        Example:
            >>> generator = SampleDataGenerator()
            >>> dataset = generator.generate_complete_dataset(3, 20, 15)
            >>> print(len(dataset['all_records']))  # 35 records total
        """
        items = self.generate_items(item_count)
        ebay_recs = self.generate_ebay_records(items, ebay_records)
        mercari_recs = self.generate_mercari_records(items, mercari_records)
        
        return {
            'items': items,
            'ebay_records': ebay_recs,
            'mercari_records': mercari_recs,
            'all_records': ebay_recs + mercari_recs
        }
