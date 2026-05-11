def extract_keywords(title):
    """eBay タイトルから検索キーワードを抽出"""
    
    # Pokemon 関連キーワード
    keywords = []
    
    # ポケモンカードなら "ポケモンカード" を追加
    if 'pokemon' in title.lower() and 'card' in title.lower():
        keywords.append('ポケモンカード')
    elif 'pokemon' in title.lower():
        keywords.append('ポケモン')
    
    # セット名を抽出
    set_keywords = {
        'base set': 'ベースセット',
        'jungle': 'ジャングル',
        'fossil': 'フォッシル',
        '1st edition': '初版',
        'holo': 'ホロ',
        'psa': 'PSA',
        'cgc': 'CGC',
        'graded': 'グレード',
    }
    
    title_lower = title.lower()
    for en, ja in set_keywords.items():
        if en in title_lower:
            keywords.append(ja)
    
    # 数字や年号を抽出
    import re
    numbers = re.findall(r'\d{4}|\d{1,3}', title)
    keywords.extend(numbers[:2])  # 最初の2つの数字
    
    return ' '.join(keywords)

# テスト
title = "1999 Pokemon Base Set: Choose Your Card! All Cards Available"
result = extract_keywords(title)
print(f"抽出キーワード: {result}")
