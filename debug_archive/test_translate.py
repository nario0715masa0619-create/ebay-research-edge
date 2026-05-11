import requests

def translate_to_japanese(text):
    """MyMemory 翻訳 API（無料）を使用"""
    try:
        url = 'https://api.mymemory.translated.net/get'
        params = {'q': text, 'langpair': 'en|ja'}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data['responseStatus'] == 200:
                translated = data['responseData']['translatedText']
                return translated
    except Exception as e:
        print(f"⚠️ 翻訳エラー: {e}")
    
    return text

# テスト
text = "1999 Pokemon Base Set: Choose Your Card! All Cards Available"
result = translate_to_japanese(text)
print(f"元: {text}")
print(f"訳: {result}")
