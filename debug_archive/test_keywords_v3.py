def extract_keywords(title):
    """eBay タイトルから検索キーワードを抽出（改善版）"""
    
    keywords = []
    
    # ポケモンカード関連
    if 'pokemon' in title.lower() and 'card' in title.lower():
        keywords.append('ポケモンカード')
    elif 'pokemon' in title.lower():
        keywords.append('ポケモン')
    
    # 重要なセット名やキャラクター
    important_keywords = {
        'base set': 'ベースセット',
        'charizard': 'リザードン',
        'pikachu': 'ピカチュウ',
        'blastoise': 'フリーザー',
        'venusaur': 'フシギバナ',
        '1st edition': '初版',
        'psa': 'PSA',
        'cgc': 'CGC',
    }
    
    title_lower = title.lower()
    for en, ja in important_keywords.items():
        if en in title_lower:
            keywords.append(ja)
    
    # Lot や bulk 商品の場合
    if 'lot' in title_lower or 'bulk' in title_lower or 'pack' in title_lower:
        keywords.append('まとめ売り')
    
    # 年号のみ抽出（4桁の数字）
    import re
    year_match = re.search(r'(19|20)\d{2}', title)
    if year_match:
        keywords.append(year_match.group(0))
    
    return ' '.join(keywords)

# テスト
test_titles = [
    "1999 Pokemon Base Set: Choose Your Card! All Cards Available",
    "500 Pokemon Card Lot + 50 Holo, Rares, Reverse Foils EX V",
    "PSA 10 Charizard 1999 Pokemon Base Set Holo",
    "Pokemon Card Lot 100 Official TCG Cards Ultra Rare"
]

for title in test_titles:
    result = extract_keywords(title)
    print(f"{title[:50]}...")
    print(f"  → {result}\n")
