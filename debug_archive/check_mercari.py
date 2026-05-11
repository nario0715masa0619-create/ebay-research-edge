from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://jp.mercari.com/search?keyword=ポケモンカード"
driver.get(url)

print("ページを開いて手動確認してください...")
print("ブラウザに表示されている商品数を数えてください")
print("F12 で DevTools を開いて、Console でこれを実行:")
print()
print("document.querySelectorAll('li[data-testid=\"item-cell\"]').length")
print()
print("その数字を教えてください")
print()

time.sleep(60)  # 60秒待機

driver.quit()
