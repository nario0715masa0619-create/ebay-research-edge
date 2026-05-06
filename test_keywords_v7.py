import unicodedata

def normalize_text(text):
    """Unicode を正規化（é → e など）"""
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')

def extract_keywords(title):
    """eBay タイトルから検索キーワードを抽出（最終版v3）"""
    
    keywords = []
    
    # Unicode 正規化して検索
    normalized_title = normalize_text(title).lower()
    
    # ポケモンカードは必須
    if 'pokemon' in normalized_title and 'card' in normalized_title:
        keywords.append('ポケモンカード')
    elif 'pokemon' in normalized_title:
        keywords.append('ポケモンカード')
    
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
    
    for en, ja in important_keywords.items():
        if en in normalized_title:
            keywords.append(ja)
    
    if 'lot' in normalized_title or 'bulk' in normalized_title or 'pack' in normalized_title:
        keywords.append('まとめ売り')
    
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
    "Pokemon Card Lot 100 Official TCG Cards Ultra Rare",
    "EX Pokémon Cards! Full Art Rare Mega Break XY Black and Whit",
    "Pokemon Scarlet & Violet-151 Choose Your Card! All Ex, Holo'"
]

for title in test_titles:
    result = extract_keywords(title)
    print(f"{title[:50]}...")
    print(f"  → {result}\n")
