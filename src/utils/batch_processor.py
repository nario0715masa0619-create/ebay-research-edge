"""
Batch import utilities for Phase 5B
Handles multiple CSV files from data/imports/ directory
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.csv_importer import CSVImporter
from src.models.data_models import SourceSite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchCSVProcessor:
    """Process multiple CSV files in batch mode."""
    
    def __init__(self, import_dir: str = "data/imports"):
        """Initialize batch processor.
        
        Args:
            import_dir (str): Directory containing CSV files to import.
        """
        self.import_dir = Path(import_dir)
        self.csv_importer = CSVImporter()
        self.logger = logging.getLogger(__name__)
        
        # Create import directory if it doesn't exist
        self.import_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Batch processor initialized (import_dir: {self.import_dir})")
    
    def discover_csv_files(self) -> Dict[str, List[Path]]:
        """Discover CSV files by source type.
        
        Expected naming convention:
        - amazon_*.csv
        - yahoo_auction_*.csv
        - yahoo_shopping_*.csv
        - yahoo_fril_*.csv
        - rakuten_*.csv
        
        Returns:
            Dict[str, List[Path]]: Dictionary mapping source name to list of CSV file paths.
        """
        sources = {
            'amazon': [],
            'yahoo_auction': [],
            'yahoo_shopping': [],
            'yahoo_fril': [],
            'rakuten': [],
        }
        
        if not self.import_dir.exists():
            self.logger.warning(f"Import directory not found: {self.import_dir}")
            return sources
        
        # Discover CSV files
        for csv_file in sorted(self.import_dir.glob('*.csv')):
            filename = csv_file.name.lower()
            
            if filename.startswith('amazon_'):
                sources['amazon'].append(csv_file)
            elif filename.startswith('yahoo_auction_'):
                sources['yahoo_auction'].append(csv_file)
            elif filename.startswith('yahoo_shopping_'):
                sources['yahoo_shopping'].append(csv_file)
            elif filename.startswith('yahoo_fril_'):
                sources['yahoo_fril'].append(csv_file)
            elif filename.startswith('rakuten_'):
                sources['rakuten'].append(csv_file)
        
        # Log discovery results
        total_files = sum(len(files) for files in sources.values())
        self.logger.info(f"Discovered {total_files} CSV files:")
        for source, files in sources.items():
            if files:
                self.logger.info(f"  {source}: {len(files)} file(s)")
                for csv_file in files:
                    self.logger.info(f"    - {csv_file.name}")
        
        return sources
    
    def process_batch(self, sources_to_process: Dict[str, List[Path]] = None) -> Tuple[List, int, int]:
        """Process all discovered CSV files.
        
        Args:
            sources_to_process (Dict, optional): Dictionary of sources/files to process.
                                                 If None, discovers all.
        
        Returns:
            Tuple[List, int, int]: (all_records, total_files, success_count)
        """
        if sources_to_process is None:
            sources_to_process = self.discover_csv_files()
        
        all_records = []
        total_files = 0
        success_count = 0
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("BATCH CSV PROCESSING START")
        self.logger.info("=" * 60)
        
        for source_name, csv_files in sources_to_process.items():
            if not csv_files:
                continue
            
            self.logger.info(f"\n[{source_name.upper()}] Processing {len(csv_files)} file(s)...")
            
            for csv_file in csv_files:
                total_files += 1
                self.logger.info(f"\n  File {total_files}: {csv_file.name}")
                
                try:
                    records = self.csv_importer.import_csv(str(csv_file), source_name)
                    all_records.extend(records)
                    success_count += 1
                    self.logger.info(f"    ✓ Imported {len(records)} records from {csv_file.name}")
                except Exception as e:
                    self.logger.error(f"    ✗ Failed to import {csv_file.name}: {e}")
        
        self.logger.info("\n" + "=" * 60)
        self.logger.info("BATCH CSV PROCESSING COMPLETE")
        self.logger.info(f"Total files: {total_files} | Success: {success_count} | Records: {len(all_records)}")
        self.logger.info("=" * 60)
        
        return all_records, total_files, success_count
    
    def archive_processed_files(self, sources_to_process: Dict[str, List[Path]]) -> int:
        """Archive processed CSV files to data/imports/archive/.
        
        Args:
            sources_to_process (Dict): Dictionary of processed sources/files.
        
        Returns:
            int: Number of files archived.
        """
        archive_dir = self.import_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        archived_count = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for source_name, csv_files in sources_to_process.items():
            for csv_file in csv_files:
                try:
                    # Rename with timestamp and move to archive
                    archive_path = archive_dir / f"{csv_file.stem}_{timestamp}.csv"
                    csv_file.rename(archive_path)
                    archived_count += 1
                    self.logger.info(f"  Archived: {csv_file.name} → {archive_path.name}")
                except Exception as e:
                    self.logger.warning(f"  Failed to archive {csv_file.name}: {e}")
        
        self.logger.info(f"✓ Archived {archived_count} file(s) to {archive_dir}")
        return archived_count


if __name__ == "__main__":
    # Test batch processor
    processor = BatchCSVProcessor()
    sources = processor.discover_csv_files()
    all_records, total_files, success_count = processor.process_batch(sources)
    
    print(f"\nResults: {total_files} files, {success_count} succeeded, {len(all_records)} total records")
