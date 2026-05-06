# search_price 関数のログ出力を追加したバージョン
async def search_price(page, site, keyword):
    print(f"    🔍 {site} で '{keyword}' を検索中...")
    try:
        if site == 'mercari':
            url = f'https://jp.mercari.com/search?keyword={keyword}'
            print(f"      URL: {url}")
            await page.goto(url, wait_until='load', timeout=15000)
            await page.wait_for_timeout(2000)
            print(f"      ページロード完了")
            # 以下のコードが続く...
