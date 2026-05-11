def extract_keywords(title):
    """eBay タイトルから検索キーワードを抽出（最終版v2）"""
    
    keywords = []
    
    # ポケモンカードは必須
    if 'pokemon' in title.lower() and 'card' in title.lower():
        keywords.append('ポケモンカード')
    elif 'pokemon' in title.lower():
        keywords.append('ポケモンカード')  # ポケモン単体でもカード扱い
    
    # キャラクター・セット名・グレード
    important_keywords = {
        'base set': 'ベースセット',
        'jungle': 'ジャングル',
        'fossil': 'フォッシル',
        'charizard': 'リザードン',
        'pikachu': 'ピカチュウ',
        'blastoise': 'フリーザー',
        'venusaur': 'フシギバナ',
        '1st edition': '初版',
        'psa': 'PSA',
        'cgc': 'CGC',
        'holo': 'ホロ',
        'reverse holo': 'リバースホロ',
        'full art': 'フルアート',
        'tcg': 'TCG',
        'ultra rare': 'ウルトラレア',
        'ex': 'EX',
        'vmax': 'VMAX',
        'vstar': 'VSTAR',
        'xy': 'XY',
        'scarlet': 'スカーレット',
        'violet': 'バイオレット',
        'sword': 'ソード',
        'shield': 'シールド',
    }
    
    title_lower = title.lower()
    for en, ja in important_keywords.items():
        if en in title_lower:
            keywords.append(ja)
    
    if 'lot' in title_lower or 'bulk' in title_lower or 'pack' in title_lower:
        keywords.append('まとめ売り')
    
    year_match = re.search(r'(19|20)\d{2}', title)
    if year_match:
        keywords.append(year_match.group(0))
    
    return ' '.join(keywords)

# テスト
test_titles = [
    "1999 Pokemon Base Set: Choose Your Card! All Cards Available",
    "500 Pokemon Card Lot + 50 Holo, Rares, Reverse Foils EX V",
    "PSA 10 Charizard 1999 Pokemon Base Set Holo",
    "Pokemon Card Lot 100 Official TCG Cards Ultra Rare",
    "EX Pokémon Cards! Full Art Rare Mega Break XY Black and Whit",
    "Pokemon Scarlet & Violet-151 Choose Your Card! All Ex, Holo'"
]

import re
for title in test_titles:
    result = extract_keywords(title)
    print(f"{title[:50]}...")
    print(f"  → {result}\n")
