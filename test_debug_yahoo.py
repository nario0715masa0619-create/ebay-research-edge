import asyncio
from playwright.async_api import async_playwright

async def debug_yahoo():
    base_url = 'https://auctions.yahoo.co.jp/search/search?auccat=&tab_ex=commerce&ei=utf-8&aq=-1&oq=&sc_i=&fr=auc_top&p=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89%E3%80%80%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&x=0&y=0'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # wait_until='load' に変更
            await page.goto(base_url, wait_until='load', timeout=30000)
            await page.wait_for_timeout(5000)
            
            title = await page.title()
            print(f'ページタイトル: {title}')
            
            # HTML保存
            html = await page.content()
            with open('yahoo_search_result.html', 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f'ページソース保存完了 ({len(html)}文字)')
            
        except Exception as e:
            print(f'エラー: {e}')
        finally:
            await browser.close()

asyncio.run(debug_yahoo())
