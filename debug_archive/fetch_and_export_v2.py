import os
import csv
from dotenv import load_dotenv
from src.fetcher.fetcher_factory import FetcherFactory

def fetch_and_export_to_csv(
    query: str = 'pokemon card',
    limit: int = 50,
    output_file: str = 'data/ebay_items.csv',
    fetcher_type: str = None
):
    """
    eBay データを取得して CSV に出力
    
    Args:
        query: 検索キーワード
        limit: 取得件数
        output_file: 出力 CSV ファイルパス
        fetcher_type: 'browse' または 'insights' （None の場合はデフォルト）
    """
    load_dotenv()
    
    print(f'Fetching eBay data: {query}')
    print(f'Fetcher type: {fetcher_type or FetcherFactory.get_current_fetcher()}')
    
    # ファクトリーで Fetcher を作成
    try:
        fetcher = FetcherFactory.create_fetcher(fetcher_type)
    except ValueError as e:
        print(f'✗ Error: {e}')
        return
    
    # データ取得
    items = fetcher.search(
        query=query,
        limit=limit,
        itemLocationCountry='JP'  # 日本から発送
    )
    
    if not items:
        print(f'✗ No items found')
        return
    
    print(f'✓ Found {len(items)} items')
    
    # CSV に出力
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Item ID', 'Title', 'Price (USD)', 'Currency', 'URL', 'Condition', 'Ships From', 'Source']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in items:
            writer.writerow({
                'Item ID': item.get('item_id', ''),
                'Title': item.get('title', ''),
                'Price (USD)': item.get('price', ''),
                'Currency': item.get('currency', ''),
                'URL': item.get('url', ''),
                'Condition': item.get('condition', ''),
                'Ships From': item.get('ships_from', ''),
                'Source': item.get('source', '')
            })
    
    print(f'✓ Exported to {output_file}')
    print('')
    print('First 3 items:')
    for i, item in enumerate(items[:3], 1):
        price = item.get('price', 'N/A')
        currency = item.get('currency', '')
        print(f'{i}. {item["title"]} - {price} {currency}')

if __name__ == '__main__':
    # 当面は Browse API で取得
    fetch_and_export_to_csv(
        query='pokemon card',
        limit=50,
        output_file='data/ebay_items.csv',
        fetcher_type='browse'  # または None（デフォルト）
    )
    
    print('')
    print('='*60)
    print('将来、Marketplace Insights API が利用可能になったら：')
    print('  fetcher_type="insights" に変更するだけで自動切り替え')
    print('='*60)
