"""Debug script to diagnose scoring issue"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.csv_importer import CSVImporter
from src.normalizer.normalizer import Normalizer
from src.models.data_models import SourceSite
from collections import defaultdict

# Import CSV
csv_importer = CSVImporter()
csv_records = csv_importer.import_csv("docs/csv_formats/amazon_template.csv", "amazon")
print(f"\n[DEBUG] CSV Records imported: {len(csv_records)}")
for i, rec in enumerate(csv_records):
    print(f"  {i+1}. Title: {rec.original_title} | Source: {rec.source_site} | Price: {rec.total_price}")

# Normalize
normalizer = Normalizer()
normalized = normalizer.normalize_records(csv_records)
print(f"\n[DEBUG] Normalized records: {len(normalized)}")
for i, rec in enumerate(normalized):
    print(f"  {i+1}. Normalized Title: {rec.normalized_title} | Source: {rec.source_site}")

# Group by title and source
items_dict = defaultdict(lambda: defaultdict(list))
for record in normalized:
    item_name = record.normalized_title
    source_name = record.source_site.name.lower()
    items_dict[item_name][source_name].append(record)

print(f"\n[DEBUG] Items grouped: {len(items_dict)}")
for item_name, sources_dict in items_dict.items():
    print(f"  Item: {item_name}")
    for source_name, recs in sources_dict.items():
        print(f"    - {source_name}: {len(recs)} records")
    
    ebay_recs = sources_dict.get('ebay', [])
    other_recs = []
    other_sources = []
    for source_name, recs in sources_dict.items():
        if source_name != 'ebay':
            other_recs.extend(recs)
            other_sources.append(source_name)
    
    print(f"    -> eBay: {len(ebay_recs)}, Other: {len(other_recs)}, Other sources: {other_sources}")
    
    if other_recs and not ebay_recs:
        print(f"    -> Would create DOMESTIC-ONLY candidate")
    elif ebay_recs and other_recs:
        print(f"    -> Would create MULTI-SOURCE candidate")
    else:
        print(f"    -> SKIPPED (no candidate criteria met)")
